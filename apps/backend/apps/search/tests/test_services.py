"""
Property-based tests for ES search services module.

**Feature: search-logging-elasticsearch, Property 3: ES 쿼리 빌더 정확성**
**Validates: Requirements 5.1, 5.4**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
import string

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from apps.search.services import build_es_query


# Safe text strategies for testing
safe_chars = string.ascii_letters + string.digits + ' ' + '가나다라마바사아자차카타파하'
safe_keyword = st.text(alphabet=safe_chars, min_size=1, max_size=50)
safe_tag = st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=30)
safe_id = st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20)


class TestESQueryBuilderAccuracy:
    """
    Property 3: ES 쿼리 빌더 정확성
    
    *For any* 검색 조건 조합(키워드, 가격 범위, 위치, 후보 ID)에 대해, 
    build_es_query()가 생성하는 ES 쿼리는 bool 쿼리 구조를 따르며 
    모든 조건이 올바르게 반영되어야 한다.
    """
    
    @given(
        keyword=st.one_of(st.none(), safe_keyword),
        min_deposit=st.one_of(st.none(), st.integers(min_value=0, max_value=50000)),
        max_deposit=st.one_of(st.none(), st.integers(min_value=0, max_value=100000)),
        candidate_ids=st.one_of(st.none(), st.lists(safe_id, min_size=1, max_size=20))
    )
    @settings(max_examples=100)
    def test_query_has_bool_structure(
        self,
        keyword,
        min_deposit,
        max_deposit,
        candidate_ids
    ):
        """
        **Feature: search-logging-elasticsearch, Property 3: ES 쿼리 빌더 정확성**
        **Validates: Requirements 5.1, 5.4**
        
        생성된 쿼리가 항상 bool 쿼리 구조를 따르는지 검증합니다.
        """
        query = build_es_query(
            keyword=keyword,
            min_deposit=min_deposit,
            max_deposit=max_deposit,
            candidate_ids=candidate_ids
        )
        
        # bool 쿼리 구조 확인
        assert "bool" in query, "Query must have 'bool' key"
        assert "must" in query["bool"], "Bool query must have 'must' key"
        assert "filter" in query["bool"], "Bool query must have 'filter' key"
        assert "should" in query["bool"], "Bool query must have 'should' key"
        
        # 각 섹션이 리스트인지 확인
        assert isinstance(query["bool"]["must"], list), "'must' must be a list"
        assert isinstance(query["bool"]["filter"], list), "'filter' must be a list"
        assert isinstance(query["bool"]["should"], list), "'should' must be a list"
    
    @given(keyword=safe_keyword)
    @settings(max_examples=100)
    def test_keyword_added_to_must_clause(self, keyword):
        """
        **Feature: search-logging-elasticsearch, Property 3: ES 쿼리 빌더 정확성**
        **Validates: Requirements 5.1, 5.4**
        
        키워드가 제공되면 must 절에 match 쿼리가 추가되는지 검증합니다.
        """
        query = build_es_query(keyword=keyword)
        
        # must 절에 match 쿼리가 있어야 함
        must_clauses = query["bool"]["must"]
        assert len(must_clauses) == 1, "Should have exactly one must clause for keyword"
        
        match_clause = must_clauses[0]
        assert "match" in match_clause, "Must clause should contain 'match'"
        assert "search_text" in match_clause["match"], "Match should target 'search_text' field"
        assert match_clause["match"]["search_text"]["query"] == keyword, "Keyword should match"
        assert match_clause["match"]["search_text"]["analyzer"] == "nori_analyzer", "Should use nori analyzer"
    
    @given(
        min_deposit=st.integers(min_value=0, max_value=50000),
        max_deposit=st.integers(min_value=50001, max_value=100000)
    )
    @settings(max_examples=100)
    def test_deposit_range_added_to_filter(self, min_deposit, max_deposit):
        """
        **Feature: search-logging-elasticsearch, Property 3: ES 쿼리 빌더 정확성**
        **Validates: Requirements 5.1, 5.4**
        
        보증금 범위가 filter 절에 range 쿼리로 추가되는지 검증합니다.
        """
        # Ensure min < max for valid range
        assume(min_deposit < max_deposit)
        
        query = build_es_query(min_deposit=min_deposit, max_deposit=max_deposit)
        
        # filter 절에 range 쿼리가 있어야 함
        filter_clauses = query["bool"]["filter"]
        assert len(filter_clauses) == 1, "Should have exactly one filter clause for deposit range"
        
        range_clause = filter_clauses[0]
        assert "range" in range_clause, "Filter clause should contain 'range'"
        assert "deposit" in range_clause["range"], "Range should target 'deposit' field"
        assert range_clause["range"]["deposit"]["gte"] == min_deposit, "Min deposit should match"
        assert range_clause["range"]["deposit"]["lte"] == max_deposit, "Max deposit should match"
    
    @given(style_tags=st.lists(safe_tag, min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_style_tags_added_to_filter(self, style_tags):
        """
        **Feature: search-logging-elasticsearch, Property 3: ES 쿼리 빌더 정확성**
        **Validates: Requirements 5.1, 5.4**
        
        스타일 태그가 filter 절에 terms 쿼리로 추가되는지 검증합니다.
        """
        query = build_es_query(style_tags=style_tags)
        
        # filter 절에 terms 쿼리가 있어야 함
        filter_clauses = query["bool"]["filter"]
        assert len(filter_clauses) == 1, "Should have exactly one filter clause for style tags"
        
        terms_clause = filter_clauses[0]
        assert "terms" in terms_clause, "Filter clause should contain 'terms'"
        assert "style_tags" in terms_clause["terms"], "Terms should target 'style_tags' field"
        assert terms_clause["terms"]["style_tags"] == style_tags, "Style tags should match"
    
    @given(candidate_ids=st.lists(safe_id, min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_candidate_ids_added_to_filter(self, candidate_ids):
        """
        **Feature: search-logging-elasticsearch, Property 3: ES 쿼리 빌더 정확성**
        **Validates: Requirements 5.1, 5.4**
        
        후보 ID가 filter 절에 terms 쿼리로 추가되는지 검증합니다.
        """
        query = build_es_query(candidate_ids=candidate_ids)
        
        # filter 절에 terms 쿼리가 있어야 함
        filter_clauses = query["bool"]["filter"]
        assert len(filter_clauses) == 1, "Should have exactly one filter clause for candidate IDs"
        
        terms_clause = filter_clauses[0]
        assert "terms" in terms_clause, "Filter clause should contain 'terms'"
        assert "land_num" in terms_clause["terms"], "Terms should target 'land_num' field"
        assert terms_clause["terms"]["land_num"] == candidate_ids, "Candidate IDs should match"
    
    @given(
        lat=st.floats(min_value=33.0, max_value=43.0, allow_nan=False, allow_infinity=False),
        lng=st.floats(min_value=124.0, max_value=132.0, allow_nan=False, allow_infinity=False),
        radius=st.sampled_from(["500m", "1km", "2km", "5km"])
    )
    @settings(max_examples=100)
    def test_location_added_to_filter(self, lat, lng, radius):
        """
        **Feature: search-logging-elasticsearch, Property 3: ES 쿼리 빌더 정확성**
        **Validates: Requirements 5.1, 5.4**
        
        위치 정보가 filter 절에 geo_distance 쿼리로 추가되는지 검증합니다.
        """
        location = {"lat": lat, "lng": lng, "radius": radius}
        query = build_es_query(location=location)
        
        # filter 절에 geo_distance 쿼리가 있어야 함
        filter_clauses = query["bool"]["filter"]
        assert len(filter_clauses) == 1, "Should have exactly one filter clause for location"
        
        geo_clause = filter_clauses[0]
        assert "geo_distance" in geo_clause, "Filter clause should contain 'geo_distance'"
        assert geo_clause["geo_distance"]["distance"] == radius, "Radius should match"
        assert geo_clause["geo_distance"]["location"]["lat"] == lat, "Latitude should match"
        assert geo_clause["geo_distance"]["location"]["lon"] == lng, "Longitude should match"
    
    def test_empty_query_returns_valid_bool_structure(self):
        """
        **Feature: search-logging-elasticsearch, Property 3: ES 쿼리 빌더 정확성**
        **Validates: Requirements 5.1, 5.4**
        
        조건이 없어도 유효한 bool 쿼리 구조를 반환하는지 검증합니다.
        """
        query = build_es_query()
        
        assert "bool" in query
        assert query["bool"]["must"] == []
        assert query["bool"]["filter"] == []
        assert query["bool"]["should"] == []
    
    @given(
        keyword=safe_keyword,
        style_tags=st.lists(safe_tag, min_size=1, max_size=3),
        min_deposit=st.integers(min_value=0, max_value=50000),
        candidate_ids=st.lists(safe_id, min_size=1, max_size=10)
    )
    @settings(max_examples=100)
    def test_multiple_conditions_combined_correctly(
        self,
        keyword,
        style_tags,
        min_deposit,
        candidate_ids
    ):
        """
        **Feature: search-logging-elasticsearch, Property 3: ES 쿼리 빌더 정확성**
        **Validates: Requirements 5.1, 5.4**
        
        여러 조건이 올바르게 조합되는지 검증합니다.
        """
        query = build_es_query(
            keyword=keyword,
            style_tags=style_tags,
            min_deposit=min_deposit,
            candidate_ids=candidate_ids
        )
        
        # must 절에 키워드 검색이 있어야 함
        assert len(query["bool"]["must"]) == 1, "Should have keyword in must"
        assert "match" in query["bool"]["must"][0]
        
        # filter 절에 3개의 조건이 있어야 함 (style_tags, deposit, candidate_ids)
        assert len(query["bool"]["filter"]) == 3, "Should have 3 filter clauses"
        
        # 각 필터 타입 확인
        filter_types = []
        for clause in query["bool"]["filter"]:
            if "terms" in clause:
                if "style_tags" in clause["terms"]:
                    filter_types.append("style_tags")
                elif "land_num" in clause["terms"]:
                    filter_types.append("candidate_ids")
            elif "range" in clause:
                filter_types.append("deposit_range")
        
        assert "style_tags" in filter_types, "Should have style_tags filter"
        assert "candidate_ids" in filter_types, "Should have candidate_ids filter"
        assert "deposit_range" in filter_types, "Should have deposit_range filter"
