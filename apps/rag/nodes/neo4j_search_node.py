import os
import re
from typing import List, Dict
from langchain_community.graphs import Neo4jGraph
from common.state import RAGState

# =============================================================================
# Neo4j 연결 (Lazy Loading)
# =============================================================================
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


# =============================================================================
# 규칙 기반 쿼리 빌더 (Rule-Based Query Builder)
# =============================================================================
# LLM 없이 사용자 질문을 분석하여 동적으로 Cypher 쿼리를 생성합니다.
# 성능: 17,000ms (LLM Agent) → 150ms (규칙 기반)

# -----------------------------------------------------------------------------
# 1. 상수 및 키워드 사전 (Constants & Keyword Dictionaries)
# -----------------------------------------------------------------------------

# 스코어링 상수
SCORE_MAX_DISTANCE = 5000       # 최대 거리 점수 기준 (m)
SCORE_SUBWAY_BONUS = 500        # 지하철역 우선 보너스
SCORE_SAFETY_MULTIPLIER = 100   # 안전시설 개당 점수

# 시설 타입별 키워드 매핑
FACILITY_KEYWORDS = {
    "safety": ["안전", "치안", "cctv", "경찰", "소방", "비상벨", "안심", "범죄", 
               "보안", "안전한", "치안 좋은", "안심귀가"],
    "convenience": ["편의점", "마트", "gs25", "cu", "세븐일레븐", "이마트24",
                    "편세권", "슬세권", "미니스톱", "씨유"],
    "hospital": ["병원", "의원", "의료", "클리닉", "진료소"],
    "general_hospital": ["종합병원", "대학병원", "대형병원", "상급병원"],
    "pharmacy": ["약국", "약방"],
    "park": ["공원", "산책", "녹지", "운동", "조깅", "숲"],
    "university": ["대학교", "대학", "캠퍼스", "학교", "학세권"],
    "subway": ["역", "지하철", "전철", "교통", "역세권", "메트로"]
}

# 시설 타입 → Neo4j 관계/라벨 매핑
FACILITY_CONFIG = {
    "subway": {
        "relationship": "NEAR_SUBWAY",
        "label": "SubwayStation",
        "result_key": "trans_details"
    },
    "hospital": {
        "relationship": "NEAR_HOSPITAL|NEAR_GENERAL_HOSPITAL",
        "label": "Hospital",
        "result_key": "med_details"
    },
    "general_hospital": {
        "relationship": "NEAR_GENERAL_HOSPITAL",
        "label": "GeneralHospital",
        "result_key": "gen_hosp_details"
    },
    "pharmacy": {
        "relationship": "NEAR_PHARMACY",
        "label": "Pharmacy",
        "result_key": "pharmacy_details"
    },
    "convenience": {
        "relationship": "NEAR_CONVENIENCE",
        "label": "Convenience",
        "result_key": "conv_details"
    },
    "park": {
        "relationship": "NEAR_PARK",
        "label": "Park",
        "result_key": "park_details"
    },
    "university": {
        "relationship": "NEAR_COLLEGE",
        "label": "College",
        "result_key": "edu_details"
    },
    "safety": {
        "relationship": "NEAR_CCTV|NEAR_BELL|NEAR_POLICE|NEAR_FIRE",
        "label": "Safety",
        "result_key": "safety_details"
    }
}

# 주요 지하철역/지역명 패턴 (서울 전 노선 커버)
LOCATION_PATTERNS = [
    # 지하철역 (역 접미사 포함)
    r"(홍대입구|강남|신촌|건대입구|잠실|여의도|이태원|합정|상수|망원|연남|성수|왕십리|"
    r"신림|봉천|낙성대|사당|교대|서초|삼성|선릉|역삼|논현|신사|압구정|청담|"
    r"명동|종로|종로3가|종로5가|동대문|혜화|대학로|을지로|을지로3가|을지로4가|시청|광화문|경복궁|안국|"
    r"노원|도봉|수유|미아|길음|돈암|성신여대|한성대|창동|쌍문|"
    r"구로|신도림|영등포|당산|선유도|문래|대림|가산|가산디지털단지|금천|"
    r"마포|공덕|애오개|아현|충정로|서울역|용산|이촌|동작|"
    r"천호|강동|암사|길동|둔촌|명일|고덕|상일동|"
    r"을지로입구|신당|상왕십리|신설동|동묘앞|신정네거리|양천구청|도림천|"
    r"고속터미널|남부터미널|약수|금호|옥수|압구정로데오|잠원|"
    r"동대문역사문화공원|충무로|회현|숙대입구|삼각지|한강진|"
    r"청구|신금호|행당|마장|답십리|장한평|"
    r"녹사평|효창공원앞|대흥|광흥창|"
    r"어린이대공원|군자|면목|사가정|용마산|중곡|상봉|"
    r"남구로|신풍|보라매|신대방삼거리|장승배기|"
    r"김포공항|마곡나루|가양|양천향교|염창|등촌|증미|신논현|언주|선정릉|삼성중앙|봉은사|종합운동장|"
    r"양재|양재시민의숲|청계산입구|판교|정자)(?:역)?",
    # 대학교
    r"(서울대|연세대|고려대|이화여대|홍익대|건국대|한양대|성균관대|중앙대|경희대|"
    r"서강대|숙명여대|동국대|국민대|세종대|한국외대|시립대|광운대|상명대|덕성여대|"
    r"숭실대|가톨릭대|서울여대|한성대|삼육대|명지대|"
    r"서울과기대|서울시립대|단국대|인하대|숭의여대|총신대|KC대|감리교신학대|"
    r"서울교대|한예종|서울예대|추계예대)(?:학교)?(?:교)?",
    # 일반 지역명
    r"(신촌|홍대|이태원|강남|잠실|여의도|명동|종로|동대문|성수|"
    r"마포|용산|영등포|구로|노원|송파|강동|관악|동작|서초|강서|양천|은평|"
    r"도봉|강북|중랑|성북|광진|금천|구로디지털단지|"
    r"목동|화곡|방화|개화|발산|등촌|마곡|상암|연희|연남동|"
    r"청량리|회기|중화|상봉|망우|태릉입구|공릉|하계|중계|"
    r"문정|가락|거여|마천|방이|오금|개롱|"
    r"회현|남대문|후암|청파|원효로|한남|보광동|이태원동)"
]


# -----------------------------------------------------------------------------
# 2. 질문 분석 함수 (Question Analysis Functions)
# -----------------------------------------------------------------------------

# 대학교 이름 패턴 (별도 정의 - 우선 매칭용)
UNIVERSITY_PATTERN = (
    r"(서울대|연세대|고려대|이화여대|홍익대|건국대|한양대|성균관대|중앙대|경희대|"
    r"서강대|숙명여대|동국대|국민대|세종대|한국외대|시립대|광운대|상명대|덕성여대|"
    r"숭실대|가톨릭대|서울여대|한성대|삼육대|명지대|"
    r"서울과기대|서울시립대|단국대|인하대|숭의여대|총신대|KC대|감리교신학대|"
    r"서울교대|한예종|서울예대|추계예대)(?:학교)?(?:교)?(?:근처|주변|앞)?"
)

# 대학교 의도 키워드
UNIVERSITY_INTENT_KEYWORDS = ["대학", "학교", "캠퍼스", "학세권", "대학교"]


def extract_location(question: str) -> tuple:
    """
    질문에서 위치 정보 추출 (정규식 기반)
    
    Returns:
        (location: str, location_type: str)
        location_type: 'university', 'subway', 'region', ''
    """
    # 1. 대학교 의도가 있는지 먼저 확인
    has_university_intent = any(kw in question for kw in UNIVERSITY_INTENT_KEYWORDS)
    
    # 2. 대학교 의도가 있으면 대학교 패턴 먼저 검사
    if has_university_intent:
        match = re.search(UNIVERSITY_PATTERN, question)
        if match:
            location = match.group(1)
            print(f"[QueryBuilder] 📍 Location: {location} (university, intent detected)")
            return location, "university"
    
<<<<<<< HEAD
    # 1. Find Anchor Location (Subway, University, etc.)
    # We allow the anchor to be ANY valid POI type
    # [Fix]: Do NOT limit anchors immediately. We must check for connectivity first.
    # [Fix]: Prioritize SubwayStation via Score Boost later.
    # [Fix]: Bidirectional Matching with TEXT INDEX optimization (Requirements 6.1)
    #   - Priority 1: STARTS WITH (fastest with TEXT INDEX)
    #   - Priority 2: CONTAINS (fallback for partial matches)
    #   - Case A: Keyword "Hongdae" matches Name "Hongdae Entrance" (Name STARTS WITH or CONTAINS Keyword)
    #   - Case B: Keyword "Hongdae Station" matches Name "Hongdae" (Keyword CONTAINS Name)
    anchor_match = """
    MATCH (anchor) 
    WHERE (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
      AND (anchor.name STARTS WITH $keyword OR anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
=======
    # 3. 대학교 패턴에서 정확히 매칭되는지 확인 (대학, 학교 접미사 포함된 경우)
    uni_match = re.search(UNIVERSITY_PATTERN + r"(?=\s|$|근처|주변|앞|역)", question)
    if uni_match:
        location = uni_match.group(1)
        print(f"[QueryBuilder] 📍 Location: {location} (university, exact match)")
        return location, "university"
    
    # 4. 일반 패턴 순서대로 검사
    for i, pattern in enumerate(LOCATION_PATTERNS):
        match = re.search(pattern, question)
        if match:
            location = match.group(1)
            # 패턴 인덱스로 타입 결정: 0=지하철, 1=대학교, 2=지역
            if i == 0:
                loc_type = "subway"
            elif i == 1:
                loc_type = "university"
            else:
                loc_type = "region"
            print(f"[QueryBuilder] 📍 Location: {location} ({loc_type})")
            return location, loc_type
    
    print("[QueryBuilder] ⚠️ No location found")
    return "", ""


def detect_facilities(question: str) -> Dict[str, bool]:
    """질문에서 요청된 시설 타입들 감지 (키워드 매칭)"""
    q = question.lower()
    detected = {}
    
    for facility, keywords in FACILITY_KEYWORDS.items():
        detected[facility] = any(kw in q for kw in keywords)
    
    return detected


def analyze_question(question: str) -> Dict:
>>>>>>> e5e287129bd0e48ae86e0bb7a1db2b5f865436f3
    """
    질문 분석 - 위치와 시설 타입을 추출
    
    Returns:
        {
            'location': str,           # 추출된 위치
            'location_type': str,      # 'university', 'subway', 'region', ''
            'facilities': List[str],   # 감지된 시설 타입들
            'search_type': str         # 'single', 'multi', 'default'
        }
    """
    location, location_type = extract_location(question)
    facilities_dict = detect_facilities(question)
    active_facilities = [f for f, active in facilities_dict.items() if active]
    
    # 대학교 위치인 경우 university 시설로 강제 추가 (학교 근처 검색 최적화)
    if location_type == "university" and "university" not in active_facilities:
        facilities_dict["university"] = True
        active_facilities.append("university")
        print(f"[QueryBuilder] 🎓 Added 'university' facility for location_type=university")
    
    # 검색 타입 결정
    if len(active_facilities) >= 2:
        search_type = "multi"
    elif len(active_facilities) == 1:
        search_type = "single"
    else:
        search_type = "default"  # 지하철역 기본 검색
    
    print(f"[QueryBuilder] 🏷️ Facilities: {active_facilities}, Type: {search_type}")
    
    return {
        'location': location,
        'location_type': location_type,
        'facilities': active_facilities,
        'facilities_dict': facilities_dict,
        'search_type': search_type
    }



# -----------------------------------------------------------------------------
# 3. 동적 Cypher 쿼리 빌더 (Dynamic Cypher Query Builder)
# -----------------------------------------------------------------------------

def build_single_facility_query(facility_type: str) -> str:
    """단일 시설 타입에 대한 Cypher 쿼리 생성"""
    
    config = FACILITY_CONFIG.get(facility_type)
    if not config:
        return build_subway_query()  # 기본값
    
    if facility_type == "subway":
        return build_subway_query()
    elif facility_type == "university":
        return build_university_query()
    elif facility_type == "safety":
        return build_safety_query()
    else:
        return build_facility_query(
            relationship=config["relationship"],
            label=config["label"],
            result_key=config["result_key"]
        )


def build_subway_query() -> str:
    """지하철역 검색 Cypher 쿼리 (TEXT INDEX 활용)"""
    return f"""
    MATCH (s:SubwayStation)
    WHERE s.name STARTS WITH $keyword OR s.name CONTAINS $keyword
    WITH s LIMIT 5
    
    MATCH (p:Property)-[r:NEAR_SUBWAY]->(s)
    WITH p, s, r ORDER BY r.distance LIMIT 100
    
    WITH p, s, r, ({SCORE_MAX_DISTANCE} - coalesce(toInteger(r.distance), {SCORE_MAX_DISTANCE})) as total_score
    RETURN p.id as id, total_score,
           collect({{name: s.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)}}) as poi_details
    ORDER BY total_score DESC LIMIT 50
    """


def build_university_query() -> str:
    """대학교 검색 Cypher 쿼리 (TEXT INDEX 활용)"""
    return f"""
    MATCH (anchor:College)
    WHERE anchor.name STARTS WITH $keyword OR anchor.name CONTAINS $keyword
    WITH anchor LIMIT 5
    
    MATCH (p:Property)-[r_anchor:NEAR_COLLEGE]->(anchor)
    WITH p, anchor, r_anchor ORDER BY r_anchor.distance LIMIT 100
    
    OPTIONAL MATCH (p)-[r_sub:NEAR_SUBWAY]->(sub:SubwayStation)
    WITH p, anchor, r_anchor, sub, r_sub
    ORDER BY CASE WHEN r_sub IS NULL THEN 9999 ELSE r_sub.distance END
    WITH p, anchor, r_anchor, head(collect(sub)) as closest_sub, head(collect(r_sub)) as closest_r_sub
    
    WITH p, anchor, r_anchor, closest_sub, closest_r_sub,
         ({SCORE_MAX_DISTANCE} - coalesce(toInteger(r_anchor.distance), {SCORE_MAX_DISTANCE})) as total_score
    
    RETURN p.id as id, total_score,
           CASE WHEN closest_sub IS NOT NULL 
                THEN [{{name: closest_sub.name, dist: coalesce(toInteger(closest_r_sub.distance), 9999), time: coalesce(toInteger(closest_r_sub.walking_time), 9999)}}]
                ELSE [] 
           END as poi_details,
           [{{name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)}}] as edu_details
    ORDER BY total_score DESC LIMIT 50
    """


def build_safety_query() -> str:
    """안전 시설 검색 Cypher 쿼리 (TEXT INDEX 활용)"""
    return f"""
    MATCH (anchor)
    WHERE (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
      AND (anchor.name STARTS WITH $keyword OR anchor.name CONTAINS $keyword)
    WITH anchor LIMIT 5
    
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    WITH DISTINCT p, anchor, r_anchor
    ORDER BY r_anchor.distance LIMIT 100
    
    CALL {{ WITH p RETURN count{{(p)-[:NEAR_CCTV]->()}} as cctv_count }}
    CALL {{ WITH p RETURN count{{(p)-[:NEAR_BELL]->()}} as bell_count }}
    CALL {{ 
        WITH p 
        OPTIONAL MATCH (p)-[r:NEAR_POLICE]->(police:PoliceStation)
        RETURN collect({{name: police.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}})[..1] as police_list
    }}
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_FIRE]->(fire:FireStation)
        RETURN collect({{name: fire.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}})[..1] as fire_list
    }}
    
    WITH p, anchor, r_anchor, cctv_count, bell_count,
         [item in police_list WHERE item.name IS NOT NULL] as police_details,
         [item in fire_list WHERE item.name IS NOT NULL] as fire_details
    
    WITH p, anchor, r_anchor, cctv_count, bell_count, police_details, fire_details,
         (cctv_count * {SCORE_SAFETY_MULTIPLIER} + bell_count * {SCORE_SAFETY_MULTIPLIER}) as count_score,
         CASE WHEN size(police_details) > 0 THEN ({SCORE_MAX_DISTANCE} - coalesce(police_details[0].dist, {SCORE_MAX_DISTANCE})) ELSE 0 END as police_score,
         CASE WHEN size(fire_details) > 0 THEN ({SCORE_MAX_DISTANCE} - coalesce(fire_details[0].dist, {SCORE_MAX_DISTANCE})) ELSE 0 END as fire_score,
         ({SCORE_MAX_DISTANCE} - coalesce(toInteger(r_anchor.distance), {SCORE_MAX_DISTANCE})) as anchor_score,
         CASE WHEN 'SubwayStation' IN labels(anchor) THEN {SCORE_SUBWAY_BONUS} ELSE 0 END as priority_score
    
    WITH p, anchor, cctv_count, bell_count, police_details, fire_details,
         (count_score + police_score + fire_score + anchor_score + priority_score) as total_score,
         {{name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)}} as anchor_info
    
    RETURN p.id as id, total_score,
           [anchor_info] as poi_details,
           cctv_count, bell_count, police_details, fire_details
    ORDER BY total_score DESC LIMIT 50
    """


def build_facility_query(relationship: str, label: str, result_key: str) -> str:
    """일반 시설 검색 Cypher 쿼리 (TEXT INDEX 활용)"""
    return f"""
    MATCH (anchor)
    WHERE (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
      AND (anchor.name STARTS WITH $keyword OR anchor.name CONTAINS $keyword)
    WITH anchor LIMIT 5
    
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    
    MATCH (p)-[r_fac:{relationship}]->(target:{label})
    
    WITH p, anchor, r_anchor, target, r_fac ORDER BY coalesce(toInteger(r_fac.distance), 99999) ASC
    WITH p, anchor, r_anchor, count(DISTINCT target) as fac_count,
         collect({{name: target.name, dist: coalesce(toInteger(r_fac.distance), 9999), time: coalesce(toInteger(r_fac.walking_time), 9999)}}) as all_details
    WITH p, anchor, r_anchor, fac_count, all_details[..3] as fac_details,
         CASE WHEN size(all_details) > 0 THEN ({SCORE_MAX_DISTANCE} - all_details[0].dist) ELSE 0 END as fac_score
    
    WITH p, anchor, r_anchor, fac_count, fac_details, fac_score, 
         ({SCORE_MAX_DISTANCE} - coalesce(toInteger(r_anchor.distance), {SCORE_MAX_DISTANCE})) as anchor_score,
         CASE WHEN 'SubwayStation' IN labels(anchor) THEN {SCORE_SUBWAY_BONUS} ELSE 0 END as priority_score
         
    WITH p, anchor, fac_count, fac_details, (anchor_score + fac_score + priority_score) as total_score,
         {{name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)}} as anchor_info
    
    RETURN p.id as id, total_score, 
           [anchor_info] as poi_details,
           fac_details as {result_key}
    ORDER BY total_score DESC LIMIT 50
    """


<<<<<<< HEAD
# --- DOMAIN TOOLS ---

@tool
def search_properties_near_subway(location_keyword: str):
    """
    Find properties near a specific Subway Station (Transportation).
    Use this when user asks for "Subway", "Station", "Transport".
    """
    # For subway, Anchor IS the Target.
    # We modify the query slightly: Finding properties connected to the Subway node.
    # [Optimization] TEXT INDEX optimization (Requirements 6.1): STARTS WITH priority, CONTAINS fallback
    query = """
    MATCH (s:SubwayStation) WHERE (s.name STARTS WITH $keyword OR s.name CONTAINS $keyword OR $keyword CONTAINS s.name)
    WITH s LIMIT 3
    MATCH (p:Property)-[r:NEAR_SUBWAY]->(s)
    
    WITH p, s, r, (5000 - coalesce(toInteger(r.distance), 5000)) as total_score
    RETURN p.id as id, total_score,
           collect({name: s.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)}) as poi_details,
           collect({name: s.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)}) as trans_details
    ORDER BY total_score DESC LIMIT 300
    """
    return get_graph().query(query, params={"keyword": location_keyword})

@tool
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

@tool
def search_properties_near_pharmacy(location_keyword: str):
    """
    Find properties near Pharmacies.
    """
    return execute_hybrid_query(location_keyword, "Pharmacy", "NEAR_PHARMACY", "pharmacy_details", "dist")

@tool
def search_properties_near_convenience(location_keyword: str):
    """
    Find properties near Convenience Stores.
    """
    return execute_hybrid_query(location_keyword, "Convenience", "NEAR_CONVENIENCE", "conv_details", "dist")

@tool
def search_properties_near_park(location_keyword: str):
    """
    Find properties near Parks or Walking areas.
    """
    return execute_hybrid_query(location_keyword, "Park", "NEAR_PARK", "park_details", "dist")

@tool
def search_properties_near_university(location_keyword: str):
    """
    Find properties near Universities/Colleges.
    Uses a specialized query that ONLY matches College nodes as anchors.
    Returns: poi_details = nearby subway station, edu_details = searched university only
    """
    # [Optimization] TEXT INDEX optimization (Requirements 6.1): STARTS WITH priority, CONTAINS fallback
    query = """
    MATCH (anchor:College) 
    WHERE (anchor.name STARTS WITH $keyword OR anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
    
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
    ORDER BY total_score DESC LIMIT 300
    """
    print(f"[Debug] University Search: '{location_keyword}'")
    return get_graph().query(query, params={"keyword": location_keyword})


@tool
def search_properties_with_safety(location_keyword: str):
    """
    Find properties with GOOD SAFETY infrastructure.
    Returns:
    - CCTV/Bell counts (e.g., "CCTV 5개")
    - Police/Fire distance and time (e.g., "경찰서 150m, 도보 2분")
    
    [Optimization] Requirements 2.2: CALL subqueries to prevent Cartesian product
    """
    # [Optimization] TEXT INDEX optimization (Requirements 6.1): STARTS WITH priority, CONTAINS fallback
    # [Optimization] CALL subqueries to prevent Cartesian product (Requirements 2.2)
    query = """
    MATCH (anchor) 
    WHERE (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
      AND (anchor.name STARTS WITH $keyword OR anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
=======
def build_multi_criteria_query() -> str:
    """다중 조건 검색 Cypher 쿼리 (TEXT INDEX 활용)"""
    return f"""
    MATCH (anchor)
    WHERE (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
      AND (anchor.name STARTS WITH $keyword OR anchor.name CONTAINS $keyword)
    WITH anchor LIMIT 5
>>>>>>> e5e287129bd0e48ae86e0bb7a1db2b5f865436f3
    
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    WITH DISTINCT p, anchor, r_anchor
    ORDER BY r_anchor.distance LIMIT 150
    
<<<<<<< HEAD
    WITH p, anchor, r_anchor
    
    // CCTV count - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[:NEAR_CCTV]->(c)
        RETURN count(c) as cctv_count
    }
    
    // Bell count - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[:NEAR_BELL]->(b)
        RETURN count(b) as bell_count
    }
    
    // Police details - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_POLICE]->(pol)
        WITH pol, r ORDER BY coalesce(toInteger(r.distance), 9999) ASC
        WITH collect({name: pol.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)})[..3] as police_list
        RETURN [item in police_list WHERE item.name IS NOT NULL] as police_details
    }
    
    // Fire station details - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_FIRE]->(f)
        WITH f, r ORDER BY coalesce(toInteger(r.distance), 9999) ASC
        WITH collect({name: f.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)})[..3] as fire_list
        RETURN [item in fire_list WHERE item.name IS NOT NULL] as fire_details
    }
=======
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_CONVENIENCE]->(n:Convenience)
        WITH n, r ORDER BY r.distance LIMIT 3
        RETURN count(n) as conv_count,
               collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as conv_list
    }}
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_HOSPITAL|NEAR_GENERAL_HOSPITAL]->(n)
        WITH n, r ORDER BY r.distance LIMIT 3
        RETURN count(n) as hosp_count,
               collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as hosp_list
    }}
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_PHARMACY]->(n:Pharmacy)
        WITH n, r ORDER BY r.distance LIMIT 3
        RETURN count(n) as pharm_count,
               collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as pharm_list
    }}
    
    CALL {{
        WITH p
        RETURN count{{(p)-[:NEAR_CCTV]->()}} as cctv_count,
               count{{(p)-[:NEAR_BELL]->()}} as bell_count
    }}
>>>>>>> e5e287129bd0e48ae86e0bb7a1db2b5f865436f3
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_POLICE]->(n:PoliceStation)
        WITH n, r ORDER BY r.distance LIMIT 1
        RETURN collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as police_list
    }}
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_FIRE]->(n:FireStation)
        WITH n, r ORDER BY r.distance LIMIT 1
        RETURN collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as fire_list
    }}
    
<<<<<<< HEAD
    RETURN p.id as id, total_score,
           [anchor_info] as poi_details,
           cctv_count, bell_count, police_details, fire_details
    ORDER BY total_score DESC LIMIT 300
    """
    return get_graph().query(query, params={"keyword": location_keyword})

@tool
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
    
    [Optimization] Requirements 2.2: CALL subqueries to prevent Cartesian product
    """
    
    # [Optimization] TEXT INDEX optimization (Requirements 6.1): STARTS WITH priority, CONTAINS fallback
    # [Optimization] CALL subqueries to prevent Cartesian product (Requirements 2.2)
    query = """
    MATCH (anchor) 
    WHERE (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
      AND (anchor.name STARTS WITH $keyword OR anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
    
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    
    WITH p, anchor, r_anchor
    
    // Convenience - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_CONVENIENCE]->(conv:Convenience)
        WITH conv, r ORDER BY coalesce(toInteger(r.distance), 9999) ASC
        WITH count(conv) as cnt, collect({name: conv.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)})[..3] as details
        RETURN cnt as conv_count, [item in details WHERE item.name IS NOT NULL] as conv_details
    }
    
    // Hospital - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_HOSPITAL|NEAR_GENERAL_HOSPITAL]->(hosp)
        WITH hosp, r ORDER BY coalesce(toInteger(r.distance), 9999) ASC
        WITH count(hosp) as cnt, collect({name: hosp.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)})[..3] as details
        RETURN cnt as hosp_count, [item in details WHERE item.name IS NOT NULL] as hosp_details
    }
    
    // Pharmacy - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_PHARMACY]->(pharm:Pharmacy)
        WITH pharm, r ORDER BY coalesce(toInteger(r.distance), 9999) ASC
        WITH count(pharm) as cnt, collect({name: pharm.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)})[..3] as details
        RETURN cnt as pharm_count, [item in details WHERE item.name IS NOT NULL] as pharm_details
    }
    
    // CCTV count - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[:NEAR_CCTV]->(c)
        RETURN count(c) as cctv_count
    }
    
    // Bell count - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[:NEAR_BELL]->(b)
        RETURN count(b) as bell_count
    }
    
    // Police details - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_POLICE]->(pol)
        WITH pol, r ORDER BY coalesce(toInteger(r.distance), 9999) ASC
        WITH collect({name: pol.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)})[..3] as details
        RETURN [item in details WHERE item.name IS NOT NULL] as police_details
    }
    
    // Fire station details - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_FIRE]->(f)
        WITH f, r ORDER BY coalesce(toInteger(r.distance), 9999) ASC
        WITH collect({name: f.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)})[..3] as details
        RETURN [item in details WHERE item.name IS NOT NULL] as fire_details
    }
    
    // Park - separate subquery to prevent Cartesian product
    CALL {
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_PARK]->(park_node:Park)
        WITH park_node, r ORDER BY coalesce(toInteger(r.distance), 9999) ASC
        WITH count(park_node) as cnt, collect({name: park_node.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)})[..3] as details
        RETURN cnt as park_count, [item in details WHERE item.name IS NOT NULL] as park_details
    }
    
    // WHERE: Property must satisfy ALL requested conditions
    WITH p, anchor, r_anchor,
         conv_count, conv_details,
         hosp_count, hosp_details,
         pharm_count, pharm_details,
         cctv_count, bell_count, police_details, fire_details,
         park_count, park_details
=======
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_PARK]->(n:Park)
        WITH n, r ORDER BY r.distance LIMIT 3
        RETURN count(n) as park_count,
               collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as park_list
    }}
    
    WITH p, anchor, r_anchor,
         conv_count, [item in conv_list WHERE item.name IS NOT NULL] as conv_details,
         hosp_count, [item in hosp_list WHERE item.name IS NOT NULL] as hosp_details,
         pharm_count, [item in pharm_list WHERE item.name IS NOT NULL] as pharm_details,
         cctv_count, bell_count,
         [item in police_list WHERE item.name IS NOT NULL] as police_details,
         [item in fire_list WHERE item.name IS NOT NULL] as fire_details,
         park_count, [item in park_list WHERE item.name IS NOT NULL] as park_details
    
>>>>>>> e5e287129bd0e48ae86e0bb7a1db2b5f865436f3
    WHERE
        (NOT $need_conv OR conv_count > 0) AND
        (NOT $need_hosp OR hosp_count > 0) AND
        (NOT $need_pharm OR pharm_count > 0) AND
        (NOT $need_safety OR (cctv_count + bell_count) > 0 OR size(police_list) > 0 OR size(fire_list) > 0) AND
        (NOT $need_park OR park_count > 0)
    
    WITH p, anchor, r_anchor,
         conv_details, hosp_details, pharm_details,
         cctv_count, bell_count, police_details, fire_details, park_details,
         ({SCORE_MAX_DISTANCE} - coalesce(toInteger(r_anchor.distance), {SCORE_MAX_DISTANCE})) as anchor_score,
         CASE WHEN 'SubwayStation' IN labels(anchor) THEN {SCORE_SUBWAY_BONUS} ELSE 0 END as priority_score
    
    WITH p, (anchor_score + priority_score) as total_score,
         {{name: anchor.name, dist: toInteger(r_anchor.distance), time: toInteger(r_anchor.walking_time)}} as anchor_info,
         conv_details, hosp_details, pharm_details,
         cctv_count, bell_count, police_details, fire_details, park_details
    
    RETURN p.id as id, total_score,
           [anchor_info] as poi_details,
           conv_details, hosp_details as med_details, pharm_details as pharmacy_details,
           cctv_count, bell_count, police_details, fire_details, park_details
    ORDER BY total_score DESC LIMIT 50
    """


def build_university_multi_query() -> str:
    """대학교 전용 다중 조건 검색 Cypher 쿼리 (College만 앵커로 사용)"""
    return f"""
    MATCH (anchor:College)
    WHERE anchor.name STARTS WITH $keyword OR anchor.name CONTAINS $keyword
    WITH anchor LIMIT 5
    
    MATCH (p:Property)-[r_anchor:NEAR_COLLEGE]->(anchor)
    WITH DISTINCT p, anchor, r_anchor
    ORDER BY r_anchor.distance LIMIT 150
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_CONVENIENCE]->(n:Convenience)
        WITH n, r ORDER BY r.distance LIMIT 3
        RETURN count(n) as conv_count,
               collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as conv_list
    }}
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_HOSPITAL|NEAR_GENERAL_HOSPITAL]->(n)
        WITH n, r ORDER BY r.distance LIMIT 3
        RETURN count(n) as hosp_count,
               collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as hosp_list
    }}
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_PHARMACY]->(n:Pharmacy)
        WITH n, r ORDER BY r.distance LIMIT 3
        RETURN count(n) as pharm_count,
               collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as pharm_list
    }}
    
    CALL {{
        WITH p
        RETURN count{{(p)-[:NEAR_CCTV]->()}} as cctv_count,
               count{{(p)-[:NEAR_BELL]->()}} as bell_count
    }}
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_POLICE]->(n:PoliceStation)
        WITH n, r ORDER BY r.distance LIMIT 1
        RETURN collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as police_list
    }}
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_FIRE]->(n:FireStation)
        WITH n, r ORDER BY r.distance LIMIT 1
        RETURN collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as fire_list
    }}
    
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_PARK]->(n:Park)
        WITH n, r ORDER BY r.distance LIMIT 3
        RETURN count(n) as park_count,
               collect({{name: n.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as park_list
    }}
    
    // 추가: 가장 가까운 지하철역 정보
    CALL {{
        WITH p
        OPTIONAL MATCH (p)-[r:NEAR_SUBWAY]->(s:SubwayStation)
        WITH s, r ORDER BY r.distance LIMIT 1
        RETURN collect({{name: s.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}}) as subway_list
    }}
    
    WITH p, anchor, r_anchor,
         conv_count, [item in conv_list WHERE item.name IS NOT NULL] as conv_details,
         hosp_count, [item in hosp_list WHERE item.name IS NOT NULL] as hosp_details,
         pharm_count, [item in pharm_list WHERE item.name IS NOT NULL] as pharm_details,
         cctv_count, bell_count,
         [item in police_list WHERE item.name IS NOT NULL] as police_details,
         [item in fire_list WHERE item.name IS NOT NULL] as fire_details,
         park_count, [item in park_list WHERE item.name IS NOT NULL] as park_details,
         [item in subway_list WHERE item.name IS NOT NULL] as trans_details
    
    WHERE
        (NOT $need_conv OR conv_count > 0) AND
        (NOT $need_hosp OR hosp_count > 0) AND
        (NOT $need_pharm OR pharm_count > 0) AND
        (NOT $need_safety OR (cctv_count + bell_count) > 0 OR size(police_list) > 0 OR size(fire_list) > 0) AND
        (NOT $need_park OR park_count > 0)
    
    WITH p, anchor, r_anchor,
         conv_details, hosp_details, pharm_details,
         cctv_count, bell_count, police_details, fire_details, park_details, trans_details,
         ({SCORE_MAX_DISTANCE} - coalesce(toInteger(r_anchor.distance), {SCORE_MAX_DISTANCE})) as anchor_score
    
    WITH p, anchor_score as total_score,
         {{name: anchor.name, dist: toInteger(r_anchor.distance), time: toInteger(r_anchor.walking_time)}} as edu_info,
         conv_details, hosp_details, pharm_details,
         cctv_count, bell_count, police_details, fire_details, park_details, trans_details
    
    RETURN p.id as id, total_score,
           [edu_info] as edu_details,
           trans_details as poi_details,
           conv_details, hosp_details as med_details, pharm_details as pharmacy_details,
           cctv_count, bell_count, police_details, fire_details, park_details
    ORDER BY total_score DESC LIMIT 50
    """


# -----------------------------------------------------------------------------
# 4. 쿼리 실행 함수 (Query Execution)
# -----------------------------------------------------------------------------

def execute_query(location: str, analysis: Dict) -> List[Dict]:
    """
    분석 결과를 기반으로 적절한 Cypher 쿼리 실행
    
    Args:
        location: 추출된 위치
        analysis: analyze_question() 결과
    
    Returns:
        Neo4j 쿼리 결과 리스트
    """
    search_type = analysis['search_type']
    facilities = analysis['facilities']
    facilities_dict = analysis['facilities_dict']
    location_type = analysis.get('location_type', '')
    
    try:
        # 다중 시설 검색
        if search_type == "multi":
            print(f"[QueryBuilder] 🔀 Multi-criteria search: {facilities}")
            
            # 대학교 위치인 경우 대학교 전용 멀티 쿼리 사용
            if location_type == "university":
                print(f"[QueryBuilder] 🎓 Using university-anchor multi-criteria query")
                query = build_university_multi_query()
                params = {
                    "keyword": location,
                    "need_conv": facilities_dict.get("convenience", False),
                    "need_hosp": facilities_dict.get("hospital", False) or facilities_dict.get("general_hospital", False),
                    "need_pharm": facilities_dict.get("pharmacy", False),
                    "need_safety": facilities_dict.get("safety", False),
                    "need_park": facilities_dict.get("park", False)
                }
            else:
                query = build_multi_criteria_query()
                params = {
                    "keyword": location,
                    "need_conv": facilities_dict.get("convenience", False),
                    "need_hosp": facilities_dict.get("hospital", False) or facilities_dict.get("general_hospital", False),
                    "need_pharm": facilities_dict.get("pharmacy", False),
                    "need_safety": facilities_dict.get("safety", False),
                    "need_park": facilities_dict.get("park", False)
                }
            return get_graph().query(query, params=params)
        
        # 단일 시설 검색
        elif search_type == "single":
            facility_type = facilities[0]
            
            # 대학교 위치인 경우 university 쿼리 강제 사용
            if location_type == "university":
                print(f"[QueryBuilder] 🎓 University location detected - using university query")
                query = build_university_query()
                return get_graph().query(query, params={"keyword": location})
            
            # 시설 타입별 우선순위 조정
            if facilities_dict.get("general_hospital"):
                facility_type = "general_hospital"
            
            print(f"[QueryBuilder] 🔍 Single facility search: {facility_type}")
            query = build_single_facility_query(facility_type)
            return get_graph().query(query, params={"keyword": location})
        
        # 기본 검색 - location_type에 따라 분기
        else:
            if location_type == "university":
                print(f"[QueryBuilder] 🎓 Default university search")
                query = build_university_query()
            else:
                print(f"[QueryBuilder] 🚇 Default subway search")
                query = build_subway_query()
            return get_graph().query(query, params={"keyword": location})
    
    except Exception as e:
        print(f"[QueryBuilder] ❌ Query execution error: {e}")
        return []



# -----------------------------------------------------------------------------
# 5. 메인 검색 함수 (Main Search Function)
# -----------------------------------------------------------------------------

def generate_search_steps(location: str, facilities: List[str]) -> List[str]:
    """검색 의도에 따른 사용자 친화적 진행 메시지 생성"""
    steps = []
    
    # 1. 위치 검색 메시지
    if location:
        steps.append(f"{location} 근처 매물 찾는 중...")
    
    # 2. 시설별 검색 메시지
    facility_msg_map = {
        "safety": "안전한 방(CCTV/치안) 찾는 중...",
        "convenience": "가까운 편의점 찾는 중...",
        "hospital": "가까운 병원 확인하는 중...",
        "general_hospital": "종합병원 접근성 확인 중...",
        "pharmacy": "근처 약국 찾는 중...",
        "park": "산책하기 좋은 공원 찾는 중...",
        "university": "대학교 통학 거리 계산 중...",
        "subway": "역세권 매물 스캔 중..."
    }
    
    for fac in facilities:
        if fac in facility_msg_map:
            steps.append(facility_msg_map[fac])
        elif fac == "subway" and not location: # location이 없는데 subway만 있으면
            steps.append("역세권 매물 스캔 중...")
            
    return steps


def rule_based_search(state: RAGState) -> Dict:
    """
    규칙 기반 검색 (LLM 0회 호출)
    
    1. 질문 분석 (위치 + 시설 타입 추출)
    2. 동적 Cypher 쿼리 생성
    3. Neo4j 쿼리 실행
    4. 결과 정제 및 반환
    """
    import time
    start_time = time.time()
    
    # 위치 캐싱 import
    from common.redis_cache import get_location_cache, save_location_cache
    
    question = state["question"]
    print(f"\n{'='*60}")
    print(f"[Neo4j] 🚀 검색 시작: {question}")
    print(f"{'='*60}\n")
    
    # 1. 질문 분석
    analysis = analyze_question(question)
    location = analysis['location']
    facilities = analysis['facilities']
    
    # 검색 진행 상황 메시지 생성 (UI 표시용)
    search_steps = generate_search_steps(location, facilities)
    print(f"[Neo4j] 📋 Progress Steps: {search_steps}")
    
    # 2. 위치가 없으면 검색 불가
    if not location:
        return {
            "graph_results": [],
            "graph_summary": "어느 지역이나 지하철역 근처를 찾으시나요? (예: 홍대입구역, 강남역)",
            "search_steps": search_steps or ["검색 조건을 확인 중입니다..."]
        }
    
    # 3. 캐시 확인 (단일 시설만, location_type 반영)
    location_type = analysis.get('location_type', '')
    cache_key = facilities[0] if len(facilities) == 1 else ("subway" if not facilities and location_type != "university" else None)
    
    # 대학교 검색인 경우 캐시 키에 university 접두사 추가
    full_cache_key = f"{location_type}:{cache_key}" if location_type and cache_key else cache_key
    
    if full_cache_key:
        cached_results = get_location_cache(location, full_cache_key)
        if cached_results:
            elapsed = int((time.time() - start_time) * 1000)
            print(f"[Neo4j] ⚡ 캐시 히트! | 시간: {elapsed}ms")
            
            # 캐시된 경우에도 steps는 반환
            return {
                "graph_results": cached_results,
                "graph_summary": f"캐시된 검색 결과: {location} 근처 {cache_key}",
                "search_steps": search_steps,
                "requested_facilities": facilities
            }
    
    # 4. 쿼리 실행
    results = execute_query(location, analysis)
    
    # 5. 결과 중복 제거
    if isinstance(results, list):
        unique_props = {p.get('id'): p for p in results if isinstance(p, dict) and p.get('id')}
        results = list(unique_props.values())
    
    elapsed = int((time.time() - start_time) * 1000)
    print(f"[Neo4j] ✅ 완료: {len(results)}개 결과 | 시간: {elapsed}ms")
    
    # 6. 캐시 저장 (단일 시설만, location_type 반영)
    if full_cache_key and results:
        save_location_cache(location, full_cache_key, results)
    
    return {
        "graph_results": results if isinstance(results, list) else [],
        "graph_summary": f"규칙 기반 검색 완료: {location} 근처 {facilities or ['기본']} 검색",
        "search_steps": search_steps,
        "requested_facilities": facilities
    }




# =============================================================================
# 진입점 (Entry Point)
# =============================================================================

def search(state: RAGState) -> Dict:
    """
    Neo4j 그래프 검색 - 순수 규칙 기반 (LLM 0회 호출)
    
    동작: 질문에서 위치/시설 추출 → Cypher 쿼리 생성 → Neo4j 실행
    성능: 17,000ms (LLM) → 150ms (규칙 기반)
    """
    return rule_based_search(state)
