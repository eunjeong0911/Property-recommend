"""
Cache Filter Node - AND 조건 필터링

핵심 로직:
- Q1: 전체 검색 → 20개 매물
- Q2: Q1 결과 중 조건 만족하는 것만 → N개로 줄어듦
- Q3: Q2 결과 중 조건 만족하는 것만 → M개로 줄어듦
- 각 단계에서 조건 불만족 매물은 탈락 (AND 조건)
"""
from common.state import RAGState
from langchain_community.graphs import Neo4jGraph
import psycopg2
import os
import re

# 시설 타입별 키워드
FACILITY_KEYWORDS = {
    "safety": ["안전", "치안", "cctv", "경찰", "비상벨", "범죄"],
    "convenience": ["편의점", "마트", "gs25", "cu", "세븐일레븐"],
    "hospital": ["병원", "의원", "의료", "종합병원"],
    "pharmacy": ["약국"],
    "park": ["공원", "산책", "녹지"],
    "university": ["대학", "학교", "캠퍼스"],
    "subway": ["역", "지하철", "전철"]
}

POSTGRES_KEYWORDS = {
    "price": ["가격", "월세", "보증금", "만원"],
    "room": ["방", "개", "룸"],
    "area": ["평", "m2", "면적"]
}


def cache_filter(state: RAGState) -> RAGState:
    """
    캐시된 매물 ID 중 조건 만족하는 것만 필터링 (AND 조건)
    
    예시:
    - Q1: 20개 매물 (편의점 가까운)
    - Q2: 그 중 CCTV 있는 것만 → 12개
    - Q3: 그 중 병원 가까운 것만 → 8개
    """
    cached_ids = state.get("cached_property_ids", [])
    question = state["question"]
    accumulated = state.get("accumulated_results", {})
    
    print(f"\n[CacheFilter] {'='*50}")
    print(f"[CacheFilter] Input: {len(cached_ids)} properties")
    print(f"[CacheFilter] Question: {question}")
    
    if not cached_ids:
        print("[CacheFilter] ✗ No cached IDs")
        state["use_cache"] = False
        state["graph_results"] = []
        state["sql_results"] = []
        return state
    
    # 시설 타입 감지
    facility_type = _detect_facility_type(question)
    postgres_filter = _detect_postgres_filter(question)
    
    print(f"[CacheFilter] Filter: facility={facility_type}, postgres={postgres_filter}")
    
    # Neo4j 기반 필터링 (AND 조건)
    if facility_type:
        # 조건 만족하는 매물만 반환 (필터링!)
        filtered_results = _filter_by_facility(cached_ids, facility_type)
        
        if filtered_results:
            # 필터된 ID만 추출
            filtered_ids = [str(r.get("id") or r.get("p.id")) for r in filtered_results if isinstance(r, dict)]
            
            # 누적 데이터와 병합
            merged_results = _merge_all_data(filtered_results, accumulated)
            
            state["graph_results"] = merged_results
            state["cached_property_ids"] = filtered_ids  # 필터된 ID로 업데이트!
            state["filter_source"] = f"neo4j:{facility_type}"
            state["use_cache"] = True
            state["sql_results"] = _fetch_sql_details(filtered_ids)
            
            print(f"[CacheFilter] ✓ Filtered: {len(cached_ids)} → {len(filtered_ids)} (AND: {facility_type})")
            return state
        else:
            print(f"[CacheFilter] ✗ No properties match {facility_type}")
            state["graph_results"] = []
            state["sql_results"] = []
            state["use_cache"] = True
            return state
    
    # PostgreSQL 필터링
    if postgres_filter:
        filtered = _filter_by_postgres(cached_ids, question, postgres_filter)
        if filtered:
            filtered_ids = [str(r.get("land_num")) for r in filtered if r.get("land_num")]
            merged_results = _merge_all_data(filtered, accumulated)
            
            state["graph_results"] = merged_results
            state["sql_results"] = filtered
            state["cached_property_ids"] = filtered_ids
            state["filter_source"] = f"postgres:{postgres_filter}"
            state["use_cache"] = True
            print(f"[CacheFilter] ✓ Filtered by {postgres_filter}: {len(filtered_ids)}")
            return state
    
    # 기본: 상세정보만 조회
    print("[CacheFilter] No filter, returning cached properties")
    state["sql_results"] = _fetch_sql_details(cached_ids)
    state["graph_results"] = [accumulated.get(id, {"id": id}) for id in cached_ids]
    state["use_cache"] = True
    return state


def _filter_by_facility(property_ids: list, facility_type: str) -> list:
    """
    시설 조건 만족하는 매물만 필터링 (AND 조건)
    
    - 조건 불만족 매물은 결과에서 제외됨
    - 조건 만족 매물만 반환
    """
    graph = _get_neo4j_graph()
    
    # 각 시설별 필터 쿼리 (조건 불만족하면 결과에서 제외)
    queries = {
        "safety": """
            MATCH (p:Property) WHERE p.id IN $ids
            OPTIONAL MATCH (p)-[:NEAR_CCTV]->(c)
            WITH p, count(c) as cctv_count
            WHERE cctv_count > 0
            OPTIONAL MATCH (p)-[:NEAR_BELL]->(b)
            WITH p, cctv_count, count(b) as bell_count
            OPTIONAL MATCH (p)-[r:NEAR_POLICE]->(pol:PoliceStation)
            WITH p, cctv_count, bell_count, 
                 head(collect({name:pol.name, dist:toInteger(r.distance), time:toInteger(r.walking_time)})) as police_details
            OPTIONAL MATCH (p)-[r:NEAR_FIRE]->(fire:FireStation)
            WITH p, cctv_count, bell_count, police_details,
                 head(collect({name:fire.name, dist:toInteger(r.distance), time:toInteger(r.walking_time)})) as fire_details
            RETURN p.id as id, p.address as address,
                   cctv_count, bell_count, police_details, fire_details,
                   (cctv_count*50 + bell_count*30) as total_score
            ORDER BY total_score DESC
        """,
        
        "convenience": """
            MATCH (p:Property) WHERE p.id IN $ids
            OPTIONAL MATCH (p)-[r:NEAR_CONVENIENCE]->(c:Convenience)
            WITH p, count(c) as conv_count,
                 collect({name:c.name, dist:toInteger(r.distance), time:toInteger(r.walking_time)})[..3] as conv_details
            WHERE conv_count > 0
            RETURN p.id as id, p.address as address,
                   conv_count, conv_details,
                   conv_count * 100 as total_score
            ORDER BY total_score DESC
        """,
        
        "hospital": """
            MATCH (p:Property) WHERE p.id IN $ids
            OPTIONAL MATCH (p)-[r:NEAR_HOSPITAL|NEAR_GENERAL_HOSPITAL]->(h)
            WITH p, count(h) as hosp_count,
                 collect({name:h.name, dist:toInteger(r.distance), time:toInteger(r.walking_time)})[..3] as med_details
            WHERE hosp_count > 0
            RETURN p.id as id, p.address as address,
                   hosp_count, med_details,
                   hosp_count * 100 as total_score
            ORDER BY total_score DESC
        """,
        
        "pharmacy": """
            MATCH (p:Property) WHERE p.id IN $ids
            OPTIONAL MATCH (p)-[r:NEAR_PHARMACY]->(ph:Pharmacy)
            WITH p, count(ph) as pharm_count,
                 collect({name:ph.name, dist:toInteger(r.distance), time:toInteger(r.walking_time)})[..3] as pharm_details
            WHERE pharm_count > 0
            RETURN p.id as id, p.address as address,
                   pharm_count, pharm_details,
                   pharm_count * 100 as total_score
            ORDER BY total_score DESC
        """,
        
        "park": """
            MATCH (p:Property) WHERE p.id IN $ids
            OPTIONAL MATCH (p)-[r:NEAR_PARK]->(pk:Park)
            WITH p, count(pk) as park_count,
                 collect({name:pk.name, dist:toInteger(r.distance), time:toInteger(r.walking_time)})[..3] as park_details
            WHERE park_count > 0
            RETURN p.id as id, p.address as address,
                   park_count, park_details,
                   park_count * 100 as total_score
            ORDER BY total_score DESC
        """,
        
        "university": """
            MATCH (p:Property) WHERE p.id IN $ids
            OPTIONAL MATCH (p)-[r:NEAR_COLLEGE]->(u:College)
            WITH p, count(u) as uni_count,
                 collect({name:u.name, dist:toInteger(r.distance), time:toInteger(r.walking_time)})[..3] as edu_details
            WHERE uni_count > 0
            RETURN p.id as id, p.address as address,
                   uni_count, edu_details,
                   uni_count * 100 as total_score
            ORDER BY total_score DESC
        """,
        
        "subway": """
            MATCH (p:Property) WHERE p.id IN $ids
            MATCH (p)-[r:NEAR_SUBWAY]->(s:SubwayStation)
            WITH p, 
                 head(collect({name:s.name, dist:toInteger(r.distance), time:toInteger(r.walking_time)})) as station
            WHERE station IS NOT NULL
            RETURN p.id as id, p.address as address,
                   [station] as poi_details,
                   1000 - coalesce(station.dist, 9999) as total_score
            ORDER BY total_score DESC
        """
    }
    
    query = queries.get(facility_type)
    if not query:
        print(f"[CacheFilter] Unknown facility: {facility_type}")
        return []
    
    try:
        results = graph.query(query, {"ids": property_ids})
        print(f"[CacheFilter] Neo4j filter: {len(property_ids)} → {len(results)}")
        return results
    except Exception as e:
        print(f"[CacheFilter] Neo4j error: {e}")
        return []


def _merge_all_data(new_results: list, accumulated: dict) -> list:
    """새 쿼리 결과에 누적된 모든 데이터 병합"""
    if not accumulated:
        print("[CacheFilter] _merge: No accumulated data")
        return new_results
    
    # 디버그: 누적된 데이터의 샘플 필드 확인
    sample_id = next(iter(accumulated.keys()), None)
    if sample_id:
        sample_fields = [k for k in accumulated[sample_id].keys() if accumulated[sample_id].get(k)]
        print(f"[CacheFilter] _merge: Accumulated has fields: {sample_fields}")
    
    merged_list = []
    for result in new_results:
        if not isinstance(result, dict):
            merged_list.append(result)
            continue
        
        prop_id = str(result.get("id") or result.get("p.id") or result.get("land_num") or "")
        
        if prop_id in accumulated:
            # 1. 기존 누적 데이터로 시작
            merged = accumulated[prop_id].copy()
            # 2. 새 결과의 유효한 값만 추가/덮어쓰기
            for key, value in result.items():
                if value and value != [] and value != 0:
                    merged[key] = value
            merged_list.append(merged)
        else:
            merged_list.append(result)
    
    # 디버그: 병합 결과 확인
    if merged_list:
        sample = merged_list[0]
        sample_fields = [k for k in sample.keys() if sample.get(k)]
        print(f"[CacheFilter] _merge: Result has fields: {sample_fields}")
    
    return merged_list


def _detect_facility_type(question: str) -> str | None:
    q = question.lower()
    for facility, keywords in FACILITY_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return facility
    return None


def _detect_postgres_filter(question: str) -> str | None:
    q = question.lower()
    for filter_type, keywords in POSTGRES_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return filter_type
    return None


def _get_neo4j_graph():
    return Neo4jGraph(
        url=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password")
    )


def _fetch_sql_details(property_ids: list) -> list:
    if not property_ids:
        print("[CacheFilter] SQL: No property IDs to fetch")
        return []
    
    print(f"[CacheFilter] SQL: Fetching details for {len(property_ids)} IDs: {property_ids[:3]}...")
    
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        cursor = conn.cursor()
        placeholders = ','.join(['%s'] * len(property_ids))
        cursor.execute(f"""
            SELECT land_num, building_type, address, deal_type, url, images,
                   trade_info, listing_info, additional_options, description,
                   agent_info, like_count, view_count, 'm' as distance_unit
            FROM land WHERE land_num = ANY(%s::text[])
        """, (property_ids,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        print(f"[CacheFilter] SQL: Found {len(results)} records")
        if results:
            print(f"[CacheFilter] SQL: Sample land_num: {results[0].get('land_num')}")
        
        return results
    except Exception as e:
        print(f"[CacheFilter] SQL Error: {e}")
        return []


def _filter_by_postgres(property_ids: list, question: str, filter_type: str) -> list:
    sql_results = _fetch_sql_details(property_ids)
    if not sql_results:
        return []
    
    if filter_type == "price":
        match = re.search(r'(\d+)\s*만', question)
        if match:
            max_price = int(match.group(1)) * 10000
            return [r for r in sql_results if (r.get('monthly_rent') or 0) <= max_price]
    
    return sql_results
