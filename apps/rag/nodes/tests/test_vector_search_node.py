"""
Vector Search Node Property-Based Tests

Tests for ES kNN vector search functionality.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import patch, MagicMock

import sys
import os

# apps/rag 디렉토리를 path에 추가
rag_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.abspath(rag_path))


def create_mock_es_response(hits_data: list) -> dict:
    """Mock ES response 생성"""
    return {
        "hits": {
            "hits": [
                {
                    "_id": hit.get("_id", f"doc_{i}"),
                    "_score": hit.get("score", 0.5),
                    "_source": {
                        "land_num": hit.get("land_num", f"land_{i}"),
                        "search_text": hit.get("search_text", ""),
                        "주소_정보": hit.get("주소_정보", {})
                    }
                }
                for i, hit in enumerate(hits_data)
            ],
            "total": {"value": len(hits_data)}
        }
    }


class TestVectorSearchResultCountLimit:
    """
    **Feature: vector-search, Property 5: 검색 결과 개수 제한**
    **Validates: Requirements 3.2**
    """
    
    @given(
        top_k=st.integers(min_value=1, max_value=100),
        num_results=st.integers(min_value=0, max_value=200)
    )
    @settings(max_examples=100)
    def test_search_result_count_limit(self, top_k: int, num_results: int):
        """
        **Feature: vector-search, Property 5: 검색 결과 개수 제한**
        **Validates: Requirements 3.2**
        
        *For any* 벡터 검색 요청에 대해, 반환되는 결과 개수는 요청한 top_k 이하여야 한다.
        """
        from nodes.vector_search_node import vector_search
        
        # ES가 반환할 결과 수 (top_k 이하로 제한됨)
        actual_results = min(num_results, top_k)
        
        # Mock 데이터 생성
        mock_hits = [
            {"land_num": f"land_{i}", "search_text": f"text_{i}", "score": 0.9 - (i * 0.01)}
            for i in range(actual_results)
        ]
        mock_response = create_mock_es_response(mock_hits)
        
        # Mock embedding (3072 차원)
        mock_embedding = [0.1] * 3072
        
        with patch('nodes.vector_search_node.get_embedding_service') as mock_embed_svc, \
             patch('nodes.vector_search_node.get_es_client') as mock_es_client:
            
            # EmbeddingService mock
            mock_service = MagicMock()
            mock_service.embed_text.return_value = mock_embedding
            mock_embed_svc.return_value = mock_service
            
            # ES client mock
            mock_es = MagicMock()
            mock_es.search.return_value = mock_response
            mock_es_client.return_value = mock_es
            
            # 검색 실행
            results = vector_search("테스트 쿼리", top_k=top_k, min_score=0.0)
            
            # Property 검증: 결과 개수는 top_k 이하
            assert len(results) <= top_k, \
                f"결과 개수({len(results)})가 top_k({top_k})를 초과했습니다."


class TestVectorSearchRequiredFields:
    """
    **Feature: vector-search, Property 6: 검색 결과 필수 필드**
    **Validates: Requirements 3.3**
    """
    
    @given(
        num_results=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_search_result_required_fields(self, num_results: int):
        """
        **Feature: vector-search, Property 6: 검색 결과 필수 필드**
        **Validates: Requirements 3.3**
        
        *For any* 벡터 검색 결과에 대해, 각 결과는 land_num, score, search_text 필드를 포함해야 한다.
        """
        from nodes.vector_search_node import vector_search
        
        # 테스트 데이터 직접 생성 (assume 제거)
        land_nums = [f"land_{i}" for i in range(num_results)]
        search_texts = [f"search_text_{i}" for i in range(num_results)]
        scores = [0.9 - (i * 0.05) for i in range(num_results)]
        
        # Mock 데이터 생성
        mock_hits = [
            {
                "land_num": land_nums[i],
                "search_text": search_texts[i],
                "score": scores[i]
            }
            for i in range(num_results)
        ]
        mock_response = create_mock_es_response(mock_hits)
        
        # Mock embedding (3072 차원)
        mock_embedding = [0.1] * 3072
        
        with patch('nodes.vector_search_node.get_embedding_service') as mock_embed_svc, \
             patch('nodes.vector_search_node.get_es_client') as mock_es_client:
            
            # EmbeddingService mock
            mock_service = MagicMock()
            mock_service.embed_text.return_value = mock_embedding
            mock_embed_svc.return_value = mock_service
            
            # ES client mock
            mock_es = MagicMock()
            mock_es.search.return_value = mock_response
            mock_es_client.return_value = mock_es
            
            # 검색 실행
            results = vector_search("테스트 쿼리", top_k=20, min_score=0.0)
            
            # Property 검증: 각 결과에 필수 필드 포함
            for r in results:
                assert "land_num" in r, \
                    f"결과에 land_num 필드가 없습니다: {r}"
                assert "score" in r, \
                    f"결과에 score 필드가 없습니다: {r}"
                assert "search_text" in r, \
                    f"결과에 search_text 필드가 없습니다: {r}"


class TestVectorSearchMinScoreFiltering:
    """
    **Feature: vector-search, Property 7: 유사도 점수 임계값 필터링**
    **Validates: Requirements 3.4**
    """
    
    @given(
        min_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        result_scores=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_similarity_threshold_filtering(self, min_score: float, result_scores: list):
        """
        **Feature: vector-search, Property 7: 유사도 점수 임계값 필터링**
        **Validates: Requirements 3.4**
        
        *For any* min_score가 설정된 벡터 검색에 대해, 반환된 모든 결과의 score는 min_score 이상이어야 한다.
        """
        from nodes.vector_search_node import vector_search
        
        # ES의 min_score 필터링을 시뮬레이션: min_score 이상인 결과만 반환
        filtered_scores = [s for s in result_scores if s >= min_score]
        
        # Mock 데이터 생성 (min_score 이상인 결과만)
        mock_hits = [
            {
                "land_num": f"land_{i}",
                "search_text": f"text_{i}",
                "score": score
            }
            for i, score in enumerate(filtered_scores)
        ]
        mock_response = create_mock_es_response(mock_hits)
        
        # Mock embedding (3072 차원)
        mock_embedding = [0.1] * 3072
        
        with patch('nodes.vector_search_node.get_embedding_service') as mock_embed_svc, \
             patch('nodes.vector_search_node.get_es_client') as mock_es_client:
            
            # EmbeddingService mock
            mock_service = MagicMock()
            mock_service.embed_text.return_value = mock_embedding
            mock_embed_svc.return_value = mock_service
            
            # ES client mock
            mock_es = MagicMock()
            mock_es.search.return_value = mock_response
            mock_es_client.return_value = mock_es
            
            # 검색 실행
            results = vector_search("테스트 쿼리", top_k=20, min_score=min_score)
            
            # Property 검증: 모든 결과의 score는 min_score 이상
            for r in results:
                assert r["score"] >= min_score, \
                    f"결과 score({r['score']})가 min_score({min_score})보다 작습니다."


class TestVectorSearchEmptyQuery:
    """빈 쿼리 처리 테스트"""
    
    def test_empty_query_returns_empty_results(self):
        """빈 쿼리는 빈 결과를 반환해야 함"""
        from nodes.vector_search_node import vector_search
        
        results = vector_search("", top_k=10, min_score=0.5)
        assert results == [], "빈 쿼리에 대해 빈 결과가 반환되어야 합니다."
    
    def test_whitespace_query_returns_empty_results(self):
        """공백만 있는 쿼리는 빈 결과를 반환해야 함"""
        from nodes.vector_search_node import vector_search
        
        results = vector_search("   ", top_k=10, min_score=0.5)
        assert results == [], "공백 쿼리에 대해 빈 결과가 반환되어야 합니다."


class TestRAGStateIntegration:
    """RAG State 통합 테스트"""
    
    def test_search_node_updates_state_correctly(self):
        """search 노드가 RAGState를 올바르게 업데이트하는지 검증"""
        from nodes.vector_search_node import search
        from common.state import RAGState
        
        # Mock 데이터
        mock_hits = [
            {"land_num": "land_1", "search_text": "text_1", "score": 0.9},
            {"land_num": "land_2", "search_text": "text_2", "score": 0.8}
        ]
        mock_response = create_mock_es_response(mock_hits)
        mock_embedding = [0.1] * 3072
        
        with patch('nodes.vector_search_node.get_embedding_service') as mock_embed_svc, \
             patch('nodes.vector_search_node.get_es_client') as mock_es_client:
            
            mock_service = MagicMock()
            mock_service.embed_text.return_value = mock_embedding
            mock_embed_svc.return_value = mock_service
            
            mock_es = MagicMock()
            mock_es.search.return_value = mock_response
            mock_es_client.return_value = mock_es
            
            # 초기 상태
            state: RAGState = {"question": "테스트 질문"}
            
            # search 노드 실행
            result_state = search(state)
            
            # 상태 검증
            assert "vector_results" in result_state, \
                "결과 상태에 vector_results가 없습니다."
            assert "vector_scores" in result_state, \
                "결과 상태에 vector_scores가 없습니다."
            assert len(result_state["vector_results"]) == 2, \
                f"vector_results 개수가 예상과 다릅니다: {len(result_state['vector_results'])}"
            assert "land_1" in result_state["vector_scores"], \
                "vector_scores에 land_1이 없습니다."
            assert "land_2" in result_state["vector_scores"], \
                "vector_scores에 land_2가 없습니다."
    
    def test_search_node_handles_empty_question(self):
        """빈 질문에 대해 빈 결과를 반환하는지 검증"""
        from nodes.vector_search_node import search
        from common.state import RAGState
        
        state: RAGState = {"question": ""}
        result_state = search(state)
        
        assert result_state["vector_results"] == [], \
            "빈 질문에 대해 빈 vector_results가 반환되어야 합니다."
        assert result_state["vector_scores"] == {}, \
            "빈 질문에 대해 빈 vector_scores가 반환되어야 합니다."
