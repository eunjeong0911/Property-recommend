from common.state import RAGState

def classify(state: RAGState) -> RAGState:
    # TODO: Implement query classification
    state["query_type"] = "search"
    return state
