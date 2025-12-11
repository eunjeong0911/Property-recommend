from langgraph.graph import StateGraph
from common.state import RAGState
from nodes import classify_node, sql_search_node, vector_search_node, generate_node, neo4j_search_node, cache_filter_node

def create_rag_graph():
    """
    RAG 그래프 생성
    
    흐름 (조건부):
    1. classify: 질문 분류 + 캐시 확인
    2-A. [캐시 있음] cache_filter → generate (sql_search 스킵!)
    2-B. [캐시 없음] neo4j_search → sql_search → generate
    """
    workflow = StateGraph(RAGState)
    
    # 노드 등록
    workflow.add_node("classify", classify_node.classify)
    workflow.add_node("cache_filter", cache_filter_node.cache_filter)
    workflow.add_node("neo4j_search", neo4j_search_node.search)
    workflow.add_node("sql_search", sql_search_node.search)
    workflow.add_node("generate", generate_node.generate)
    
    # 진입점
    workflow.set_entry_point("classify")
    
    # 조건부 라우팅: 캐시 여부에 따라 분기
    def route_by_cache(state: RAGState) -> str:
        cached_ids = state.get("cached_property_ids", [])
        if cached_ids and len(cached_ids) > 0:
            print(f"[Router] ✓ Cache found: {len(cached_ids)} IDs → cache_filter")
            return "cache_filter"
        else:
            print("[Router] ✗ No cache → neo4j_search")
            return "neo4j_search"
    
    workflow.add_conditional_edges(
        "classify",
        route_by_cache,
        {
            "cache_filter": "cache_filter",
            "neo4j_search": "neo4j_search"
        }
    )
    
    # cache_filter → generate (직접! sql_search 스킵)
    workflow.add_edge("cache_filter", "generate")
    
    # neo4j_search → sql_search → generate (일반 경로)
    workflow.add_edge("neo4j_search", "sql_search")
    workflow.add_edge("sql_search", "generate")
    
    return workflow.compile()
