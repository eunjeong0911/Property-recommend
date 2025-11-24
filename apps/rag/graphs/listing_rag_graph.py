from langgraph.graph import StateGraph
from common.state import RAGState
from nodes import classify_node, sql_search_node, vector_search_node, generate_node

def create_rag_graph():
    workflow = StateGraph(RAGState)
    
    workflow.add_node("classify", classify_node.classify)
    workflow.add_node("sql_search", sql_search_node.search)
    workflow.add_node("vector_search", vector_search_node.search)
    workflow.add_node("generate", generate_node.generate)
    
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "sql_search")
    workflow.add_edge("sql_search", "generate")
    
    return workflow.compile()
