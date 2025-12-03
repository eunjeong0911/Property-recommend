from typing import TypedDict, List, Optional

class RAGState(TypedDict):
    question: str
    query_type: Optional[str]
    sql_results: Optional[List]
    vector_results: Optional[List]
    graph_results: Optional[List]
    graph_summary: Optional[str]  # Neo4j 결과의 LLM 요약
    answer: Optional[str]
