from typing import List
from langgraph.graph import StateGraph, END
from common.state import RAGState
from nodes import classify_node, sql_search_node, vector_search_node, generate_node, neo4j_search_node, cache_filter_node, es_search_node

def create_rag_graph():
    """
    RAG 그래프 생성 (하이브리드 검색 통합 + 벡터 검색)
    
    흐름 (조건부):
    1. classify: 질문 분류 + 캐시 확인
    2-A. [캐시 있음] cache_filter → generate (sql_search 스킵!)
    2-B. [캐시 없음] 병렬 실행:
         - neo4j_search → es_rerank (위치/인프라 + 텍스트 기반)
         - vector_search (시맨틱 벡터 검색)
         → merge_results → sql_search → generate
    
    하이브리드 검색 (Requirements 4.1, 6.1, 6.2, 6.3):
    - Neo4j: 위치/인프라 기반 후보 추출
    - ES: 텍스트 기반 재정렬
    - Vector: 시맨틱 벡터 검색 (kNN)
    - 최종 결과: Neo4j 점수 + ES 점수 + Vector 점수 조합
    """
    workflow = StateGraph(RAGState)
    
    # 노드 등록
    workflow.add_node("classify", classify_node.classify)
    workflow.add_node("cache_filter", cache_filter_node.cache_filter)
    workflow.add_node("parallel_search", parallel_search_node)  # 병렬 검색 노드 (Neo4j + Vector)
    workflow.add_node("es_rerank", es_search_node.es_rerank)  # ES 재정렬 노드
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
            print("[Router] ✗ No cache → parallel_search")
            return "parallel_search"
    
    workflow.add_conditional_edges(
        "classify",
        route_by_cache,
        {
            "cache_filter": "cache_filter",
            "parallel_search": "parallel_search"
        }
    )
    
    # cache_filter → generate (직접! sql_search 스킵)
    workflow.add_edge("cache_filter", "generate")
    
    # 하이브리드 검색 경로 (Requirements 4.1, 6.1, 6.2, 6.3):
    # parallel_search (Neo4j + Vector) → es_rerank → sql_search → generate
    workflow.add_edge("parallel_search", "es_rerank")  # 병렬 검색 후 ES 재정렬
    workflow.add_edge("es_rerank", "sql_search")    # ES 재정렬 후 SQL 조회
    workflow.add_edge("sql_search", "generate")
    
    return workflow.compile()


def parallel_search_node(state: RAGState) -> RAGState:
    """
    Neo4j 검색과 벡터 검색을 동시에 실행하는 병렬 검색 노드
    
    Requirements:
    - 4.1: ES의 kNN 쿼리와 bool 쿼리를 단일 요청으로 결합
    - 3.1: 사용자 질문을 text-embedding-3-large로 임베딩
    - 3.2: ES kNN 검색을 사용하여 상위 N개 결과 반환
    """
    import concurrent.futures
    
    print(f"\n{'='*60}")
    print(f"[Parallel Search] 🚀 Starting parallel search...")
    print(f"{'='*60}\n")
    
    # 병렬 실행을 위한 함수들
    def run_neo4j_search():
        return neo4j_search_node.search(state.copy())
    
    def run_vector_search():
        return vector_search_node.search(state.copy())
    
    # ThreadPoolExecutor로 병렬 실행
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        neo4j_future = executor.submit(run_neo4j_search)
        vector_future = executor.submit(run_vector_search)
        
        # 결과 수집
        try:
            neo4j_state = neo4j_future.result(timeout=30)
            print(f"[Parallel Search] ✅ Neo4j search completed")
        except Exception as e:
            print(f"[Parallel Search] ❌ Neo4j search failed: {e}")
            neo4j_state = state.copy()
        
        try:
            vector_state = vector_future.result(timeout=30)
            print(f"[Parallel Search] ✅ Vector search completed")
        except Exception as e:
            print(f"[Parallel Search] ❌ Vector search failed: {e}")
            vector_state = state.copy()
    
    # 결과 병합
    state["graph_results"] = neo4j_state.get("graph_results", [])
    state["graph_summary"] = neo4j_state.get("graph_summary", "")
    state["vector_results"] = vector_state.get("vector_results", [])
    state["vector_scores"] = vector_state.get("vector_scores", {})
    
    # 벡터 검색 결과를 그래프 결과에 병합
    state = merge_search_results(state)
    
    print(f"[Parallel Search] 📊 Graph results: {len(state.get('graph_results', []))}")
    print(f"[Parallel Search] 📊 Vector results: {len(state.get('vector_results', []))}")
    
    return state


def merge_search_results(state: RAGState) -> RAGState:
    """
    Neo4j/ES 하이브리드 검색 결과와 벡터 검색 결과 병합
    
    Requirements:
    - 4.1: ES의 kNN 쿼리와 bool 쿼리를 단일 요청으로 결합
    - 4.4: ES 하이브리드 결과와 Neo4j 결과 별도 병합
    - 4.5: 각 검색 소스별 기여도 함께 제공
    """
    graph_results = state.get("graph_results", [])
    vector_results = state.get("vector_results", [])
    vector_scores = state.get("vector_scores", {})
    es_scores = state.get("es_scores", {})
    
    print(f"\n{'='*60}")
    print(f"[Merge] 🔀 Merging search results...")
    print(f"[Merge] 📊 Graph results: {len(graph_results)}")
    print(f"[Merge] 📊 Vector results: {len(vector_results)}")
    print(f"{'='*60}\n")
    
    # 결과가 없으면 그대로 반환
    if not graph_results and not vector_results:
        print("[Merge] ⚠️ No results to merge")
        return state
    
    # 벡터 검색 결과가 없으면 그래프 결과만 사용
    if not vector_results:
        print("[Merge] ⚠️ No vector results, using graph results only")
        return state
    
    # 그래프 결과가 없으면 벡터 결과만 사용
    if not graph_results:
        print("[Merge] ⚠️ No graph results, using vector results only")
        # 벡터 결과를 그래프 결과 형식으로 변환
        state["graph_results"] = [
            {
                "id": r["land_num"],
                "total_score": r["score"],
                "vector_score": r["score"],
                "source": "vector"
            }
            for r in vector_results
        ]
        return state
    
    # 결과 병합: 그래프 결과에 벡터 점수 추가
    merged_results = {}
    
    # 그래프 결과 처리 (Neo4j + ES 하이브리드)
    for result in graph_results:
        prop_id = str(result.get("id", ""))
        if prop_id:
            merged_results[prop_id] = {
                **result,
                "vector_score": vector_scores.get(prop_id, 0),
                "has_vector": prop_id in vector_scores
            }
    
    # 벡터 결과 중 그래프에 없는 것 추가
    for result in vector_results:
        prop_id = str(result.get("land_num", ""))
        if prop_id and prop_id not in merged_results:
            merged_results[prop_id] = {
                "id": prop_id,
                "total_score": result["score"] * 0.5,  # 벡터만 있는 경우 가중치 낮춤
                "vector_score": result["score"],
                "search_text": result.get("search_text", ""),
                "source": "vector_only",
                "has_vector": True
            }
    
    # 최종 점수 계산 및 정렬
    # 벡터 점수가 있는 결과에 보너스 부여
    for prop_id, result in merged_results.items():
        base_score = result.get("total_score", 0) or result.get("combined_score", 0)
        vector_score = result.get("vector_score", 0)
        
        # 벡터 점수 정규화 (0-1 범위로)
        max_vector_score = max(vector_scores.values(), default=1) if vector_scores else 1
        if max_vector_score > 0:
            normalized_vector = vector_score / max_vector_score
        else:
            normalized_vector = 0
        
        # 최종 점수: 기존 점수 70% + 벡터 점수 30%
        if result.get("has_vector"):
            result["final_merged_score"] = base_score * 0.7 + normalized_vector * 0.3
        else:
            result["final_merged_score"] = base_score * 0.7  # 벡터 없으면 기존 점수만
    
    # 최종 점수로 정렬
    sorted_results = sorted(
        merged_results.values(),
        key=lambda x: x.get("final_merged_score", 0),
        reverse=True
    )
    
    print(f"[Merge] ✅ Merged {len(sorted_results)} results")
    
    # 상태 업데이트
    state["graph_results"] = sorted_results
    
    return state
