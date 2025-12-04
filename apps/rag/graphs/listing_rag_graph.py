from langgraph.graph import StateGraph
from common.state import RAGState
from nodes import classify_node, sql_search_node, vector_search_node, generate_node, neo4j_search_node

def create_rag_graph():
    """
    RAG 그래프 생성
    
    흐름:
    1. classify: 질문 분류
    2. neo4j_search: Neo4j에서 위치 기반 매물 검색 (가까운 역, 시설 등)
    3. sql_search: Neo4j 결과의 매물 ID로 PostgreSQL에서 상세 정보 조회
    4. generate: 두 결과를 합쳐서 답변 생성
    """
    workflow = StateGraph(RAGState)
    
    workflow.add_node("classify", classify_node.classify)
    workflow.add_node("neo4j_search", neo4j_search_node.search)
    workflow.add_node("sql_search", sql_search_node.search)
    workflow.add_node("generate", generate_node.generate)
    
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "neo4j_search")
    workflow.add_edge("neo4j_search", "sql_search")
    workflow.add_edge("sql_search", "generate")
    
    return workflow.compile()
