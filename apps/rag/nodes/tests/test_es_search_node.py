"""
ES Search Node 하이브리드 검색 재정렬 일관성 테스트

**Feature: search-logging-elasticsearch, Property 5: 하이브리드 검색 재정렬 일관성**
**Validates: Requirements 6.2, 6.3**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume

import sys
import os

# apps/rag 디렉토리를 path에 추가
rag_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.abspath(rag_path))

from nodes.es_search_node import combine_scores, build_hybrid_query, combine_with_neo4j


class TestHybridSearchReranking:
    """하이브리드 검색 재정렬 일관성 Property 테스트"""
    
    @given(
        neo4j_ids=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
            min_size=1,
            max_size=20,
            unique=True
        ),
        neo4j_scores=st.lists(
            st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=20
        ),
        es_subset_ratio=st.floats(min_value=0.1, max_value=1.0),
        es_scores_values=st.lists(
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_hybrid_reranking_excludes_non_es_results(
        self,
        neo4j_ids: list,
        neo4j_scores: list,
        es_subset_ratio: float,
        es_scores_values: list
    ):
        """
        **Feature: search-logging-elasticsearch, Property 5: 하이브리드 검색 재정렬 일관성**
        **Validates: Requirements 6.2, 6.3**
        
        *For any* Neo4j 후보 ID 목록과 ES 검색 결과에 대해, 최종 결과는 두 점수를 조합한 
        순위로 정렬되어야 하며, Neo4j 후보에 없는 ID는 결과에 포함되지 않아야 한다.
        """
        # 입력 데이터 정규화
        assume(len(neo4j_ids) > 0)
        assume(len(neo4j_scores) >= len(neo4j_ids))
        
        # Neo4j 결과 생성
        neo4j_results = []
        for i, prop_id in enumerate(neo4j_ids):
            score = neo4j_scores[i % len(neo4j_scores)]
            neo4j_results.append({
                'id': prop_id,
                'total_score': score
            })
        
        # ES 결과 생성 (Neo4j 결과의 일부만 포함)
        es_subset_size = max(1, int(len(neo4j_ids) * es_subset_ratio))
        es_ids = neo4j_ids[:es_subset_size]
        
        es_scores = {}
        for i, prop_id in enumerate(es_ids):
            score = es_scores_values[i % len(es_scores_values)]
            es_scores[prop_id] = score
        
        # combine_scores 실행
        combined_results = combine_scores(neo4j_results, es_scores)
        
        # Property 검증 1: 결과에 포함된 모든 ID는 ES 결과에 있어야 함
        for result in combined_results:
            result_id = str(result.get('id', ''))
            assert result_id in es_scores, \
                f"결과 ID '{result_id}'가 ES 결과에 없습니다. ES에 없는 ID는 제외되어야 합니다."
        
        # Property 검증 2: ES 결과에 없는 Neo4j ID는 최종 결과에 포함되지 않아야 함
        result_ids = {str(r.get('id', '')) for r in combined_results}
        for neo4j_result in neo4j_results:
            neo4j_id = str(neo4j_result.get('id', ''))
            if neo4j_id not in es_scores:
                assert neo4j_id not in result_ids, \
                    f"ES 결과에 없는 ID '{neo4j_id}'가 최종 결과에 포함되었습니다."
        
        # Property 검증 3: 결과는 combined_score 기준 내림차순 정렬되어야 함
        if len(combined_results) > 1:
            for i in range(len(combined_results) - 1):
                current_score = combined_results[i].get('combined_score', 0)
                next_score = combined_results[i + 1].get('combined_score', 0)
                assert current_score >= next_score, \
                    f"결과가 점수 순으로 정렬되지 않았습니다: {current_score} < {next_score}"
    
    @given(
        neo4j_ids=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
            min_size=1,
            max_size=10,
            unique=True
        ),
        neo4j_scores=st.lists(
            st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10
        ),
        es_scores_values=st.lists(
            st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_combined_score_uses_both_sources(
        self,
        neo4j_ids: list,
        neo4j_scores: list,
        es_scores_values: list
    ):
        """
        **Feature: search-logging-elasticsearch, Property 5: 하이브리드 검색 재정렬 일관성**
        **Validates: Requirements 6.3**
        
        *For any* Neo4j 점수와 ES 점수에 대해, 조합된 점수는 두 점수를 모두 반영해야 한다.
        """
        assume(len(neo4j_ids) > 0)
        assume(len(neo4j_scores) >= len(neo4j_ids))
        assume(len(es_scores_values) >= len(neo4j_ids))
        
        # Neo4j 결과 생성
        neo4j_results = []
        for i, prop_id in enumerate(neo4j_ids):
            score = neo4j_scores[i % len(neo4j_scores)]
            neo4j_results.append({
                'id': prop_id,
                'total_score': score
            })
        
        # ES 결과 생성 (모든 Neo4j ID 포함)
        es_scores = {}
        for i, prop_id in enumerate(neo4j_ids):
            score = es_scores_values[i % len(es_scores_values)]
            es_scores[prop_id] = score
        
        # combine_scores 실행
        combined_results = combine_scores(neo4j_results, es_scores)
        
        # Property 검증: 각 결과에 정규화된 점수가 포함되어야 함
        for result in combined_results:
            assert 'combined_score' in result, \
                "결과에 combined_score가 없습니다."
            assert 'neo4j_score_normalized' in result, \
                "결과에 neo4j_score_normalized가 없습니다."
            assert 'es_score_normalized' in result, \
                "결과에 es_score_normalized가 없습니다."
            
            # 정규화된 점수는 0~1 범위여야 함
            neo4j_norm = result['neo4j_score_normalized']
            es_norm = result['es_score_normalized']
            combined = result['combined_score']
            
            assert 0 <= neo4j_norm <= 1, \
                f"neo4j_score_normalized가 0~1 범위를 벗어났습니다: {neo4j_norm}"
            assert 0 <= es_norm <= 1, \
                f"es_score_normalized가 0~1 범위를 벗어났습니다: {es_norm}"
            assert 0 <= combined <= 1, \
                f"combined_score가 0~1 범위를 벗어났습니다: {combined}"


class TestESQueryBuilder:
    """ES 쿼리 빌더 테스트"""
    
    @given(
        keyword=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        candidate_ids=st.one_of(
            st.none(),
            st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10)
        ),
        min_deposit=st.one_of(st.none(), st.integers(min_value=0, max_value=50000)),
        max_deposit=st.one_of(st.none(), st.integers(min_value=0, max_value=100000))
    )
    @settings(max_examples=100)
    def test_query_builder_structure(
        self,
        keyword,
        candidate_ids,
        min_deposit,
        max_deposit
    ):
        """
        ES 쿼리 빌더가 올바른 bool 쿼리 구조를 생성하는지 검증
        """
        query = build_hybrid_query(
            keyword=keyword,
            candidate_ids=candidate_ids,
            min_deposit=min_deposit,
            max_deposit=max_deposit
        )
        
        # 기본 구조 검증
        assert 'bool' in query, "쿼리에 bool 키가 없습니다."
        assert 'must' in query['bool'], "bool 쿼리에 must가 없습니다."
        assert 'filter' in query['bool'], "bool 쿼리에 filter가 없습니다."
        assert 'should' in query['bool'], "bool 쿼리에 should가 없습니다."
        
        # 키워드가 있으면 must에 match 쿼리가 있어야 함
        if keyword:
            must_queries = query['bool']['must']
            has_match = any('match' in q for q in must_queries)
            assert has_match, "키워드가 있는데 match 쿼리가 없습니다."
        
        # candidate_ids가 있으면 filter에 terms 쿼리가 있어야 함
        if candidate_ids:
            filter_queries = query['bool']['filter']
            has_terms = any('terms' in q and 'land_num' in q.get('terms', {}) for q in filter_queries)
            assert has_terms, "candidate_ids가 있는데 terms 쿼리가 없습니다."
        
        # 가격 범위가 있으면 filter에 range 쿼리가 있어야 함
        if min_deposit is not None or max_deposit is not None:
            filter_queries = query['bool']['filter']
            has_range = any('range' in q and 'deposit' in q.get('range', {}) for q in filter_queries)
            assert has_range, "가격 범위가 있는데 range 쿼리가 없습니다."


class TestCombineScoresEdgeCases:
    """combine_scores 엣지 케이스 테스트"""
    
    def test_empty_neo4j_results(self):
        """Neo4j 결과가 비어있으면 빈 결과 반환"""
        result = combine_scores([], {'id1': 1.0})
        assert result == []
    
    def test_empty_es_scores(self):
        """ES 점수가 비어있으면 빈 결과 반환 (모든 ID가 제외됨)"""
        neo4j_results = [{'id': 'id1', 'total_score': 100}]
        result = combine_scores(neo4j_results, {})
        assert result == []
    
    def test_no_overlap(self):
        """Neo4j와 ES 결과가 겹치지 않으면 빈 결과 반환"""
        neo4j_results = [{'id': 'id1', 'total_score': 100}]
        es_scores = {'id2': 1.0}
        result = combine_scores(neo4j_results, es_scores)
        assert result == []
    
    def test_partial_overlap(self):
        """일부만 겹치면 겹치는 것만 반환"""
        neo4j_results = [
            {'id': 'id1', 'total_score': 100},
            {'id': 'id2', 'total_score': 200}
        ]
        es_scores = {'id1': 1.0, 'id3': 2.0}
        result = combine_scores(neo4j_results, es_scores)
        
        assert len(result) == 1
        assert result[0]['id'] == 'id1'


# =============================================================================
# Vector Search 하이브리드 검색 Property 테스트 (Requirements 4.2, 4.4, 4.5)
# =============================================================================

class TestCombineWithNeo4jProperties:
    """combine_with_neo4j 함수 Property 테스트"""
    
    @given(
        es_scores=st.dictionaries(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
            st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
            min_size=0,
            max_size=10
        ),
        neo4j_scores=st.dictionaries(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
            st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_hybrid_score_range(self, es_scores: dict, neo4j_scores: dict):
        """
        **Feature: vector-search, Property 8: 하이브리드 점수 범위**
        **Validates: Requirements 4.2**
        
        *For any* 하이브리드 검색 결과에 대해, 정규화된 최종 점수는 0과 1 사이여야 한다.
        """
        # ES 하이브리드 결과 생성
        hybrid_results = [{"land_num": k, "score": v, "search_text": "", "source": "hybrid"} 
                         for k, v in es_scores.items()]
        
        # combine_with_neo4j 실행
        combined = combine_with_neo4j(hybrid_results, neo4j_scores)
        
        # Property 검증: 모든 final_score는 0과 1 사이여야 함
        for r in combined:
            assert 0 <= r["final_score"] <= 1, \
                f"final_score가 0~1 범위를 벗어났습니다: {r['final_score']}"
    
    @given(
        es_ids=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
            unique=True,
            min_size=0,
            max_size=10
        ),
        neo4j_ids=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
            unique=True,
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_merge_completeness(self, es_ids: list, neo4j_ids: list):
        """
        **Feature: vector-search, Property 9: 결과 병합 완전성**
        **Validates: Requirements 4.4**
        
        *For any* Neo4j와 ES 하이브리드 검색 결과 병합에 대해, 
        두 소스의 모든 고유 land_num이 최종 결과에 포함되어야 한다.
        """
        # ES 하이브리드 결과 생성
        hybrid_results = [{"land_num": id, "score": 1.0, "search_text": "", "source": "hybrid"} 
                         for id in es_ids]
        
        # Neo4j 점수 생성
        neo4j_scores = {id: 0.5 for id in neo4j_ids}
        
        # combine_with_neo4j 실행
        combined = combine_with_neo4j(hybrid_results, neo4j_scores)
        combined_ids = {r["land_num"] for r in combined}
        
        # Property 검증: 모든 고유 ID가 결과에 포함되어야 함
        all_ids = set(es_ids) | set(neo4j_ids)
        assert combined_ids == all_ids, \
            f"병합 결과에 누락된 ID가 있습니다. 예상: {all_ids}, 실제: {combined_ids}"
    
    @given(
        es_scores=st.dictionaries(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
            st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_contribution_fields_present(self, es_scores: dict):
        """
        **Feature: vector-search, Property 10: 기여도 필드 포함**
        **Validates: Requirements 4.5**
        
        *For any* 병합된 검색 결과에 대해, 각 결과는 es_contribution과 neo4j_contribution 필드를 포함해야 한다.
        """
        # ES 하이브리드 결과 생성
        hybrid_results = [{"land_num": k, "score": v, "search_text": "", "source": "hybrid"} 
                         for k, v in es_scores.items()]
        
        # combine_with_neo4j 실행 (빈 Neo4j 점수)
        combined = combine_with_neo4j(hybrid_results, {})
        
        # Property 검증: 모든 결과에 기여도 필드가 있어야 함
        for r in combined:
            assert "es_contribution" in r, \
                f"결과에 es_contribution 필드가 없습니다: {r}"
            assert "neo4j_contribution" in r, \
                f"결과에 neo4j_contribution 필드가 없습니다: {r}"
