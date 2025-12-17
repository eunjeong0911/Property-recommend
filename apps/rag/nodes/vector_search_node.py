"""ES kNN 벡터 검색 노드

Requirements:
- 3.1: 사용자 질문을 text-embedding-3-large로 임베딩
- 3.2: ES kNN 검색을 사용하여 상위 N개 결과 반환
- 3.3: 매물 ID, 유사도 점수, search_text 포함
- 3.4: min_score 파라미터로 임계값 이하 결과 필터링
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
ES_INDEX_NAME = "listings"

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
    """ES 클라이언트 인스턴스 반환 (싱글톤)"""
    global _es_client
    if _es_client is None:
        es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
        es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
        es_url = f"http://{es_host}:{es_port}"
        
        _es_client = Elasticsearch(
            hosts=[es_url],
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
    return _es_client


def vector_search(
    query: str,
    top_k: int = 20,
    min_score: float = 0.5
) -> List[Dict]:
    """ES kNN 벡터 검색
    
    Args:
        query: 검색 쿼리 텍스트
        top_k: 반환할 최대 결과 개수 (Requirements 3.2)
        min_score: 최소 유사도 점수 임계값 (Requirements 3.4)
    
    Returns:
        검색 결과 리스트, 각 결과는 land_num, search_text, score 포함 (Requirements 3.3)
    """
    if not query or not query.strip():
        return []
    
    # 쿼리 임베딩 (Requirements 3.1)
    service = get_embedding_service()
    query_embedding = service.embed_text(query)
    
    # ES kNN 검색 (Requirements 3.2)
    es = get_es_client()
    
    try:
        result = es.search(
            index=ES_INDEX_NAME,
            knn={
                "field": "embedding",
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": top_k * 2
            },
            min_score=min_score,
            size=top_k,
            _source=["search_text", "land_num", "주소_정보"]
        )
        
        # 결과 파싱 (Requirements 3.3: land_num, score, search_text 포함)
        results = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]
            results.append({
                "land_num": source.get("land_num", hit["_id"]),
                "search_text": source.get("search_text", ""),
                "score": hit["_score"]
            })
        
        return results
        
    except Exception as e:
        logger.error(f"[Vector Search] Error: {e}")
        return []


def search(state: RAGState) -> RAGState:
    """RAG 파이프라인 벡터 검색 노드
    
    Requirements:
    - 3.1: 사용자 질문을 text-embedding-3-large로 임베딩
    - 3.2: ES kNN 검색을 사용하여 상위 N개 결과 반환
    - 3.3: 매물 ID, 유사도 점수, search_text 포함
    - 3.4: min_score 파라미터로 임계값 이하 결과 필터링
    """
    query = state.get("question", "")
    
    if not query:
        state["vector_results"] = []
        state["vector_scores"] = {}
        return state
    
    try:
        results = vector_search(query, top_k=20, min_score=0.5)
        state["vector_results"] = results
        state["vector_scores"] = {r["land_num"]: r["score"] for r in results}
        print(f"[Vector] Found {len(results)} results")
    except Exception as e:
        print(f"[Vector] Error: {e}")
        state["vector_results"] = []
        state["vector_scores"] = {}
    
    return state
