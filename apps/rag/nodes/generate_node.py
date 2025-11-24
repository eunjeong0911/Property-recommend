from common.state import RAGState

def generate(state: RAGState) -> RAGState:
    # TODO: Implement answer generation
    state["answer"] = "Generated answer"
    return state
