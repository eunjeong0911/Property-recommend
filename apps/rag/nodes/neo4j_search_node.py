import os
import json
from typing import List, Optional, Dict
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from common.state import RAGState

# Neo4j Connection (Lazy Loading)
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
            username=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
    return _graph

# --- Helper for common query structure ---
def execute_hybrid_query(location_keyword: str, facility_labels: str, facility_rel: str, 
                         facility_name_key: str, sort_strategy: str = "dist"):
    """
    Executes a standard "Anchor Location + Target Facility" query.
    
    Args:
        location_keyword: User's location query (e.g. "Hongdae")
        facility_labels: Neo4j labels for target facility (e.g. "Hospital:Pharmacy")
        facility_rel: Relationship type to target (e.g. "NEAR_HOSPITAL|NEAR_PHARMACY")
        facility_name_key: Key for formatting details (e.g. "med_details")
        sort_strategy: "dist" (closest) or "count" (most connections)
    """
    
    # [Revert]: Removed Python-side sanitization (clean_keyword) per user request.
    # We now handle matching logic purely in Cypher for robustness.
    print(f"[Debug] Search: '{location_keyword}' | Facility: {facility_labels}")
    
    # 1. Find Anchor Location (Subway, University, etc.)
    # [Optimized]: Full-Text Index 사용으로 5-8초 → 0.5초 이하로 단축
    # Full-Text Index는 CONTAINS보다 훨씬 빠름 (인덱스 활용)
    # 
    # 주의: Full-Text Index가 없으면 에러 발생
    # 생성 방법: infra/neo4j/create_indexes.cypher 실행
    anchor_match = """
    CALL db.index.fulltext.queryNodes("location_search_fulltext", $keyword + "*") YIELD node AS anchor
    WHERE (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
    """
    
    # 2. Find Property connected to Anchor AND Target Facility
    # We join directly to ensure only Connected Anchors are used.
    core_query = f"""
    {anchor_match}
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    
    MATCH (p)-[r_fac:{facility_rel}]->(target)
    WHERE (
        '{facility_labels}' = 'ANY' OR
        any(label in labels(target) WHERE label IN split('{facility_labels}', ':'))
    )
    
    // Prioritize SubwayStation anchors for distance calculation if multiple exist for the same property?
    // No, usually a property is near ONE anchor relevant to the search.
    
    WITH p, anchor, r_anchor, target, r_fac
    """
    
    scoring = ""
    if sort_strategy == "count":
        # Safety strategy: Count connections
        score_logic = """
        WITH p, anchor, r_anchor, count(DISTINCT target) as fac_count, 
             collect({name: target.name, dist: coalesce(toInteger(r_fac.distance), 9999), time: coalesce(toInteger(r_fac.walking_time), 9999)})[..5] as fac_details
        WITH p, anchor, r_anchor, fac_count, fac_details, 
             (fac_count * 300) as fac_score
        """
    else:
        # Distance strategy: Closest one wins
        score_logic = """
        WITH p, anchor, r_anchor, target, r_fac ORDER BY coalesce(toInteger(r_fac.distance), 99999) ASC
        WITH p, anchor, r_anchor, count(DISTINCT target) as fac_count,
             collect({name: target.name, dist: coalesce(toInteger(r_fac.distance), 9999), time: coalesce(toInteger(r_fac.walking_time), 9999)}) as all_details
        WITH p, anchor, r_anchor, fac_count, all_details[..3] as fac_details,
             CASE WHEN size(all_details) > 0 THEN (5000 - all_details[0].dist) ELSE 0 END as fac_score
        """
        
    final_return = f"""
    {score_logic}
    
    // Total Score = Anchor Proximity + Facility Score + Anchor Priority (Subway Bonus)
    // [Fix]: Score Boost for SubwayStation to satisfy user preference for "Station" search
    WITH p, anchor, r_anchor, fac_count, fac_details, fac_score, (5000 - coalesce(toInteger(r_anchor.distance), 5000)) as anchor_score,
         CASE WHEN 'SubwayStation' IN labels(anchor) THEN 500 ELSE 0 END as priority_score
         
    WITH p, anchor, fac_count, fac_details, (anchor_score + fac_score + priority_score) as total_score,
         {{name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)}} as anchor_info
    
    RETURN p.id as id, total_score, 
           [anchor_info] as poi_details,
           fac_details as {facility_name_key}
    ORDER BY total_score DESC LIMIT 50
    """
    
    full_cypher = core_query + final_return
    return get_graph().query(full_cypher, params={"keyword": location_keyword})


# --- DOMAIN TOOLS (검색 도구) ---
# LLM Agent가 사용자 질문을 분석하여 적절한 도구를 선택합니다.

@tool  # 🚇 지하철역 근처 매물 검색
def search_properties_near_subway(location_keyword: str):
    """
    Find properties near a specific Subway Station (Transportation).
    Use this when user asks for "Subway", "Station", "Transport".
    """
    # For subway, Anchor IS the Target.
    # We modify the query slightly: Finding properties connected to the Subway node.
    query = """
    MATCH (s:SubwayStation) WHERE (s.name CONTAINS $keyword OR $keyword CONTAINS s.name)
    WITH s LIMIT 3
    MATCH (p:Property)-[r:NEAR_SUBWAY]->(s)
    
    WITH p, s, r, (5000 - coalesce(toInteger(r.distance), 5000)) as total_score
    RETURN p.id as id, total_score,
           collect({name: s.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)}) as poi_details,
           collect({name: s.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)}) as trans_details
    ORDER BY total_score DESC LIMIT 50
    """
    return get_graph().query(query, params={"keyword": location_keyword})

@tool  # 🏥 병원/종합병원 근처 매물 검색 (general_only=True: 종합병원만)
def search_properties_near_hospital(location_keyword: str, general_only: bool = False):
    """
    Find properties near Hospitals.
    Args:
        location_keyword: The location name (e.g. "Hongdae")
        general_only: If True, searches ONLY 'GeneralHospital/UniversityHospital'. If False, searches all hospitals/pharmacies.
    """
    if general_only:
        # Strict: GeneralHospital
        return execute_hybrid_query(location_keyword, "GeneralHospital", "NEAR_GENERAL_HOSPITAL", "gen_hosp_details", "dist")
    else:
        # Broad: Hospital, GeneralHospital (EXCLUDE Pharmacy)
        return execute_hybrid_query(location_keyword, "ANY", "NEAR_HOSPITAL|NEAR_GENERAL_HOSPITAL", "med_details", "dist")

@tool  # 💊 약국 근처 매물 검색
def search_properties_near_pharmacy(location_keyword: str):
    """
    Find properties near Pharmacies.
    """
    return execute_hybrid_query(location_keyword, "Pharmacy", "NEAR_PHARMACY", "pharmacy_details", "dist")

@tool  # 🏪 편의점 근처 매물 검색 (슬세권)
def search_properties_near_convenience(location_keyword: str):
    """
    Find properties near Convenience Stores.
    """
    return execute_hybrid_query(location_keyword, "Convenience", "NEAR_CONVENIENCE", "conv_details", "dist")

@tool  # 🌳 공원 근처 매물 검색
def search_properties_near_park(location_keyword: str):
    """
    Find properties near Parks or Walking areas.
    """
    return execute_hybrid_query(location_keyword, "Park", "NEAR_PARK", "park_details", "dist")

@tool  # 🎓 대학교 근처 매물 검색 (학세권)
def search_properties_near_university(location_keyword: str):
    """
    Find properties near Universities/Colleges.
    Uses a specialized query that ONLY matches College nodes as anchors.
    Returns: poi_details = nearby subway station, edu_details = searched university only
    """
    query = """
    MATCH (anchor:College) 
    WHERE (anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
    
    MATCH (p:Property)-[r_anchor:NEAR_COLLEGE]->(anchor)
    
    // 가장 가까운 지하철역 조회 (역 접근성용)
    OPTIONAL MATCH (p)-[r_sub:NEAR_SUBWAY]->(sub:SubwayStation)
    
    WITH p, anchor, r_anchor, sub, r_sub,
         (5000 - coalesce(toInteger(r_anchor.distance), 5000)) as total_score
    
    RETURN p.id as id, total_score,
           CASE WHEN sub IS NOT NULL 
                THEN [{name: sub.name, dist: coalesce(toInteger(r_sub.distance), 9999), time: coalesce(toInteger(r_sub.walking_time), 9999)}]
                ELSE [] 
           END as poi_details,
           [{name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)}] as edu_details
    ORDER BY total_score DESC LIMIT 50
    """
    print(f"[Debug] University Search: '{location_keyword}'")
    return get_graph().query(query, params={"keyword": location_keyword})


@tool  # 🛡️ 안전 시설 근처 매물 검색 (CCTV, 비상벨, 경찰서, 소방서)
def search_properties_with_safety(location_keyword: str):
    """
    Find properties with GOOD SAFETY infrastructure.
    Returns:
    - CCTV/Bell counts (e.g., "CCTV 5개")
    - Police/Fire distance and time (e.g., "경찰서 150m, 도보 2분")
    """
    query = """
    MATCH (anchor) 
    WHERE (anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
      AND (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
    
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    
    // Count-based: CCTV and Emergency Bell
    OPTIONAL MATCH (p)-[:NEAR_CCTV]->(cctv)
    OPTIONAL MATCH (p)-[:NEAR_BELL]->(bell)
    
    // Distance-based: Police and Fire Station
    OPTIONAL MATCH (p)-[r_police:NEAR_POLICE]->(police)
    OPTIONAL MATCH (p)-[r_fire:NEAR_FIRE]->(fire)
    
    WITH p, anchor, r_anchor,
         count(DISTINCT cctv) as cctv_count,
         count(DISTINCT bell) as bell_count,
         collect(DISTINCT {name: police.name, dist: coalesce(toInteger(r_police.distance), 9999), time: coalesce(toInteger(r_police.walking_time), 9999)})[..3] as police_list,
         collect(DISTINCT {name: fire.name, dist: coalesce(toInteger(r_fire.distance), 9999), time: coalesce(toInteger(r_fire.walking_time), 9999)})[..3] as fire_list
    
    // Filter out null entries from police/fire lists
    WITH p, anchor, r_anchor, cctv_count, bell_count,
         [item in police_list WHERE item.name IS NOT NULL] as police_details,
         [item in fire_list WHERE item.name IS NOT NULL] as fire_details
    
    // Score: Count-based (CCTV + Bell) + Distance-based (Police + Fire proximity) + Anchor proximity
    WITH p, anchor, r_anchor, cctv_count, bell_count, police_details, fire_details,
         (cctv_count * 100 + bell_count * 100) as count_score,
         CASE WHEN size(police_details) > 0 THEN (5000 - police_details[0].dist) ELSE 0 END as police_score,
         CASE WHEN size(fire_details) > 0 THEN (5000 - fire_details[0].dist) ELSE 0 END as fire_score,
         (5000 - coalesce(toInteger(r_anchor.distance), 5000)) as anchor_score,
         CASE WHEN 'SubwayStation' IN labels(anchor) THEN 500 ELSE 0 END as priority_score
    
    WITH p, anchor, cctv_count, bell_count, police_details, fire_details,
         (count_score + police_score + fire_score + anchor_score + priority_score) as total_score,
         {name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)} as anchor_info
    
    RETURN p.id as id, total_score,
           [anchor_info] as poi_details,
           cctv_count, bell_count, police_details, fire_details
    ORDER BY total_score DESC LIMIT 50
    """
    return get_graph().query(query, params={"keyword": location_keyword})

@tool  # 🔍 다중 조건 매물 검색 (편의점+병원+안전 등 복합 조건)
def search_properties_multi_criteria(
    location_keyword: str,
    convenience: bool = False,
    hospital: bool = False,
    pharmacy: bool = False,
    safety: bool = False,
    park: bool = False
):
    """
    Find properties that satisfy MULTIPLE facility requirements simultaneously.
    Use when user requests 2+ facility types (e.g., "convenience AND safety").
    Returns properties that have ALL requested facilities nearby.
    """
    
    # Base query: Find anchor and properties
    query = """
    MATCH (anchor) 
    WHERE (anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
      AND (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
    
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    
    // OPTIONAL MATCH for all possible facilities
    OPTIONAL MATCH (p)-[r_conv:NEAR_CONVENIENCE]->(conv:Convenience)
    OPTIONAL MATCH (p)-[r_hosp:NEAR_HOSPITAL|NEAR_GENERAL_HOSPITAL]->(hosp)
    OPTIONAL MATCH (p)-[r_pharm:NEAR_PHARMACY]->(pharm:Pharmacy)
    OPTIONAL MATCH (p)-[:NEAR_CCTV]->(cctv)
    OPTIONAL MATCH (p)-[:NEAR_BELL]->(bell)
    OPTIONAL MATCH (p)-[r_police:NEAR_POLICE]->(police)
    OPTIONAL MATCH (p)-[r_fire:NEAR_FIRE]->(fire)
    OPTIONAL MATCH (p)-[r_park:NEAR_PARK]->(park_node:Park)
    
    WITH p, anchor, r_anchor,
         count(DISTINCT conv) as conv_count,
         collect(DISTINCT {name: conv.name, dist: coalesce(toInteger(r_conv.distance), 9999), time: coalesce(toInteger(r_conv.walking_time), 9999)})[..3] as conv_list,
         count(DISTINCT hosp) as hosp_count,
         collect(DISTINCT {name: hosp.name, dist: coalesce(toInteger(r_hosp.distance), 9999), time: coalesce(toInteger(r_hosp.walking_time), 9999)})[..3] as hosp_list,
         count(DISTINCT pharm) as pharm_count,
         collect(DISTINCT {name: pharm.name, dist: coalesce(toInteger(r_pharm.distance), 9999), time: coalesce(toInteger(r_pharm.walking_time), 9999)})[..3] as pharm_list,
         count(DISTINCT cctv) as cctv_count,
         count(DISTINCT bell) as bell_count,
         collect(DISTINCT {name: police.name, dist: coalesce(toInteger(r_police.distance), 9999), time: coalesce(toInteger(r_police.walking_time), 9999)})[..3] as police_list,
         collect(DISTINCT {name: fire.name, dist: coalesce(toInteger(r_fire.distance), 9999), time: coalesce(toInteger(r_fire.walking_time), 9999)})[..3] as fire_list,
         count(DISTINCT park_node) as park_count,
         collect(DISTINCT {name: park_node.name, dist: coalesce(toInteger(r_park.distance), 9999), time: coalesce(toInteger(r_park.walking_time), 9999)})[..3] as park_list
    
    // Filter nulls
    WITH p, anchor, r_anchor,
         conv_count, [item in conv_list WHERE item.name IS NOT NULL] as conv_details,
         hosp_count, [item in hosp_list WHERE item.name IS NOT NULL] as hosp_details,
         pharm_count, [item in pharm_list WHERE item.name IS NOT NULL] as pharm_details,
         cctv_count, bell_count,
         [item in police_list WHERE item.name IS NOT NULL] as police_details,
         [item in fire_list WHERE item.name IS NOT NULL] as fire_details,
         park_count, [item in park_list WHERE item.name IS NOT NULL] as park_details
    
    // WHERE: Property must satisfy ALL requested conditions
    WHERE
        (NOT $need_conv OR conv_count > 0) AND
        (NOT $need_hosp OR hosp_count > 0) AND
        (NOT $need_pharm OR pharm_count > 0) AND
        (NOT $need_safety OR (cctv_count + bell_count) > 0) AND
        (NOT $need_park OR park_count > 0)
    
    WITH p, anchor, r_anchor,
         conv_details, hosp_details, pharm_details,
         cctv_count, bell_count, police_details, fire_details,
         park_details,
         (5000 - coalesce(toInteger(r_anchor.distance), 5000)) as anchor_score,
         CASE WHEN 'SubwayStation' IN labels(anchor) THEN 500 ELSE 0 END as priority_score
    
    WITH p, anchor, (anchor_score + priority_score) as total_score,
         {name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)} as anchor_info,
         conv_details, hosp_details, pharm_details,
         cctv_count, bell_count, police_details, fire_details, park_details
    
    RETURN p.id as id, total_score,
           [anchor_info] as poi_details,
           conv_details, hosp_details as med_details, pharm_details as pharmacy_details,
           cctv_count, bell_count, police_details, fire_details,
           park_details
    ORDER BY total_score DESC LIMIT 50
    """
    
    params = {
        "keyword": location_keyword,
        "need_conv": convenience,
        "need_hosp": hospital,
        "need_pharm": pharmacy,
        "need_safety": safety,
        "need_park": park
    }
    
    return get_graph().query(query, params=params)

# --- 규칙 기반 라우터 (Rule-Based Router) ---
# LLM Agent를 대체하여 응답 속도 2-4초 개선

import re

# 시설 타입별 키워드 매핑
FACILITY_KEYWORDS = {
    "safety": ["안전", "치안", "cctv", "경찰", "소방", "비상벨", "안심", "범죄"],
    "convenience": ["편의점", "마트", "gs25", "cu", "세븐일레븐", "이마트24"],
    "hospital": ["병원", "의원", "의료", "클리닉"],
    "general_hospital": ["종합병원", "대학병원", "대형병원"],
    "pharmacy": ["약국", "약방"],
    "park": ["공원", "산책", "녹지", "운동"],
    "university": ["대학교", "대학", "캠퍼스", "학교"],
    "subway": ["역", "지하철", "전철", "교통"]
}

# 주요 지하철역/지역명 패턴
LOCATION_PATTERNS = [
    # 지하철역 (역 접미사 포함)
    r"(홍대입구|강남|신촌|건대입구|잠실|여의도|이태원|합정|상수|망원|연남|성수|왕십리|"
    r"신림|봉천|낙성대|사당|교대|서초|삼성|선릉|역삼|논현|신사|압구정|청담|"
    r"명동|종로|동대문|혜화|대학로|을지로|시청|광화문|경복궁|안국|"
    r"노원|도봉|수유|미아|길음|돈암|성신여대|한성대|창동|쌍문|"
    r"구로|신도림|영등포|당산|선유도|문래|대림|가산|금천|"
    r"마포|공덕|애오개|아현|충정로|서울역|용산|이촌|동작|"
    r"천호|강동|암사|길동|둔촌|명일|고덕|상일동)(?:역)?",
    # 대학교
    r"(서울대|연세대|고려대|이화여대|홍익대|건국대|한양대|성균관대|중앙대|경희대|"
    r"서강대|숙명여대|동국대|국민대|세종대|한국외대|시립대|광운대|상명대|덕성여대|"
    r"숭실대|가톨릭대|서울여대|한성대|삼육대|명지대)(?:학교)?(?:교)?",
    # 일반 지역명
    r"(신촌|홍대|이태원|강남|잠실|여의도|명동|종로|동대문|성수|"
    r"마포|용산|영등포|구로|노원|송파|강동|관악|동작|서초|강서|양천|은평|"
    r"도봉|강북|중랑|성북|광진|금천|구로디지털단지)"
]

def extract_location(question: str) -> str:
    """
    질문에서 위치 정보 추출
    
    Returns:
        추출된 위치명 (없으면 빈 문자열)
    """
    for pattern in LOCATION_PATTERNS:
        match = re.search(pattern, question)
        if match:
            location = match.group(1)
            print(f"[Router] 📍 Location extracted: {location}")
            return location
    
    print("[Router] ⚠️ No location found in question")
    return ""

def detect_facilities(question: str) -> dict:
    """
    질문에서 요청된 시설 타입들 감지
    
    Returns:
        {facility_type: True/False} 딕셔너리
    """
    q = question.lower()
    detected = {}
    
    for facility, keywords in FACILITY_KEYWORDS.items():
        detected[facility] = any(kw in q for kw in keywords)
    
    return detected

def rule_based_search(state: RAGState):
    """
    규칙 기반 검색 라우터 (LLM Agent 대체)
    
    기존 Agent의 프롬프트 로직을 Python 코드로 구현하여
    LLM 호출 없이 즉시 적절한 검색 tool을 선택합니다.
    
    성능 개선: 2-4초 → ~50ms
    위치 캐싱: 동일 위치 재검색 시 Neo4j 스킵
    """
    # 위치 캐싱 import
    from common.redis_cache import get_location_cache, save_location_cache
    
    question = state["question"]
    print(f"\n{'='*60}")
    print(f"[Router] 🚀 Rule-based search for: {question}")
    print(f"{'='*60}\n")
    
    # 1. 위치 추출
    location = extract_location(question)
    
    # 2. 시설 타입 감지
    facilities = detect_facilities(question)
    active_facilities = [f for f, active in facilities.items() if active]
    print(f"[Router] 🏷️  Detected facilities: {active_facilities}")
    
    # 3. 위치가 없으면 검색 불가
    if not location:
        print("[Router] ❌ No location - cannot search")
        return {
            "graph_results": [],
            "graph_summary": "어느 지역이나 지하철역 근처를 찾으시나요? (예: 홍대입구역, 강남역)"
        }
    
    # 4. 캐시된 시설 타입 결정 (단일 시설만 캐싱)
    cache_facility_type = None
    if len(active_facilities) == 1:
        cache_facility_type = active_facilities[0]
    elif len(active_facilities) == 0:
        cache_facility_type = "subway"  # 기본값
    # 다중 시설은 조합이 다양하므로 캐싱하지 않음
    
    # 5. 위치 캐시 확인 (캐시 히트 시 Neo4j 쿼리 스킵!)
    if cache_facility_type:
        cached_results = get_location_cache(location, cache_facility_type)
        if cached_results:
            print(f"[Router] ⚡ Using cached results (Neo4j skipped!)")
            return {
                "graph_results": cached_results,
                "graph_summary": f"캐시된 검색 결과: {location} 근처 {cache_facility_type}"
            }
    
    # 6. 시설 개수에 따른 라우팅
    facility_count = sum(1 for f in ["convenience", "hospital", "pharmacy", "safety", "park"] 
                        if facilities.get(f))
    
    results = []
    
    try:
        # 4.1 다중 시설 요청 (2개 이상)
        if facility_count >= 2:
            print(f"[Router] 🔀 Multi-criteria search: {active_facilities}")
            results = search_properties_multi_criteria.invoke({
                "location_keyword": location,
                "convenience": facilities.get("convenience", False),
                "hospital": facilities.get("hospital", False) or facilities.get("general_hospital", False),
                "pharmacy": facilities.get("pharmacy", False),
                "safety": facilities.get("safety", False),
                "park": facilities.get("park", False)
            })
        
        # 4.2 안전 시설 (최우선)
        elif facilities.get("safety"):
            print(f"[Router] 🛡️ Safety search at: {location}")
            results = search_properties_with_safety.invoke({"location_keyword": location})
        
        # 4.3 편의점
        elif facilities.get("convenience"):
            print(f"[Router] 🏪 Convenience search at: {location}")
            results = search_properties_near_convenience.invoke({"location_keyword": location})
        
        # 4.4 종합병원 (general_only=True)
        elif facilities.get("general_hospital"):
            print(f"[Router] 🏥 General Hospital search at: {location}")
            results = search_properties_near_hospital.invoke({
                "location_keyword": location,
                "general_only": True
            })
        
        # 4.5 일반 병원
        elif facilities.get("hospital"):
            print(f"[Router] 🏥 Hospital search at: {location}")
            results = search_properties_near_hospital.invoke({
                "location_keyword": location,
                "general_only": False
            })
        
        # 4.6 약국
        elif facilities.get("pharmacy"):
            print(f"[Router] 💊 Pharmacy search at: {location}")
            results = search_properties_near_pharmacy.invoke({"location_keyword": location})
        
        # 4.7 공원
        elif facilities.get("park"):
            print(f"[Router] 🌳 Park search at: {location}")
            results = search_properties_near_park.invoke({"location_keyword": location})
        
        # 4.8 대학교
        elif facilities.get("university"):
            print(f"[Router] 🎓 University search at: {location}")
            results = search_properties_near_university.invoke({"location_keyword": location})
        
        # 4.9 지하철/역 또는 기본값
        else:
            print(f"[Router] 🚇 Subway/Default search at: {location}")
            results = search_properties_near_subway.invoke({"location_keyword": location})
        
        print(f"[Router] ✅ Found {len(results) if isinstance(results, list) else 0} results")
        
    except Exception as e:
        print(f"[Router] ❌ Search error: {e}")
        results = []
    
    # 결과 중복 제거
    if isinstance(results, list):
        unique_props = {p.get('id'): p for p in results if isinstance(p, dict) and p.get('id')}
        results = list(unique_props.values())
    
    # 7. 결과를 위치 캐시에 저장 (단일 시설만)
    if cache_facility_type and results:
        save_location_cache(location, cache_facility_type, results)
    
    return {
        "graph_results": results if isinstance(results, list) else [],
        "graph_summary": f"규칙 기반 검색 완료: {location} 근처 {active_facilities or ['기본']} 검색"
    }


# 기존 Agent 함수 (백업용으로 유지, 필요시 사용 가능)
def search_with_agent(state: RAGState):
    """
    [DEPRECATED] LLM Agent 기반 검색 (백업용)
    
    규칙 기반 라우터(rule_based_search)로 대체되었습니다.
    복잡한 자연어 해석이 필요한 경우에만 사용하세요.
    """
    question = state["question"]
    print(f"[Agent] Starting search for: {question}")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    tools = [
        search_properties_near_subway,
        search_properties_near_hospital,
        search_properties_near_pharmacy,
        search_properties_near_convenience,
        search_properties_near_park,
        search_properties_near_university,
        search_properties_with_safety,
        search_properties_multi_criteria
    ]
    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content="""You are a smart real estate assistant. Select the appropriate search tool based on the user's request."""),
        HumanMessage(content=question)
    ]

    max_steps = 3  # 축소된 스텝
    found_properties = []
    
    for step in range(max_steps):
        try:
            ai_msg = llm_with_tools.invoke(messages)
            messages.append(ai_msg)

            if not ai_msg.tool_calls:
                break

            for tool_call in ai_msg.tool_calls:
                t_name = tool_call['name']
                t_args = tool_call['args']
                
                tool_output = None
                if t_name == "search_properties_near_subway":
                    tool_output = search_properties_near_subway.invoke(t_args)
                elif t_name == "search_properties_near_hospital":
                    tool_output = search_properties_near_hospital.invoke(t_args)
                elif t_name == "search_properties_near_pharmacy":
                    tool_output = search_properties_near_pharmacy.invoke(t_args)
                elif t_name == "search_properties_near_convenience":
                    tool_output = search_properties_near_convenience.invoke(t_args)
                elif t_name == "search_properties_near_park":
                    tool_output = search_properties_near_park.invoke(t_args)
                elif t_name == "search_properties_near_university":
                    tool_output = search_properties_near_university.invoke(t_args)
                elif t_name == "search_properties_with_safety":
                    tool_output = search_properties_with_safety.invoke(t_args)
                elif t_name == "search_properties_multi_criteria":
                    tool_output = search_properties_multi_criteria.invoke(t_args)
                
                if isinstance(tool_output, list):
                    found_properties.extend(tool_output)
                
                messages.append(ToolMessage(content=json.dumps(tool_output, default=str), tool_call_id=tool_call["id"]))
        
        except Exception as e:
            print(f"[Agent] Error: {e}")
            break

    unique_props = {p['id']: p for p in found_properties}.values() if found_properties else []
    
    return {
        "graph_results": list(unique_props),
        "graph_summary": messages[-1].content if messages else ""
    }


# =============================================================================
# 하이브리드 라우터 (Hybrid Router)
# =============================================================================
# 간단한 쿼리 → 규칙 기반 라우터 (빠름, ~50ms)
# 복잡한 쿼리 → LLM Agent (정확함, 2-4초)

def analyze_query_complexity(question: str) -> dict:
    """
    쿼리 복잡도를 분석하여 규칙 기반 vs Agent 선택
    
    Returns:
        {
            'is_complex': bool,
            'reason': str,
            'confidence': float (0-1)
        }
    """
    q = question.lower()
    
    # 1. 위치 추출 가능 여부
    location = extract_location(question)
    if not location:
        return {
            'is_complex': True,
            'reason': '위치 미감지 - Agent가 문맥에서 추론 필요',
            'confidence': 0.9
        }
    
    # 2. 시설 타입 감지
    facilities = detect_facilities(question)
    active_facilities = [f for f, active in facilities.items() if active]
    
    # 3. 복잡한 자연어 패턴 감지
    # [Optimized]: 시설 키워드가 있으면 선호도/예산 표현은 무시 (규칙 기반으로 처리 가능)
    has_facility = len(active_facilities) > 0
    
    complex_patterns = [
        # 비교 표현 (항상 복잡)
        (r'(보다|더|가장|최고|덜|제일)', '비교 표현', True),
        # 조건부 표현 (항상 복잡)
        (r'(만약|경우|때문에|그래서|하지만|그런데)', '조건부 표현', True),
        # 선호도 표현 - 시설 키워드 있으면 무시 ("치안 좋은" → safety 검색으로 처리)
        (r'(좋은|좋을|좋게|싫은|원하는|원해|바라)', '선호도 표현', not has_facility),
        # 복합 조건 (항상 복잡)
        (r'(그리고|또는|이면서|동시에|둘 다)', '복합 조건', True),
        # 예산 표현 - 시설 키워드 있으면 무시 ("저렴한" → 가격 필터로 처리)
        (r'(예산|적당|합리적|저렴|비싸지|가성비)', '예산 복합 표현', not has_facility),
        # 대화형/질문형 (항상 복잡)
        (r'(뭐야\?|어때\?|있어\?|될까\?|할까\?)', '대화형 질문', True),
    ]
    
    for pattern, reason, should_check in complex_patterns:
        if should_check and re.search(pattern, q):
            return {
                'is_complex': True,
                'reason': reason,
                'confidence': 0.7
            }
    
    # 4. 다중 시설 + 추가 조건 (3개 이상)
    facility_count = len(active_facilities)
    if facility_count >= 3:
        return {
            'is_complex': True,
            'reason': f'다중 시설 요청 ({facility_count}개)',
            'confidence': 0.8
        }
    
    # 5. 질문 길이가 너무 길면 복잡할 가능성
    if len(question) > 100:
        return {
            'is_complex': True,
            'reason': '긴 질문 (100자 초과)',
            'confidence': 0.6
        }
    
    # 6. 시설도 없고 위치만 있는 경우 - 간단 (지하철역 기본 검색)
    if facility_count == 0:
        return {
            'is_complex': False,
            'reason': '기본 위치 검색',
            'confidence': 0.95
        }
    
    # 7. 단일/이중 시설 + 위치 = 간단
    return {
        'is_complex': False,
        'reason': f'명확한 시설 검색 ({active_facilities})',
        'confidence': 0.9
    }


def search(state: RAGState):
    """
    Neo4j 그래프 검색 - 하이브리드 라우터
    
    쿼리 복잡도에 따라 자동으로 최적의 방식 선택:
    - 간단한 쿼리 → 규칙 기반 라우터 (빠름, ~50ms)
    - 복잡한 쿼리 → LLM Agent (정확함, 2-4초)
    """
    question = state["question"]
    
    # 1. 쿼리 복잡도 분석
    complexity = analyze_query_complexity(question)
    
    print(f"\n{'='*60}")
    print(f"[Hybrid Router] 📊 Query analysis:")
    print(f"[Hybrid Router]    Question: {question[:50]}...")
    print(f"[Hybrid Router]    Complex: {complexity['is_complex']}")
    print(f"[Hybrid Router]    Reason: {complexity['reason']}")
    print(f"[Hybrid Router]    Confidence: {complexity['confidence']:.0%}")
    print(f"{'='*60}\n")
    
    # 2. 복잡도에 따른 라우팅
    if complexity['is_complex']:
        print(f"[Hybrid Router] 🤖 Using LLM Agent (complex query)")
        return search_with_agent(state)
    else:
        print(f"[Hybrid Router] ⚡ Using Rule-based Router (simple query)")
        return rule_based_search(state)
