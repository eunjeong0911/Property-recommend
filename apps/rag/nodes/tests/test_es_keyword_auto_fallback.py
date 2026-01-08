"""
ES Keyword Search Node 자동 폴백 메커니즘 Property 테스트

**Feature: chatbot-landlist-integration-fix, Property 3: Zero Result Auto-Fallback**
**Validates: Requirements 1.3**

스타일 필터가 적용된 검색에서 결과가 0개인 경우,
시스템은 스타일 필터를 제외한 재검색을 자동으로 실행해야 한다.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock

import sys
import os

# apps/rag 디렉토리를 path에 추가
rag_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.abspath(rag_path))


# =============================================================================
# 테스트용 헬퍼 함수 및 Mock 클래스
# =============================================================================

def create_mock_state(
    hard_filters: Optional[Dict[str, Any]] = None,
    soft_filters: Optional[List[str]] = None,
    unmapped_styles: Optional[List[str]] = None,
    graph_results: Optional[List[Dict]] = None,
    style_filter_removed: bool = False,
    removed_filters: Optional[List[str]] = None
) -> Dict[str, Any]:
    """테스트용 RAGState 생성"""
    return {
        "question": "테스트 질문",
        "session_id": "test-session",
        "hard_filters": hard_filters or {},
        "soft_filters": soft_filters or [],
        "unmapped_styles": unmapped_styles or [],
        "graph_results": graph_results or [],
        "style_filter_removed": style_filter_removed,
        "removed_filters": removed_filters or [],
        "collected_conditions": {},
    }


def create_mock_es_response(hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Mock ES 응답 생성"""
    return {
        "hits": {
            "hits": [
                {
                    "_id": hit.get("id", f"id_{i}"),
                    "_score": hit.get("score", 1.0),
                    "_source": {
                        "land_num": hit.get("id", f"id_{i}"),
                        "address": hit.get("address", "테스트 주소"),
                        "search_text": hit.get("search_text", "테스트 검색 텍스트"),
                        "deposit": hit.get("deposit", 1000),
                        "monthly_rent": hit.get("monthly_rent", 50),
                        "building_type": hit.get("building_type", "원룸"),
                        "deal_type": hit.get("deal_type", "월세"),
                    }
                }
                for i, hit in enumerate(hits)
            ],
            "total": {"value": len(hits)}
        }
    }


# =============================================================================
# Property-Based Tests
# =============================================================================

class TestZeroResultAutoFallback:
    """
    자동 폴백 메커니즘 Property 테스트
    
    **Feature: chatbot-landlist-integration-fix, Property 3: Zero Result Auto-Fallback**
    **Validates: Requirements 1.3**
    """
    
    @given(
        soft_filters=st.lists(
            st.sampled_from(["채광좋음", "깔끔함", "넓은공간", "아늑함", "모던함", "럭셔리함"]),
            min_size=1,
            max_size=3,
            unique=True
        ),
        unmapped_styles=st.lists(
            st.text(alphabet="가나다라마바사아자차카타파하", min_size=2, max_size=10),
            min_size=0,
            max_size=2
        ),
        fallback_result_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)  # deadline=None to avoid flaky test failures
    def test_style_filter_triggers_fallback_on_zero_results(
        self,
        soft_filters: List[str],
        unmapped_styles: List[str],
        fallback_result_count: int
    ):
        """
        **Feature: chatbot-landlist-integration-fix, Property 3: Zero Result Auto-Fallback**
        **Validates: Requirements 1.3**
        
        *For any* 스타일 필터가 적용된 검색에서 결과가 0개인 경우,
        시스템은 스타일 필터를 제외한 재검색을 자동으로 실행해야 한다.
        """
        # 스타일 필터가 있어야 함
        assume(len(soft_filters) > 0 or len(unmapped_styles) > 0)
        
        # 테스트 상태 생성
        state = create_mock_state(
            hard_filters={"location": "홍대입구", "deal_type": "월세"},
            soft_filters=soft_filters,
            unmapped_styles=unmapped_styles,
            style_filter_removed=False
        )
        
        # 첫 번째 검색: 0개 결과 (스타일 필터 적용)
        first_response = create_mock_es_response([])
        
        # 두 번째 검색: fallback_result_count개 결과 (스타일 필터 제외)
        fallback_hits = [{"id": f"land_{i}", "score": 1.0} for i in range(fallback_result_count)]
        fallback_response = create_mock_es_response(fallback_hits)
        
        # Mock ES 클라이언트
        mock_es = MagicMock()
        mock_es.search.side_effect = [first_response, fallback_response]
        
        with patch('elasticsearch.Elasticsearch', return_value=mock_es):
            # es_keyword_search_node 함수 임포트 및 실행
            from graphs.listing_rag_graph import es_keyword_search_node
            
            result_state = es_keyword_search_node(state)
            
            # Property 검증 1: style_filter_removed 플래그가 True로 설정되어야 함
            assert result_state.get("style_filter_removed") == True, \
                "스타일 필터 제거 후 style_filter_removed 플래그가 True여야 합니다."
            
            # Property 검증 2: 폴백 검색 결과가 반환되어야 함
            graph_results = result_state.get("graph_results", [])
            assert len(graph_results) == fallback_result_count, \
                f"폴백 검색 결과 수가 예상과 다릅니다. 예상: {fallback_result_count}, 실제: {len(graph_results)}"
            
            # Property 검증 3: 원본 스타일 필터가 저장되어야 함
            assert result_state.get("original_soft_filters") == soft_filters, \
                "원본 soft_filters가 저장되어야 합니다."
    
    @given(
        soft_filters=st.lists(
            st.sampled_from(["채광좋음", "깔끔함", "넓은공간"]),
            min_size=1,
            max_size=2,
            unique=True
        ),
        initial_result_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_no_fallback_when_results_exist(
        self,
        soft_filters: List[str],
        initial_result_count: int
    ):
        """
        **Feature: chatbot-landlist-integration-fix, Property 3: Zero Result Auto-Fallback**
        **Validates: Requirements 1.3**
        
        *For any* 스타일 필터가 적용된 검색에서 결과가 1개 이상인 경우,
        시스템은 폴백 검색을 실행하지 않아야 한다.
        """
        assume(initial_result_count > 0)
        
        # 테스트 상태 생성
        state = create_mock_state(
            hard_filters={"location": "홍대입구", "deal_type": "월세"},
            soft_filters=soft_filters,
            style_filter_removed=False
        )
        
        # 검색 결과가 있는 경우
        hits = [{"id": f"land_{i}", "score": 1.0} for i in range(initial_result_count)]
        response = create_mock_es_response(hits)
        
        # Mock ES 클라이언트
        mock_es = MagicMock()
        mock_es.search.return_value = response
        
        with patch('elasticsearch.Elasticsearch', return_value=mock_es):
            from graphs.listing_rag_graph import es_keyword_search_node
            
            result_state = es_keyword_search_node(state)
            
            # Property 검증: style_filter_removed가 False여야 함 (폴백 미실행)
            assert result_state.get("style_filter_removed", False) == False, \
                "결과가 있으면 폴백이 실행되지 않아야 합니다."
            
            # Property 검증: ES search가 1번만 호출되어야 함
            assert mock_es.search.call_count == 1, \
                f"결과가 있으면 ES search가 1번만 호출되어야 합니다. 실제: {mock_es.search.call_count}번"
    
    @given(
        hard_filters=st.fixed_dictionaries({
            "location": st.text(alphabet="가나다라마바사", min_size=2, max_size=10),
            "deal_type": st.sampled_from(["월세", "전세"]),
        })
    )
    @settings(max_examples=100)
    def test_no_fallback_without_style_filters(
        self,
        hard_filters: Dict[str, str]
    ):
        """
        **Feature: chatbot-landlist-integration-fix, Property 3: Zero Result Auto-Fallback**
        **Validates: Requirements 1.3**
        
        *For any* 스타일 필터가 없는 검색에서 결과가 0개인 경우,
        시스템은 폴백 검색을 실행하지 않아야 한다 (스타일 필터가 없으므로).
        """
        # 스타일 필터 없이 상태 생성
        state = create_mock_state(
            hard_filters=hard_filters,
            soft_filters=[],  # 스타일 필터 없음
            unmapped_styles=[],  # 매핑되지 않은 스타일도 없음
            style_filter_removed=False
        )
        
        # 검색 결과 0개
        response = create_mock_es_response([])
        
        # Mock ES 클라이언트
        mock_es = MagicMock()
        mock_es.search.return_value = response
        
        with patch('elasticsearch.Elasticsearch', return_value=mock_es):
            from graphs.listing_rag_graph import es_keyword_search_node
            
            result_state = es_keyword_search_node(state)
            
            # Property 검증: style_filter_removed가 False여야 함
            assert result_state.get("style_filter_removed", False) == False, \
                "스타일 필터가 없으면 폴백이 실행되지 않아야 합니다."
            
            # Property 검증: ES search가 1번만 호출되어야 함
            assert mock_es.search.call_count == 1, \
                f"스타일 필터가 없으면 ES search가 1번만 호출되어야 합니다. 실제: {mock_es.search.call_count}번"
    
    @given(
        soft_filters=st.lists(
            st.sampled_from(["채광좋음", "깔끔함", "넓은공간"]),
            min_size=1,
            max_size=2,
            unique=True
        )
    )
    @settings(max_examples=100)
    def test_no_double_fallback(
        self,
        soft_filters: List[str]
    ):
        """
        **Feature: chatbot-landlist-integration-fix, Property 3: Zero Result Auto-Fallback**
        **Validates: Requirements 1.3**
        
        *For any* 이미 폴백이 실행된 상태에서는 다시 폴백이 실행되지 않아야 한다.
        """
        # 이미 폴백이 실행된 상태
        state = create_mock_state(
            hard_filters={"location": "홍대입구", "deal_type": "월세"},
            soft_filters=soft_filters,
            style_filter_removed=True  # 이미 폴백 실행됨
        )
        
        # 검색 결과 0개
        response = create_mock_es_response([])
        
        # Mock ES 클라이언트
        mock_es = MagicMock()
        mock_es.search.return_value = response
        
        with patch('elasticsearch.Elasticsearch', return_value=mock_es):
            from graphs.listing_rag_graph import es_keyword_search_node
            
            result_state = es_keyword_search_node(state)
            
            # Property 검증: ES search가 1번만 호출되어야 함 (이중 폴백 방지)
            assert mock_es.search.call_count == 1, \
                f"이미 폴백이 실행된 상태에서는 추가 폴백이 실행되지 않아야 합니다. 실제: {mock_es.search.call_count}번"


class TestLowResultFilterSuggestion:
    """
    저결과 필터 제거 제안 Property 테스트
    
    **Feature: chatbot-landlist-integration-fix, Property 4: Low Result Filter Suggestion**
    **Validates: Requirements 2.1, 7.2**
    """
    
    @given(
        result_count=st.integers(min_value=0, max_value=3),
        soft_filters=st.lists(
            st.sampled_from(["채광좋음", "깔끔함", "넓은공간"]),
            min_size=1,
            max_size=2,
            unique=True
        )
    )
    @settings(max_examples=100)
    def test_filter_removal_suggested_for_low_results(
        self,
        result_count: int,
        soft_filters: List[str]
    ):
        """
        **Feature: chatbot-landlist-integration-fix, Property 4: Low Result Filter Suggestion**
        **Validates: Requirements 2.1, 7.2**
        
        *For any* 검색 결과가 3개 이하인 경우, 시스템은 제거 가능한 필터 목록과 함께
        제안 메시지를 생성해야 한다.
        """
        # 테스트 상태 생성
        state = create_mock_state(
            hard_filters={"location": "홍대입구", "deal_type": "월세", "direction": "남향"},
            soft_filters=soft_filters,
            style_filter_removed=False
        )
        
        # 저결과 응답 생성
        hits = [{"id": f"land_{i}", "score": 1.0} for i in range(result_count)]
        response = create_mock_es_response(hits)
        
        # Mock ES 클라이언트
        mock_es = MagicMock()
        mock_es.search.return_value = response
        
        with patch('elasticsearch.Elasticsearch', return_value=mock_es):
            from graphs.listing_rag_graph import es_keyword_search_node
            
            result_state = es_keyword_search_node(state)
            
            # Property 검증 1: suggest_filter_removal이 True여야 함
            assert result_state.get("suggest_filter_removal") == True, \
                f"결과가 {result_count}개일 때 필터 제거 제안이 활성화되어야 합니다."
            
            # Property 검증 2: low_result_filters가 비어있지 않아야 함
            low_result_filters = result_state.get("low_result_filters", [])
            assert len(low_result_filters) > 0, \
                "제거 가능한 필터 목록이 비어있으면 안 됩니다."
            
            # Property 검증 3: filter_removal_message가 생성되어야 함
            filter_removal_message = result_state.get("filter_removal_message", "")
            assert len(filter_removal_message) > 0, \
                "필터 제거 제안 메시지가 생성되어야 합니다."
    
    @given(
        result_count=st.integers(min_value=4, max_value=20)
    )
    @settings(max_examples=100)
    def test_no_filter_removal_suggested_for_sufficient_results(
        self,
        result_count: int
    ):
        """
        **Feature: chatbot-landlist-integration-fix, Property 4: Low Result Filter Suggestion**
        **Validates: Requirements 2.1**
        
        *For any* 검색 결과가 4개 이상인 경우, 시스템은 필터 제거를 제안하지 않아야 한다.
        """
        # 테스트 상태 생성
        state = create_mock_state(
            hard_filters={"location": "홍대입구", "deal_type": "월세", "direction": "남향"},
            soft_filters=["채광좋음"],
            style_filter_removed=False
        )
        
        # 충분한 결과 응답 생성
        hits = [{"id": f"land_{i}", "score": 1.0} for i in range(result_count)]
        response = create_mock_es_response(hits)
        
        # Mock ES 클라이언트
        mock_es = MagicMock()
        mock_es.search.return_value = response
        
        with patch('elasticsearch.Elasticsearch', return_value=mock_es):
            from graphs.listing_rag_graph import es_keyword_search_node
            
            result_state = es_keyword_search_node(state)
            
            # Property 검증: suggest_filter_removal이 False여야 함
            assert result_state.get("suggest_filter_removal") == False, \
                f"결과가 {result_count}개일 때 필터 제거 제안이 비활성화되어야 합니다."
    
    @given(
        removed_filters=st.lists(
            st.sampled_from(["style", "direction", "max_rent", "max_deposit"]),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=100)
    def test_already_removed_filters_not_suggested(
        self,
        removed_filters: List[str]
    ):
        """
        **Feature: chatbot-landlist-integration-fix, Property 7: No Duplicate Filter Suggestion**
        **Validates: Requirements 2.4, 2.5**
        
        *For any* 필터 제거 제안 시퀀스에서, 이미 제거된 필터는 다시 제안되지 않아야 한다.
        """
        # 테스트 상태 생성 (이미 일부 필터가 제거된 상태)
        state = create_mock_state(
            hard_filters={
                "location": "홍대입구",
                "deal_type": "월세",
                "direction": "남향",
                "max_rent": 50,
                "max_deposit": 1000
            },
            soft_filters=["채광좋음"],
            removed_filters=removed_filters,  # 이미 제거된 필터
            style_filter_removed=False
        )
        
        # 저결과 응답 생성
        response = create_mock_es_response([{"id": "land_1", "score": 1.0}])
        
        # Mock ES 클라이언트
        mock_es = MagicMock()
        mock_es.search.return_value = response
        
        with patch('elasticsearch.Elasticsearch', return_value=mock_es):
            from graphs.listing_rag_graph import es_keyword_search_node
            
            result_state = es_keyword_search_node(state)
            
            # Property 검증: 제안된 필터 중 이미 제거된 필터가 없어야 함
            low_result_filters = result_state.get("low_result_filters", [])
            suggested_filter_keys = [f[0] for f in low_result_filters]
            
            for removed in removed_filters:
                assert removed not in suggested_filter_keys, \
                    f"이미 제거된 필터 '{removed}'가 다시 제안되었습니다."

