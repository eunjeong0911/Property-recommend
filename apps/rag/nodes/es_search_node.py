# =============================================================================
# Elasticsearch Search Node for RAG Pipeline
# =============================================================================
#
# 역할: Neo4j 후보 ID를 기반으로 ES 텍스트 검색 및 재정렬 수행
#
# Requirements:
# - 6.1: Neo4j로 위치/인프라 기반 후보를 먼저 추출
# - 6.2: ES로 텍스트 기반 재정렬 수행
# =============================================================================

import os
import logging
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch

from common.state import RAGState

logger = logging.getLogger(__name__)

# ES 인덱스 이름
ES_INDEX_NAME = "realestate_listings"

# ES 클라이언트 (Lazy Loading)
_es_client: Optional[Elasticsearch] = None


def get_es_client() -> Elasticsearch:
    """ES 클라이언트 인스턴스 반환 (싱글톤)"""
    global _es_client
    if _es_client is None:
        es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
        es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
        es_url = f"http://{es_host}:{es_port}"
        
        try:
            _es_client = Elasticsearch(
                hosts=[es_url],
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            if _es_client.ping():
                logger.info(f"[ES Node] Connected to Elasticsearch: {es_url}")
            else:
                logger.warning(f"[ES Node] Elasticsearch ping failed: {es_url}")
        except Exception as e:
            logger.error(f"[ES Node] Failed to connect to Elasticsearch: {e}")
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
        es = get_es_client()
        
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
