from typing import TypedDict, List, Optional, Dict, Any

class RAGState(TypedDict):
    question: str
    session_id: Optional[str]  # 세션 ID
    
    # 캐시 관련 (후속 질문 필터링)
    cached_property_ids: Optional[List[str]]  # Q1에서 저장된 매물 ID
    use_cache: Optional[bool]  # 캐시 사용 여부
    filter_source: Optional[str]  # "neo4j:safety", "neo4j:convenience", "postgres" 등
    price_conditions: Optional[Dict[str, int]]  # 가격 조건: deposit_max, rent_max 등
    
    # 누적 검색 컨텍스트 (Q1+Q2+Q3... 모든 이전 결과)
    accumulated_results: Optional[Dict[str, Dict]]  # {property_id: {merged_data}}
    
    # 기존 필드
    query_type: Optional[str]
    sql_results: Optional[List]
    vector_results: Optional[List]
    graph_results: Optional[List]
    graph_summary: Optional[str]  # Neo4j 결과의 LLM 요약
    answer: Optional[str]
    
    # ES 하이브리드 검색 관련 (Requirements 6.2, 6.3)
    es_scores: Optional[Dict[str, float]]  # ES 검색 점수 {property_id: score}
    
    # 벡터 검색 관련 (Requirements 3.1, 3.2, 3.3, 3.4)
    vector_scores: Optional[Dict[str, float]]  # 벡터 검색 점수 {property_id: score}
