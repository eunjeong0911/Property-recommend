"""ES 8.17 Native kNN 벡터 검색 노드

ES 8.17 네이티브 기능 사용:
- dense_vector 필드 타입 with HNSW 인덱스
- 네이티브 knn 쿼리 (script_score 불필요)
- 하이브리드 검색 (BM25 + kNN)
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional

from elasticsearch import Elasticsearch

# libs 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.state import RAGState

logger = logging.getLogger(__name__)

# ES 인덱스 이름
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "realestate_listings")

# 모듈 레벨 싱글톤 인스턴스
_embedding_service = None
_es_client: Optional[Elasticsearch] = None


def get_embedding_service():
    """EmbeddingService 싱글톤 인스턴스 반환"""
    global _embedding_service
    if _embedding_service is None:
        from libs.clients.embedding_service import EmbeddingService
        _embedding_service = EmbeddingService.get_instance()
    return _embedding_service


def get_es_client() -> Elasticsearch:
    """Elasticsearch 8.17 클라이언트 인스턴스 반환 (싱글톤)"""
    global _es_client
    if _es_client is None:
        es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
        es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
        es_url = f"http://{es_host}:{es_port}"
        
        _es_client = Elasticsearch(
            hosts=[es_url],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        # 연결 확인
        try:
            info = _es_client.info()
            logger.info(f"[ES 8.17] Connected: {info['version']['number']}")
        except Exception as e:
            logger.warning(f"[ES 8.17] Connection check failed: {e}")
    
    return _es_client


def vector_search(
    query: str,
    top_k: int = 20,
    min_score: float = 0.5
) -> List[Dict]:
    """ES 8.17 네이티브 kNN 벡터 검색
    
    ES 8.17 네이티브 기능 사용:
    - dense_vector 필드의 HNSW 인덱스 활용
    - 네이티브 knn 파라미터 (top-level)
    
    Args:
        query: 검색 쿼리 텍스트
        top_k: 반환할 최대 결과 개수
        min_score: 최소 유사도 점수 임계값
    
    Returns:
        검색 결과 리스트, 각 결과는 land_num, search_text, score 포함
    """
    if not query or not query.strip():
        return []
    
    # 쿼리 임베딩 생성
    service = get_embedding_service()
    query_embedding = service.embed_text(query)
    
    if not query_embedding:
        logger.error("[Vector Search] Failed to generate embedding")
        return []
    
    es = get_es_client()
    
    try:
        # ES 8.17 네이티브 kNN 검색 (top-level knn 파라미터)
        result = es.search(
            index=ES_INDEX_NAME,
            knn={
                "field": "embedding",
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": top_k * 5  # 더 많은 후보로 정확도 향상
            },
            min_score=min_score,
            size=top_k,
            _source=["search_text", "land_num", "address"]
        )
        
        # 결과 파싱
        results = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]
            results.append({
                "land_num": source.get("land_num", hit["_id"]),
                "search_text": source.get("search_text", ""),
                "address": source.get("address", ""),
                "score": hit["_score"]
            })
        
        logger.info(f"[Vector Search] Found {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"[Vector Search] Error: {e}")
        return []


def hybrid_vector_search(
    query: str,
    top_k: int = 20,
    keyword_boost: float = 0.3,
    vector_boost: float = 0.7
) -> List[Dict]:
    """ES 8.17 하이브리드 검색 (BM25 + kNN)
    
    ES 8.17 네이티브 기능 사용:
    - query + knn 파라미터 동시 사용
    - RRF (Reciprocal Rank Fusion) 자동 적용
    
    Args:
        query: 검색 쿼리 텍스트
        top_k: 반환할 최대 결과 개수
        keyword_boost: 키워드 검색 가중치
        vector_boost: 벡터 검색 가중치
    
    Returns:
        하이브리드 검색 결과 리스트
    """
    if not query or not query.strip():
        return []
    
    # 쿼리 임베딩 생성
    service = get_embedding_service()
    query_embedding = service.embed_text(query)
    
    if not query_embedding:
        logger.error("[Hybrid Search] Failed to generate embedding")
        return []
    
    es = get_es_client()
    
    try:
        # ES 8.17 하이브리드 검색: query + knn
        result = es.search(
            index=ES_INDEX_NAME,
            # BM25 키워드 검색
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
            # 네이티브 kNN 벡터 검색
            knn={
                "field": "embedding",
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": top_k * 5,
                "boost": vector_boost
            },
            size=top_k,
            _source=["search_text", "land_num", "address", "style_tags", "deposit", "monthly_rent"]
        )
        
        # 결과 파싱
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
                "source": "hybrid"
            })
        
        logger.info(f"[Hybrid Search] Found {len(results)} results (BM25 + kNN)")
        return results
        
    except Exception as e:
        logger.error(f"[Hybrid Search] Error: {e}")
        return []


def filtered_knn_search(
    query: str,
    filter_conditions: Dict,
    top_k: int = 20
) -> List[Dict]:
    """ES 8.17 필터링된 kNN 검색
    
    ES 8.17 네이티브 기능 사용:
    - knn 쿼리 내 filter 파라미터
    - Pre-filtering으로 효율적인 검색
    
    Args:
        query: 검색 쿼리 텍스트
        filter_conditions: 필터 조건 (deal_type, min_deposit, max_deposit 등)
        top_k: 반환할 최대 결과 개수
    
    Returns:
        필터링된 벡터 검색 결과 리스트
    """
    if not query or not query.strip():
        return []
    
    # 쿼리 임베딩 생성
    service = get_embedding_service()
    query_embedding = service.embed_text(query)
    
    if not query_embedding:
        return []
    
    es = get_es_client()
    
    # 필터 쿼리 빌드
    filter_clauses = []
    
    if filter_conditions.get("deal_type"):
        filter_clauses.append({"term": {"deal_type": filter_conditions["deal_type"]}})
    
    if filter_conditions.get("building_type"):
        filter_clauses.append({"term": {"building_type": filter_conditions["building_type"]}})
    
    if filter_conditions.get("style_tags"):
        filter_clauses.append({"terms": {"style_tags": filter_conditions["style_tags"]}})
    
    # 가격 범위 필터
    if filter_conditions.get("min_deposit") or filter_conditions.get("max_deposit"):
        deposit_range = {"range": {"deposit": {}}}
        if filter_conditions.get("min_deposit"):
            deposit_range["range"]["deposit"]["gte"] = filter_conditions["min_deposit"]
        if filter_conditions.get("max_deposit"):
            deposit_range["range"]["deposit"]["lte"] = filter_conditions["max_deposit"]
        filter_clauses.append(deposit_range)
    
    try:
        # ES 8.17 필터링된 kNN 검색
        knn_params = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": top_k * 5
        }
        
        # 필터가 있으면 추가
        if filter_clauses:
            knn_params["filter"] = {"bool": {"must": filter_clauses}}
        
        result = es.search(
            index=ES_INDEX_NAME,
            knn=knn_params,
            size=top_k,
            _source=["search_text", "land_num", "address", "deal_type", "deposit", "monthly_rent"]
        )
        
        # 결과 파싱
        results = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]
            results.append({
                "land_num": source.get("land_num", hit["_id"]),
                "search_text": source.get("search_text", ""),
                "address": source.get("address", ""),
                "deal_type": source.get("deal_type", ""),
                "deposit": source.get("deposit", 0),
                "monthly_rent": source.get("monthly_rent", 0),
                "score": hit["_score"]
            })
        
        logger.info(f"[Filtered kNN] Found {len(results)} results with {len(filter_clauses)} filters")
        return results
        
    except Exception as e:
        logger.error(f"[Filtered kNN] Error: {e}")
        return []


def search(state: RAGState) -> RAGState:
    """RAG 파이프라인 벡터 검색 노드 (ES 8.17)"""
    query = state.get("question", "")
    
    if not query:
        state["vector_results"] = []
        state["vector_scores"] = {}
        return state
    
    try:
        # 하이브리드 검색 사용 (BM25 + kNN)
        results = hybrid_vector_search(query, top_k=20)
        state["vector_results"] = results
        state["vector_scores"] = {r["land_num"]: r["score"] for r in results}
        print(f"[Vector ES 8.17] Found {len(results)} results (Hybrid BM25+kNN)")
    except Exception as e:
        print(f"[Vector ES 8.17] Error: {e}")
        state["vector_results"] = []
        state["vector_scores"] = {}
    
    return state
