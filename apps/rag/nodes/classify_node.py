from common.state import RAGState

def classify(state: RAGState) -> RAGState:
    # For now, default to graph search
    state["query_type"] = "graph_search"
    return state
