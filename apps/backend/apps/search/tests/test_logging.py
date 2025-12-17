"""
Property-based tests for search logging module.

**Feature: search-logging-elasticsearch, Property 1: 검색 로그 저장 완전성**
**Validates: Requirements 1.1, 1.2**
"""
import pytest
from hypothesis import given, strategies as st, settings
import string

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from apps.search.logging import log_user_search_sync
from apps.search.models import UserSearchLog


# PostgreSQL-safe text strategy (excludes null characters which PostgreSQL JSON doesn't support)
# Using printable characters + Korean characters for realistic test data
safe_chars = string.ascii_letters + string.digits + string.punctuation + ' ' + '가나다라마바사아자차카타파하'
safe_text = st.text(alphabet=safe_chars, min_size=1, max_size=200)
safe_text_short = st.text(alphabet=safe_chars, min_size=1, max_size=50)
safe_text_id = st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20)


class TestSearchLogCompleteness:
    """
    Property 1: 검색 로그 저장 완전성
    
    *For any* 검색 요청에 대해, log_user_search() 호출 시 query, result_ids, 
    filters, session_id, search_duration_ms 필드가 모두 UserSearchLog 레코드에 
    저장되어야 한다.
    """
    
    @pytest.fixture(autouse=True)
    def setup_db(self, db):
        """Enable database access for all tests"""
        pass
    
    @given(
        query=safe_text,
        result_ids=st.lists(safe_text_id, max_size=50),
        duration=st.integers(min_value=0, max_value=10000),
        session_id=safe_text_short
    )
    @settings(max_examples=100)
    def test_search_log_stores_all_required_fields(
        self, 
        query: str, 
        result_ids: list, 
        duration: int,
        session_id: str
    ):
        """
        **Feature: search-logging-elasticsearch, Property 1: 검색 로그 저장 완전성**
        **Validates: Requirements 1.1, 1.2**
        
        모든 필수 필드가 저장되는지 검증합니다.
        """
        filters = {'price_min': 1000, 'price_max': 5000}
        
        # 동기 버전으로 로그 저장
        log = log_user_search_sync(
            query=query,
            result_ids=result_ids,
            filters=filters,
            session_id=session_id,
            search_duration_ms=duration,
            search_type='rag'
        )
        
        # 로그가 생성되었는지 확인
        assert log is not None, "Log should be created"
        
        # 모든 필수 필드가 저장되었는지 확인
        assert log.query == query, f"Query mismatch: expected '{query}', got '{log.query}'"
        assert log.result_ids == result_ids, f"Result IDs mismatch"
        assert log.filters == filters, f"Filters mismatch"
        assert log.session_id == session_id, f"Session ID mismatch"
        assert log.search_duration_ms == duration, f"Duration mismatch"
        assert log.result_count == len(result_ids), f"Result count mismatch"
        assert log.search_type == 'rag', f"Search type mismatch"
        
        # 타임스탬프가 설정되었는지 확인
        assert log.created_at is not None, "Created at should be set"
    
    @given(
        query=safe_text,
        result_ids=st.lists(safe_text_id, max_size=30)
    )
    @settings(max_examples=100)
    def test_search_log_with_empty_filters(self, query: str, result_ids: list):
        """
        **Feature: search-logging-elasticsearch, Property 1: 검색 로그 저장 완전성**
        **Validates: Requirements 1.1, 1.2**
        
        필터가 없는 경우에도 로그가 정상적으로 저장되는지 검증합니다.
        """
        log = log_user_search_sync(
            query=query,
            result_ids=result_ids,
            filters=None,  # 필터 없음
            session_id=None,  # 세션 ID 없음
            search_duration_ms=0
        )
        
        assert log is not None, "Log should be created even without filters"
        assert log.query == query
        assert log.result_ids == result_ids
        assert log.filters == {}, "Empty filters should default to empty dict"
        assert log.session_id == 'anonymous', "Missing session_id should default to 'anonymous'"
    
    @given(
        search_type=st.sampled_from(['rag', 'es', 'hybrid'])
    )
    @settings(max_examples=10)
    def test_search_log_search_type_choices(self, search_type: str):
        """
        **Feature: search-logging-elasticsearch, Property 1: 검색 로그 저장 완전성**
        **Validates: Requirements 1.1, 1.2**
        
        모든 검색 유형이 정상적으로 저장되는지 검증합니다.
        """
        log = log_user_search_sync(
            query="test query",
            result_ids=["id1", "id2"],
            search_type=search_type
        )
        
        assert log is not None
        assert log.search_type == search_type
    
    @given(
        result_ids=st.lists(safe_text_id, min_size=0, max_size=100)
    )
    @settings(max_examples=50)
    def test_result_count_matches_result_ids_length(self, result_ids: list):
        """
        **Feature: search-logging-elasticsearch, Property 1: 검색 로그 저장 완전성**
        **Validates: Requirements 1.1, 1.2**
        
        result_count가 result_ids의 길이와 일치하는지 검증합니다.
        """
        log = log_user_search_sync(
            query="test query",
            result_ids=result_ids
        )
        
        assert log is not None
        assert log.result_count == len(result_ids), (
            f"Result count ({log.result_count}) should match "
            f"result_ids length ({len(result_ids)})"
        )
