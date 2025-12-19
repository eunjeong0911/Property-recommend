# =============================================================================
# Elasticsearch Search Node for RAG Pipeline
# =============================================================================
#
# 역할: Neo4j 후보 ID를 기반으로 ES 텍스트 검색 및 재정렬 수행
#
# Requirements:
# - 6.1: Neo4j로 위치/인프라 기반 후보를 먼저 추출
# - 6.2: ES로 텍스트 기반 재정렬 수행
# - 4.1: ES의 kNN 쿼리와 bool 쿼리를 단일 요청으로 결합
# - 4.2: 키워드 점수와 벡터 점수를 boost 파라미터로 가중치 조합
# - 4.3: 기본값으로 keyword:0.4, vector:0.6 비율 사용
# - 4.4: ES 하이브리드 결과와 Neo4j 결과 별도 병합
# - 4.5: 각 검색 소스별 기여도 함께 제공
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
ES_INDEX_NAME = "realestate_listings"

# ES 클라이언트 (Lazy Loading)
_es_client: Optional[Elasticsearch] = None


def get_opensearch_client() -> Elasticsearch:
    """OpenSearch 클라이언트 인스턴스 반환 (싱글톤)
    
    AWS OpenSearch Service와 호환되는 클라이언트 설정
    """
    global _es_client
    if _es_client is None:
        # OpenSearch 환경변수 우선, ES 환경변수 fallback
        os_host = os.getenv("OPENSEARCH_HOST") or os.getenv("ELASTICSEARCH_HOST", "opensearch")
        os_port = os.getenv("OPENSEARCH_PORT") or os.getenv("ELASTICSEARCH_PORT", "9200")
        os_url = f"http://{os_host}:{os_port}"
        
        try:
            _es_client = Elasticsearch(
                hosts=[os_url],
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            if _es_client.ping():
                logger.info(f"[OpenSearch] Connected to: {os_url}")
            else:
                logger.warning(f"[OpenSearch] Ping failed: {os_url}")
        except Exception as e:
            logger.error(f"[OpenSearch] Failed to connect: {e}")
            raise
    
    return _es_client


def build_hybrid_query(
    keyword: Optional[str] = None,
    candidate_ids: Optional[List[str]] = None,
    style_tags: Optional[List[str]] = None,
    min_deposit: Optional[int] = None,
    max_deposit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    하이브리드 검색을 위한 ES 쿼리 빌드
    
    Args:
        keyword: 검색 키워드 (search_text 필드에서 검색)
        candidate_ids: Neo4j에서 추출한 후보 매물 ID 목록
        style_tags: 스타일 태그 목록
        min_deposit: 최소 보증금
        max_deposit: 최대 보증금
    
    Returns:
        ES bool 쿼리 딕셔너리
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
        query["bool"]["must"].append({
            "match": {
                "search_text": {
                    "query": keyword,
                    "analyzer": "nori_analyzer"
                }
            }
        })
    
    # 후보 ID 필터 (Neo4j 결과 기반) - 필수!
    if candidate_ids:
        query["bool"]["filter"].append({
            "terms": {"land_num": candidate_ids}
        })
    
    # 스타일 태그 필터
    if style_tags:
        query["bool"]["filter"].append({
            "terms": {"style_tags": style_tags}
        })
    
    # 보증금 범위 필터
    if min_deposit is not None or max_deposit is not None:
        deposit_range: Dict[str, Any] = {"range": {"deposit": {}}}
        if min_deposit is not None:
            deposit_range["range"]["deposit"]["gte"] = min_deposit
        if max_deposit is not None:
            deposit_range["range"]["deposit"]["lte"] = max_deposit
        query["bool"]["filter"].append(deposit_range)
    
    return query


def search_with_es(
    candidate_ids: List[str],
    keyword: Optional[str] = None,
    style_tags: Optional[List[str]] = None,
    min_deposit: Optional[int] = None,
    max_deposit: Optional[int] = None,
    size: int = 300
) -> Dict[str, Any]:
    """
    ES를 활용한 하이브리드 검색
    
    Args:
        candidate_ids: Neo4j에서 추출한 후보 매물 ID 목록 (필수)
        keyword: 검색 키워드
        style_tags: 스타일 태그 목록
        min_deposit: 최소 보증금
        max_deposit: 최대 보증금
        size: 반환할 최대 결과 수
    
    Returns:
        {
            'ids': List[str],  # 매물 ID 목록 (ES 점수 순)
            'scores': Dict[str, float],  # ID별 ES 점수
            'total': int  # 전체 매칭 수
        }
    """
    empty_result: Dict[str, Any] = {'ids': [], 'scores': {}, 'total': 0}
    
    # 후보 ID가 없으면 빈 결과 반환
    if not candidate_ids:
        logger.warning("[ES Node] No candidate IDs provided")
        return empty_result
    
    try:
        es = get_opensearch_client()
        
        # 쿼리 빌드
        query = build_hybrid_query(
            keyword=keyword,
            candidate_ids=candidate_ids,
            style_tags=style_tags,
            min_deposit=min_deposit,
            max_deposit=max_deposit
        )
        
        # ES 검색 실행
        response = es.search(
            index=ES_INDEX_NAME,
            query=query,
            size=size,
            _source=["land_num", "address", "search_text", "deposit", "monthly_rent", "style_tags"]
        )
        
        # 결과 파싱
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
        
    except ConnectionError as e:
        logger.error(f"[ES Node] Connection failed: {e}")
        return empty_result
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
    
    Args:
        neo4j_results: Neo4j 검색 결과 (id, total_score 포함)
        es_scores: ES 검색 결과의 ID별 점수
        neo4j_weight: Neo4j 점수 가중치 (기본 0.6)
        es_weight: ES 점수 가중치 (기본 0.4)
    
    Returns:
        조합된 점수로 재정렬된 결과 목록
    """
    if not neo4j_results:
        return []
    
    # Neo4j 점수 정규화를 위한 최대값 계산
    max_neo4j_score = max(
        (r.get('total_score', 0) for r in neo4j_results),
        default=1
    )
    if max_neo4j_score == 0:
        max_neo4j_score = 1
    
    # ES 점수 정규화를 위한 최대값 계산
    max_es_score = max(es_scores.values(), default=1) if es_scores else 1
    if max_es_score == 0:
        max_es_score = 1
    
    # 조합된 점수 계산
    combined_results = []
    for result in neo4j_results:
        prop_id = str(result.get('id', ''))
        
        # ES 결과에 없는 ID는 제외 (Requirements 6.2)
        if prop_id not in es_scores:
            continue
        
        # 정규화된 점수 계산
        neo4j_score = result.get('total_score', 0) / max_neo4j_score
        es_score = es_scores.get(prop_id, 0) / max_es_score
        
        # 가중 평균 계산
        combined_score = (neo4j_weight * neo4j_score) + (es_weight * es_score)
        
        # 결과에 조합된 점수 추가
        combined_result = {**result}
        combined_result['combined_score'] = combined_score
        combined_result['neo4j_score_normalized'] = neo4j_score
        combined_result['es_score_normalized'] = es_score
        
        combined_results.append(combined_result)
    
    # 조합된 점수로 정렬 (내림차순)
    combined_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
    
    return combined_results


# =============================================================================
# 벡터 하이브리드 검색 함수 (Requirements 4.1, 4.2, 4.3)
# =============================================================================

# 모듈 레벨 싱글톤 인스턴스 (임베딩 서비스용)
_embedding_service = None


def get_embedding_service():
    """EmbeddingService 싱글톤 인스턴스 반환"""
    global _embedding_service
    if _embedding_service is None:
        from libs.clients.embedding_service import EmbeddingService
        _embedding_service = EmbeddingService.get_instance()
    return _embedding_service


def build_knn_query(query_vector: List[float], k: int = 20) -> Dict[str, Any]:
    """OpenSearch k-NN 쿼리 빌드
    
    OpenSearch k-NN DSL 형식으로 쿼리 생성
    
    Args:
        query_vector: 쿼리 임베딩 벡터
        k: 반환할 최대 결과 개수
    
    Returns:
        OpenSearch k-NN 쿼리 딕셔너리
    """
    return {
        "knn": {
            "embedding": {
                "vector": query_vector,
                "k": k
            }
        }
    }


def hybrid_search(
    query: str,
    query_embedding: List[float],
    top_k: int = 20,
    keyword_boost: float = 0.4,
    vector_boost: float = 0.6
) -> List[Dict]:
    """ES 키워드 + 벡터 하이브리드 검색 (OpenSearch k-NN DSL 형식)
    
    Requirements:
    - 4.1: ES의 kNN 쿼리와 bool 쿼리를 단일 요청으로 결합
    - 4.2: 키워드 점수와 벡터 점수를 boost 파라미터로 가중치 조합
    - 4.3: 기본값으로 keyword:0.4, vector:0.6 비율 사용
    - 2.2: OpenSearch k-NN DSL 형식 사용
    
    Args:
        query: 검색 쿼리 텍스트
        query_embedding: 쿼리의 임베딩 벡터 (3072차원)
        top_k: 반환할 최대 결과 개수
        keyword_boost: 키워드 검색 가중치 (기본 0.4)
        vector_boost: 벡터 검색 가중치 (기본 0.6)
    
    Returns:
        검색 결과 리스트, 각 결과는 land_num, search_text, score, source 포함
    """
    if not query or not query.strip():
        return []
    
    if not query_embedding:
        return []
    
    es = get_opensearch_client()
    
    try:
        # OpenSearch 하이브리드 검색: k-NN + bool 쿼리 결합 (Requirements 4.1, 2.2)
        # OpenSearch k-NN DSL 형식 사용
        result = es.search(
            index="listings",
            query={
                "bool": {
                    "should": [
                        # 키워드 검색 (Requirements 4.2)
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["search_text^2", "주소_정보.전체주소"],
                                "boost": keyword_boost
                            }
                        },
                        # OpenSearch k-NN 쿼리 (Requirements 2.2)
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding,
                                    "k": top_k,
                                    "boost": vector_boost
                                }
                            }
                        }
                    ]
                }
            },
            size=top_k,
            _source=["search_text", "land_num", "주소_정보"]
        )
        
        # 결과 파싱
        results = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]
            results.append({
                "land_num": source.get("land_num", hit["_id"]),
                "search_text": source.get("search_text", ""),
                "score": hit["_score"],
                "source": "hybrid"
            })
        
        logger.info(f"[Hybrid Search] Found {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"[Hybrid Search] Error: {e}")
        return []


def combine_with_neo4j(
    hybrid_results: List[Dict],
    neo4j_scores: Dict[str, float],
    neo4j_weight: float = 0.3
) -> List[Dict]:
    """ES 하이브리드 결과와 Neo4j 점수 병합
    
    Requirements:
    - 4.4: ES 하이브리드 결과와 Neo4j 결과 별도 병합
    - 4.5: 각 검색 소스별 기여도 함께 제공
    
    Args:
        hybrid_results: ES 하이브리드 검색 결과 리스트
        neo4j_scores: Neo4j 검색 결과의 land_num별 점수 딕셔너리
        neo4j_weight: Neo4j 점수 가중치 (기본 0.3)
    
    Returns:
        병합된 결과 리스트, 각 결과는 final_score, es_contribution, neo4j_contribution 포함
    """
    # ES 점수 정규화를 위한 최대값 계산
    max_es_score = max((r["score"] for r in hybrid_results), default=1) if hybrid_results else 1
    if max_es_score == 0:
        max_es_score = 1
    
    # Neo4j 점수 정규화를 위한 최대값 계산
    max_neo4j_score = max(neo4j_scores.values(), default=1) if neo4j_scores else 1
    if max_neo4j_score == 0:
        max_neo4j_score = 1
    
    combined: Dict[str, Dict] = {}
    
    # ES 하이브리드 결과 처리
    for r in hybrid_results:
        land_num = r["land_num"]
        es_score_normalized = r["score"] / max_es_score
        neo4j_score = neo4j_scores.get(land_num, 0)
        neo4j_score_normalized = neo4j_score / max_neo4j_score if neo4j_score > 0 else 0
        
        # 가중치 조합
        es_contribution = es_score_normalized * (1 - neo4j_weight)
        neo4j_contribution = neo4j_score_normalized * neo4j_weight
        final_score = es_contribution + neo4j_contribution
        
        combined[land_num] = {
            **r,
            "final_score": final_score,
            "es_contribution": es_contribution,
            "neo4j_contribution": neo4j_contribution
        }
    
    # Neo4j에만 있는 결과 추가 (Requirements 4.4: 모든 고유 land_num 포함)
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
    
    # final_score로 정렬 (내림차순)
    sorted_results = sorted(combined.values(), key=lambda x: x["final_score"], reverse=True)
    
    logger.info(f"[Combine] Merged {len(sorted_results)} results from ES and Neo4j")
    return sorted_results


def es_rerank(state: RAGState) -> RAGState:
    """
    ES 기반 재정렬 노드
    
    Neo4j 검색 결과를 ES로 재정렬하여 하이브리드 검색 수행
    
    Requirements:
    - 6.1: Neo4j로 위치/인프라 기반 후보를 먼저 추출
    - 6.2: ES로 텍스트 기반 재정렬 수행
    """
    question = state.get("question", "")
    graph_results = state.get("graph_results", [])
    price_conditions = state.get("price_conditions", {})
    
    print(f"\n{'='*60}")
    print(f"[ES Rerank] 🔍 Starting ES-based reranking...")
    print(f"[ES Rerank] 📝 Question: {question}")
    print(f"[ES Rerank] 📊 Neo4j results count: {len(graph_results)}")
    print(f"{'='*60}\n")
    
    # Neo4j 결과가 없으면 그대로 반환
    if not graph_results:
        print("[ES Rerank] ⚠️ No Neo4j results to rerank")
        return state
    
    # Neo4j 결과에서 후보 ID 추출
    candidate_ids = []
    for result in graph_results:
        prop_id = result.get('id')
        if prop_id:
            candidate_ids.append(str(prop_id))
    
    if not candidate_ids:
        print("[ES Rerank] ⚠️ No candidate IDs extracted from Neo4j results")
        return state
    
    print(f"[ES Rerank] 📋 Extracted {len(candidate_ids)} candidate IDs")
    
    # 가격 조건 추출
    min_deposit = price_conditions.get('deposit_min')
    max_deposit = price_conditions.get('deposit_max')
    
    # ES 검색 실행
    es_result = search_with_es(
        candidate_ids=candidate_ids,
        keyword=question,  # 질문을 키워드로 사용
        min_deposit=min_deposit,
        max_deposit=max_deposit
    )
    
    print(f"[ES Rerank] 🔎 ES returned {len(es_result['ids'])} results")
    
    # ES 결과가 없으면 Neo4j 결과 그대로 반환
    if not es_result['ids']:
        print("[ES Rerank] ⚠️ No ES results, keeping Neo4j order")
        return state
    
    # 점수 조합 및 재정렬
    reranked_results = combine_scores(
        neo4j_results=graph_results,
        es_scores=es_result['scores']
    )
    
    print(f"[ES Rerank] ✅ Reranked {len(reranked_results)} results")
    
    # 상태 업데이트
    state["graph_results"] = reranked_results
    state["es_scores"] = es_result['scores']
    
    return state
