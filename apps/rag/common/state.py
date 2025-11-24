from typing import TypedDict, List, Optional

class RAGState(TypedDict):
    question: str
    query_type: Optional[str]
    sql_results: Optional[List]
    vector_results: Optional[List]
    graph_results: Optional[List]
    answer: Optional[str]
