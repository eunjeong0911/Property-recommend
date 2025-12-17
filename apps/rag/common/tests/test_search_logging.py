"""
Property-based tests for RAG search logging module.

**Feature: search-logging-elasticsearch, Property 6: 검색 로그와 추천 결과 동기화**
**Validates: Requirements 6.4**
"""
import pytest
from hypothesis import given, strategies as st, settings
import string
import json

import sys
import os

# apps/rag 디렉토리를 path에 추가
rag_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.abspath(rag_path))


# PostgreSQL-safe text strategy (excludes null characters)
safe_chars = string.ascii_letters + string.digits + ' ' + '가나다라마바사아자차카타파하'
safe_text = st.text(alphabet=safe_chars, min_size=1, max_size=200)
safe_text_short = st.text(alphabet=safe_chars, min_size=1, max_size=50)
safe_text_id = st.text(alphabet=string.digits, min_size=1, max_size=10)


class TestSearchLogResultSynchronization:
    """
    Property 6: 검색 로그와 추천 결과 동기화
    
    *For any* RAG 파이프라인 실행 완료 시, UserSearchLog에 저장된 result_ids는 
    실제 반환된 추천 결과의 매물 ID 목록과 일치해야 한다.
    """
    
    @given(
        query=safe_text,
        result_ids=st.lists(safe_text_id, min_size=0, max_size=50),
        session_id=safe_text_short,
        duration=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=100)
    def test_log_result_ids_match_actual_results(
        self, 
        query: str, 
        result_ids: list, 
        session_id: str,
        duration: int
    ):
        """
        **Feature: search-logging-elasticsearch, Property 6: 검색 로그와 추천 결과 동기화**
        **Validates: Requirements 6.4**
        
        log_user_search_sync()로 저장된 result_ids가 입력된 result_ids와 
        정확히 일치하는지 검증합니다.
        """
        from unittest.mock import patch, MagicMock
        from common.search_logging import log_user_search_sync
        
        # Mock the database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]  # Return a mock log ID
        
        captured_params = {}
        
        def capture_execute(query, params):
            captured_params['query'] = query
            captured_params['params'] = params
        
        mock_cursor.execute.side_effect = capture_execute
        
        with patch('common.search_logging.PostgresPool.get_connection', return_value=mock_conn):
            with patch('common.search_logging.PostgresPool.return_connection'):
                log_id = log_user_search_sync(
                    query=query,
                    result_ids=result_ids,
                    filters={'test': True},
                    session_id=session_id,
                    search_duration_ms=duration,
                    search_type='rag'
                )
        
        # Verify the log was created
        assert log_id is not None, "Log should be created"
        
        # Verify the captured parameters
        assert 'params' in captured_params, "Execute should have been called with params"
        
        params = captured_params['params']
        # params order: (user_id, session_id, query, filters, result_ids, result_count, 
        #                search_duration_ms, search_type, created_at)
        
        stored_session_id = params[1]
        stored_query = params[2]
        stored_result_ids_json = params[4]
        stored_result_count = params[5]
        stored_duration = params[6]
        stored_search_type = params[7]
        
        # Parse the stored result_ids JSON
        stored_result_ids = json.loads(stored_result_ids_json)
        
        # Property: stored result_ids must match input result_ids exactly
        assert stored_result_ids == result_ids, (
            f"Stored result_ids {stored_result_ids} should match input {result_ids}"
        )
        
        # Property: result_count must match length of result_ids
        assert stored_result_count == len(result_ids), (
            f"Result count {stored_result_count} should match len(result_ids) {len(result_ids)}"
        )
        
        # Property: query must be stored exactly
        assert stored_query == query, (
            f"Stored query '{stored_query}' should match input '{query}'"
        )
        
        # Property: session_id must be stored (or 'anonymous' if None)
        assert stored_session_id == session_id, (
            f"Stored session_id '{stored_session_id}' should match input '{session_id}'"
        )
        
        # Property: duration must be stored exactly
        assert stored_duration == duration, (
            f"Stored duration {stored_duration} should match input {duration}"
        )
        
        # Property: search_type must be stored exactly
        assert stored_search_type == 'rag', (
            f"Stored search_type '{stored_search_type}' should be 'rag'"
        )
    
    @given(
        result_ids=st.lists(safe_text_id, min_size=1, max_size=30)
    )
    @settings(max_examples=50)
    def test_result_ids_order_preserved(self, result_ids: list):
        """
        **Feature: search-logging-elasticsearch, Property 6: 검색 로그와 추천 결과 동기화**
        **Validates: Requirements 6.4**
        
        result_ids의 순서가 저장 시 보존되는지 검증합니다.
        추천 결과의 순위가 중요하므로 순서 보존은 필수입니다.
        """
        from unittest.mock import patch, MagicMock
        from common.search_logging import log_user_search_sync
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]
        
        captured_result_ids = None
        
        def capture_execute(query, params):
            nonlocal captured_result_ids
            # result_ids is at index 4
            captured_result_ids = json.loads(params[4])
        
        mock_cursor.execute.side_effect = capture_execute
        
        with patch('common.search_logging.PostgresPool.get_connection', return_value=mock_conn):
            with patch('common.search_logging.PostgresPool.return_connection'):
                log_user_search_sync(
                    query="test query",
                    result_ids=result_ids
                )
        
        # Property: order must be preserved
        assert captured_result_ids == result_ids, (
            f"Order not preserved: expected {result_ids}, got {captured_result_ids}"
        )
    
    @given(
        filters=st.fixed_dictionaries({
            'price_conditions': st.fixed_dictionaries({
                'deposit_max': st.integers(min_value=0, max_value=100000),
                'rent_max': st.integers(min_value=0, max_value=1000)
            }),
            'use_cache': st.booleans()
        })
    )
    @settings(max_examples=50)
    def test_filters_stored_correctly(self, filters: dict):
        """
        **Feature: search-logging-elasticsearch, Property 6: 검색 로그와 추천 결과 동기화**
        **Validates: Requirements 6.4**
        
        필터 조건이 정확하게 저장되는지 검증합니다.
        """
        from unittest.mock import patch, MagicMock
        from common.search_logging import log_user_search_sync
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]
        
        captured_filters = None
        
        def capture_execute(query, params):
            nonlocal captured_filters
            # filters is at index 3
            captured_filters = json.loads(params[3])
        
        mock_cursor.execute.side_effect = capture_execute
        
        with patch('common.search_logging.PostgresPool.get_connection', return_value=mock_conn):
            with patch('common.search_logging.PostgresPool.return_connection'):
                log_user_search_sync(
                    query="test query",
                    result_ids=["1", "2", "3"],
                    filters=filters
                )
        
        # Property: filters must be stored exactly
        assert captured_filters == filters, (
            f"Filters not stored correctly: expected {filters}, got {captured_filters}"
        )
    
    @given(
        search_type=st.sampled_from(['rag', 'es', 'hybrid'])
    )
    @settings(max_examples=10)
    def test_search_type_stored_correctly(self, search_type: str):
        """
        **Feature: search-logging-elasticsearch, Property 6: 검색 로그와 추천 결과 동기화**
        **Validates: Requirements 6.4**
        
        검색 유형이 정확하게 저장되는지 검증합니다.
        """
        from unittest.mock import patch, MagicMock
        from common.search_logging import log_user_search_sync
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]
        
        captured_search_type = None
        
        def capture_execute(query, params):
            nonlocal captured_search_type
            # search_type is at index 7
            captured_search_type = params[7]
        
        mock_cursor.execute.side_effect = capture_execute
        
        with patch('common.search_logging.PostgresPool.get_connection', return_value=mock_conn):
            with patch('common.search_logging.PostgresPool.return_connection'):
                log_user_search_sync(
                    query="test query",
                    result_ids=["1"],
                    search_type=search_type
                )
        
        # Property: search_type must be stored exactly
        assert captured_search_type == search_type, (
            f"Search type not stored correctly: expected {search_type}, got {captured_search_type}"
        )
