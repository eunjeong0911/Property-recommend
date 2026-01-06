# =============================================================================
# Elasticsearch 8.17 Search Node for RAG Pipeline
# =============================================================================
# ES 8.17 네이티브 기능 사용:
# - dense_vector 필드 with HNSW 인덱스
# - 네이티브 knn 쿼리 파라미터
# - 하이브리드 검색 (BM25 + kNN)
# - 필터링된 kNN 검색
# =============================================================================

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch

# libs 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.state import RAGState

logger = logging.getLogger(__name__)

# ES 인덱스 이름
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "realestate_listings")

# ES 클라이언트 (Lazy Loading)
_es_client: Optional[Elasticsearch] = None


def get_es_client() -> Elasticsearch:
    """Elasticsearch 8.17 클라이언트 인스턴스 반환 (싱글톤)"""
    global _es_client
    if _es_client is None:
        es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
        es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
        es_url = f"http://{es_host}:{es_port}"
        
        try:
            _es_client = Elasticsearch(
                hosts=[es_url],
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            if _es_client.ping():
                info = _es_client.info()
                logger.info(f"[ES 8.17] Connected: {es_url} (v{info['version']['number']})")
            else:
                logger.warning(f"[ES 8.17] Ping failed: {es_url}")
        except Exception as e:
            logger.error(f"[ES 8.17] Connection failed: {e}")
            raise
    
    return _es_client


def build_hybrid_query(
    keyword: Optional[str] = None,
    candidate_ids: Optional[List[str]] = None,
    style_tags: Optional[List[str]] = None,
    min_deposit: Optional[int] = None,
    max_deposit: Optional[int] = None,
    building_type: Optional[str] = None,
    deal_type: Optional[str] = None,
    max_rent: Optional[int] = None,
) -> Dict[str, Any]:
    """
    하이브리드 검색을 위한 ES bool 쿼리 빌드
    """
    query: Dict[str, Any] = {
        "bool": {
            "must": [],
            "filter": [],
            "should": []
        }
    }
    
    # 키워드 검색 (search_text 필드)
    if keyword:
        query["bool"]["should"].append({
            "multi_match": {
                "query": keyword,
                "fields": ["search_text^3", "address^2", "style_tags"],
                "type": "best_fields"
            }
        })
    
    # 후보 ID 필터 (Neo4j 결과 기반)
    if candidate_ids:
        query["bool"]["filter"].append({
            "terms": {"land_num": candidate_ids}
        })
    
    # 스타일 태그 필터
    if style_tags:
        query["bool"]["filter"].append({
            "terms": {"style_tags": style_tags}
        })
        
    # [NEW] 건물 유형 필터
    if building_type:
        query["bool"]["filter"].append({
            "term": {"building_type": building_type}
        })
        
    # [NEW] 거래 유형 필터
    if deal_type:
        query["bool"]["filter"].append({
            "term": {"deal_type": deal_type}
        })
    
    # 보증금 범위 필터
    if min_deposit is not None or max_deposit is not None:
        deposit_range: Dict[str, Any] = {"range": {"deposit": {}}}
        if min_deposit is not None:
            deposit_range["range"]["deposit"]["gte"] = min_deposit
        if max_deposit is not None:
            deposit_range["range"]["deposit"]["lte"] = max_deposit
        query["bool"]["filter"].append(deposit_range)
        
    # [NEW] 월세 상한 필터
    if max_rent is not None:
        rent_range: Dict[str, Any] = {"range": {"monthly_rent": {"lte": max_rent}}}
        query["bool"]["filter"].append(rent_range)
    
    return query


def search_with_es(
    candidate_ids: List[str],
    keyword: Optional[str] = None,
    style_tags: Optional[List[str]] = None,
    min_deposit: Optional[int] = None,
    max_deposit: Optional[int] = None,
    building_type: Optional[str] = None,
    deal_type: Optional[str] = None,
    max_rent: Optional[int] = None,
    size: int = 300
) -> Dict[str, Any]:
    """
    ES를 활용한 하이브리드 검색 (Neo4j 후보 기반)
    """
    empty_result: Dict[str, Any] = {'ids': [], 'scores': {}, 'total': 0}
    
    if not candidate_ids:
        logger.warning("[ES Node] No candidate IDs provided")
        return empty_result
    
    try:
        es = get_es_client()
        
        query = build_hybrid_query(
            keyword=keyword,
            candidate_ids=candidate_ids,
            style_tags=style_tags,
            min_deposit=min_deposit,
            max_deposit=max_deposit,
            building_type=building_type,
            deal_type=deal_type,
            max_rent=max_rent
        )
        
        response = es.search(
            index=ES_INDEX_NAME,
            query=query,
            size=size,
            _source=["land_num", "address", "search_text", "deposit", "monthly_rent", "style_tags", "building_type", "deal_type"]
        )
        
        ids: List[str] = []
        scores: Dict[str, float] = {}
        
        for hit in response['hits']['hits']:
            land_num = hit['_source'].get('land_num')
            if land_num:
                ids.append(str(land_num))
                scores[str(land_num)] = hit['_score'] or 0.0
        
        total = response['hits']['total']
        total_count = total['value'] if isinstance(total, dict) else total
        
        logger.info(f"[ES Node] Found {len(ids)} results from {len(candidate_ids)} candidates")
        
        return {
            'ids': ids,
            'scores': scores,
            'total': total_count
        }
        
    except Exception as e:
        logger.error(f"[ES Node] Search error: {e}")
        return empty_result


def combine_scores(
    neo4j_results: List[Dict[str, Any]],
    es_scores: Dict[str, float],
    neo4j_weight: float = 0.6,
    es_weight: float = 0.4
) -> List[Dict[str, Any]]:
    """
    Neo4j 점수와 ES 점수를 조합하여 최종 순위 결정
    """
    if not neo4j_results:
        return []
    
    # 점수 정규화
    max_neo4j_score = max((r.get('total_score', 0) for r in neo4j_results), default=1) or 1
    max_es_score = max(es_scores.values(), default=1) or 1
    
    combined_results = []
    for result in neo4j_results:
        prop_id = str(result.get('id', ''))
        
        if prop_id not in es_scores:
            continue
        
        neo4j_score = result.get('total_score', 0) / max_neo4j_score
        es_score = es_scores.get(prop_id, 0) / max_es_score
        combined_score = (neo4j_weight * neo4j_score) + (es_weight * es_score)
        
        combined_result = {**result}
        combined_result['combined_score'] = combined_score
        combined_result['neo4j_score_normalized'] = neo4j_score
        combined_result['es_score_normalized'] = es_score
        
        combined_results.append(combined_result)
    
    combined_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
    return combined_results


# =============================================================================
# ES 8.17 네이티브 벡터 하이브리드 검색 함수
# =============================================================================

_embedding_service = None


def get_embedding_service():
    """EmbeddingService 싱글톤 인스턴스 반환"""
    global _embedding_service
    if _embedding_service is None:
        from libs.clients.embedding_service import EmbeddingService
        _embedding_service = EmbeddingService.get_instance()
    return _embedding_service


def hybrid_search(
    query: str,
    query_embedding: List[float],
    top_k: int = 20,
    keyword_boost: float = 0.3,
    vector_boost: float = 0.7,
    filter_conditions: Optional[Dict] = None
) -> List[Dict]:
    """ES 8.17 하이브리드 검색 (BM25 + 네이티브 kNN)
    
    ES 8.17 네이티브 기능 사용:
    - query + knn 파라미터 동시 사용
    - knn 쿼리 내 filter 지원
    - 자동 점수 조합
    
    Args:
        query: 검색 쿼리 텍스트
        query_embedding: 쿼리 임베딩 벡터 (3072차원)
        top_k: 반환할 최대 결과 개수
        keyword_boost: 키워드 검색 가중치
        vector_boost: 벡터 검색 가중치
        filter_conditions: 필터 조건 딕셔너리
    
    Returns:
        하이브리드 검색 결과 리스트
    """
    if not query or not query.strip():
        return []
    
    if not query_embedding:
        return []
    
    es = get_es_client()
    
    try:
        # kNN 파라미터 빌드
        knn_params = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": top_k * 5,
            "boost": vector_boost
        }
        
        # 필터 조건이 있으면 kNN에 적용 (Pre-filtering)
        if filter_conditions:
            filter_clauses = []
            if filter_conditions.get("deal_type"):
                filter_clauses.append({"term": {"deal_type": filter_conditions["deal_type"]}})
            if filter_conditions.get("style_tags"):
                filter_clauses.append({"terms": {"style_tags": filter_conditions["style_tags"]}})
            if filter_conditions.get("candidate_ids"):
                filter_clauses.append({"terms": {"land_num": filter_conditions["candidate_ids"]}})
            
            # 가격 필터
            if filter_conditions.get("min_deposit") or filter_conditions.get("max_deposit"):
                deposit_range = {"range": {"deposit": {}}}
                if filter_conditions.get("min_deposit"):
                    deposit_range["range"]["deposit"]["gte"] = filter_conditions["min_deposit"]
                if filter_conditions.get("max_deposit"):
                    deposit_range["range"]["deposit"]["lte"] = filter_conditions["max_deposit"]
                filter_clauses.append(deposit_range)
            
            if filter_clauses:
                knn_params["filter"] = {"bool": {"must": filter_clauses}}
        
        # ES 8.17 하이브리드 검색 실행
        result = es.search(
            index=ES_INDEX_NAME,
            query={
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["search_text^3", "address^2", "style_tags"],
                                "type": "best_fields",
                                "boost": keyword_boost
                            }
                        }
                    ]
                }
            },
            knn=knn_params,
            size=top_k,
            _source=["search_text", "land_num", "address", "style_tags", "deposit", "monthly_rent"]
        )
        
        results = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]
            results.append({
                "land_num": source.get("land_num", hit["_id"]),
                "search_text": source.get("search_text", ""),
                "address": source.get("address", ""),
                "style_tags": source.get("style_tags", []),
                "deposit": source.get("deposit", 0),
                "monthly_rent": source.get("monthly_rent", 0),
                "score": hit["_score"],
                "source": "hybrid_es8"
            })
        
        logger.info(f"[Hybrid ES 8.17] Found {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"[Hybrid ES 8.17] Error: {e}")
        return []


def combine_with_neo4j(
    hybrid_results: List[Dict],
    neo4j_scores: Dict[str, float],
    neo4j_weight: float = 0.3
) -> List[Dict]:
    """ES 하이브리드 결과와 Neo4j 점수 병합"""
    max_es_score = max((r["score"] for r in hybrid_results), default=1) or 1
    max_neo4j_score = max(neo4j_scores.values(), default=1) or 1
    
    combined: Dict[str, Dict] = {}
    
    for r in hybrid_results:
        land_num = r["land_num"]
        es_score_normalized = r["score"] / max_es_score
        neo4j_score = neo4j_scores.get(land_num, 0)
        neo4j_score_normalized = neo4j_score / max_neo4j_score if neo4j_score > 0 else 0
        
        es_contribution = es_score_normalized * (1 - neo4j_weight)
        neo4j_contribution = neo4j_score_normalized * neo4j_weight
        final_score = es_contribution + neo4j_contribution
        
        combined[land_num] = {
            **r,
            "final_score": final_score,
            "es_contribution": es_contribution,
            "neo4j_contribution": neo4j_contribution
        }
    
    # Neo4j에만 있는 결과도 추가
    for land_num, score in neo4j_scores.items():
        if land_num not in combined:
            neo4j_score_normalized = score / max_neo4j_score if score > 0 else 0
            neo4j_contribution = neo4j_score_normalized * neo4j_weight
            combined[land_num] = {
                "land_num": land_num,
                "search_text": "",
                "score": 0,
                "source": "neo4j_only",
                "final_score": neo4j_contribution,
                "es_contribution": 0,
                "neo4j_contribution": neo4j_contribution
            }
    
    sorted_results = sorted(combined.values(), key=lambda x: x["final_score"], reverse=True)
    logger.info(f"[Combine] Merged {len(sorted_results)} results from ES 8.17 and Neo4j")
    return sorted_results


def es_rerank(state: RAGState) -> RAGState:
    """
    ES 8.17 기반 재정렬 노드
    
    Neo4j 검색 결과를 ES 8.17 네이티브 kNN으로 재정렬
    """
    question = state.get("question", "")
    graph_results = state.get("graph_results", [])
    price_conditions = state.get("price_conditions", {})
    
    print(f"\n{'='*60}")
    print(f"[ES 8.17 Rerank] 🔍 Starting ES-based reranking...")
    print(f"[ES 8.17 Rerank] 📝 Question: {question}")
    print(f"[ES 8.17 Rerank] 📊 Neo4j results count: {len(graph_results)}")
    print(f"{'='*60}\n")
    
    if not graph_results:
        print("[ES 8.17 Rerank] ⚠️ No Neo4j results to rerank")
        return state
    
    # 후보 ID 추출
    candidate_ids = [str(r.get('id', '')) for r in graph_results if r.get('id')]
    
    if not candidate_ids:
        print("[ES 8.17 Rerank] ⚠️ No candidate IDs extracted")
        return state
    
    print(f"[ES 8.17 Rerank] 📋 Extracted {len(candidate_ids)} candidate IDs")
    
    # 가격 조건 추출
    min_deposit = price_conditions.get('deposit_min')
    max_deposit = price_conditions.get('deposit_max')
    
    # ES 검색 실행
    es_result = search_with_es(
        candidate_ids=candidate_ids,
        keyword=question,
        min_deposit=min_deposit,
        max_deposit=max_deposit
    )
    
    print(f"[ES 8.17 Rerank] 🔎 ES returned {len(es_result['ids'])} results")
    
    if not es_result['ids']:
        print("[ES 8.17 Rerank] ⚠️ No ES results, keeping Neo4j order")
        return state
    
    # 점수 조합 및 재정렬
    reranked_results = combine_scores(
        neo4j_results=graph_results,
        es_scores=es_result['scores']
    )
    
    print(f"[ES 8.17 Rerank] ✅ Reranked {len(reranked_results)} results")
    
    state["graph_results"] = reranked_results
    state["es_scores"] = es_result['scores']
    
    return state


def es_vector_rerank(state: RAGState) -> RAGState:
    """
    ES 8.17 벡터 기반 재정렬 노드
    
    Neo4j 결과를 ES 8.17 하이브리드 검색(BM25 + kNN)으로 재정렬
    """
    question = state.get("question", "")
    graph_results = state.get("graph_results", [])
    price_conditions = state.get("price_conditions", {})
    
    if not graph_results or not question:
        return state
    
    print(f"[ES 8.17 Vector Rerank] Starting with {len(graph_results)} candidates...")
    
    # 임베딩 생성
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.embed_text(question)
    
    if not query_embedding:
        print("[ES 8.17 Vector Rerank] Failed to generate embedding")
        return state
    
    # 후보 ID 추출
    candidate_ids = [str(r.get('id', '')) for r in graph_results if r.get('id')]
    
    # 필터 조건 빌드
    filter_conditions = {
        "candidate_ids": candidate_ids,
        "min_deposit": price_conditions.get('deposit_min'),
        "max_deposit": price_conditions.get('deposit_max')
    }
    
    # 하이브리드 검색 실행
    results = hybrid_search(
        query=question,
        query_embedding=query_embedding,
        top_k=len(candidate_ids),
        filter_conditions=filter_conditions
    )
    
    if not results:
        print("[ES 8.17 Vector Rerank] No results, keeping original order")
        return state
    
    # Neo4j 점수와 병합
    neo4j_scores = {str(r.get('id', '')): r.get('total_score', 0) for r in graph_results}
    combined_results = combine_with_neo4j(results, neo4j_scores)
    
    # 결과를 graph_results 형식으로 변환
    reranked_results = []
    for r in combined_results:
        # 원본 Neo4j 결과에서 상세 정보 가져오기
        original = next((g for g in graph_results if str(g.get('id', '')) == r['land_num']), None)
        if original:
            reranked = {**original}
            reranked['combined_score'] = r['final_score']
            reranked['es_vector_score'] = r['score']
            reranked['es_contribution'] = r['es_contribution']
            reranked['neo4j_contribution'] = r['neo4j_contribution']
            reranked_results.append(reranked)
    
    print(f"[ES 8.17 Vector Rerank] ✅ Reranked {len(reranked_results)} results (Hybrid BM25+kNN)")
    
    state["graph_results"] = reranked_results
    state["es_hybrid_results"] = results
    
    return state
