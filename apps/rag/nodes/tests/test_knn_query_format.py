"""
k-NN Query Format Property-Based Tests

**Feature: aws-deployment-prep, Property 3: k-NN query format validity**
**Validates: Requirements 2.2**

Tests that k-NN queries are generated in valid Elasticsearch 8.17 k-NN DSL format.
"""
import pytest
from hypothesis import given, strategies as st, settings
from typing import List, Dict, Any
import json

import sys
import os

# apps/rag 디렉토리를 path에 추가
rag_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.abspath(rag_path))


def validate_knn_query_structure(query: Dict[str, Any]) -> bool:
    """
    Elasticsearch 8.17 k-NN 쿼리 구조 검증
    
    유효한 k-NN 쿼리는 다음 구조를 가져야 함:
    {
        "knn": {
            "<field_name>": {
                "vector": [...],
                "k": <int>
            }
        }
    }
    """
    if "knn" not in query:
        return False
    
    knn_content = query["knn"]
    if not isinstance(knn_content, dict):
        return False
    
    # knn 내부에 최소 하나의 필드가 있어야 함
    if len(knn_content) == 0:
        return False
    
    # 각 필드에 대해 vector와 k가 있어야 함
    for field_name, field_config in knn_content.items():
        if not isinstance(field_config, dict):
            return False
        if "vector" not in field_config:
            return False
        if "k" not in field_config:
            return False
        
        # vector는 리스트여야 함
        if not isinstance(field_config["vector"], list):
            return False
        
        # k는 양의 정수여야 함
        if not isinstance(field_config["k"], int) or field_config["k"] <= 0:
            return False
    
    return True


class TestKnnQueryFormatValidity:
    """
    **Feature: aws-deployment-prep, Property 3: k-NN query format validity**
    **Validates: Requirements 2.2**
    
    *For any* vector similarity search request, the generated Elasticsearch 8.17 query 
    SHALL use `knn` query type with valid `vector` and `k` parameters in 
    Elasticsearch 8.17 k-NN DSL format.
    """
    
    @given(
        k=st.integers(min_value=1, max_value=100),
        vector_dim=st.integers(min_value=1, max_value=3072)
    )
    @settings(max_examples=100)
    def test_build_knn_query_format_validity(self, k: int, vector_dim: int):
        """
        **Feature: aws-deployment-prep, Property 3: k-NN query format validity**
        **Validates: Requirements 2.2**
        
        *For any* k value and vector dimension, build_knn_query SHALL produce
        a valid Elasticsearch 8.17 k-NN DSL query with 'knn' type, 'vector', and 'k' parameters.
        """
        from nodes.vector_search_node import build_knn_query
        
        # 임의의 벡터 생성
        query_vector = [0.1] * vector_dim
        
        # k-NN 쿼리 빌드
        query = build_knn_query(query_vector, k=k)
        
        # Property 검증: 쿼리가 유효한 Elasticsearch 8.17 k-NN DSL 형식인지 확인
        assert validate_knn_query_structure(query), \
            f"생성된 쿼리가 유효한 Elasticsearch 8.17 k-NN DSL 형식이 아닙니다: {json.dumps(query, indent=2)}"
        
        # 추가 검증: vector와 k 값이 올바른지 확인
        knn_config = query["knn"]["embedding"]
        assert knn_config["vector"] == query_vector, \
            "쿼리의 vector가 입력 벡터와 일치하지 않습니다."
        assert knn_config["k"] == k, \
            f"쿼리의 k({knn_config['k']})가 입력 k({k})와 일치하지 않습니다."
    
    @given(
        k=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100)
    def test_build_knn_query_with_3072_dim_vector(self, k: int):
        """
        **Feature: aws-deployment-prep, Property 3: k-NN query format validity**
        **Validates: Requirements 2.2**
        
        *For any* k value with 3072-dimensional embedding vector (text-embedding-3-large),
        build_knn_query SHALL produce a valid Elasticsearch 8.17 k-NN DSL query.
        """
        from nodes.vector_search_node import build_knn_query
        
        # 3072차원 벡터 (text-embedding-3-large 출력 차원)
        query_vector = [0.01 * (i % 100) for i in range(3072)]
        
        # k-NN 쿼리 빌드
        query = build_knn_query(query_vector, k=k)
        
        # Property 검증
        assert validate_knn_query_structure(query), \
            f"3072차원 벡터에 대한 쿼리가 유효하지 않습니다: {json.dumps(query, indent=2)}"
        
        # 벡터 차원 검증
        assert len(query["knn"]["embedding"]["vector"]) == 3072, \
            "쿼리 벡터의 차원이 3072가 아닙니다."
    
    @given(
        k=st.integers(min_value=1, max_value=100),
        vector_values=st.lists(
            st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=10,
            max_size=100
        )
    )
    @settings(max_examples=100)
    def test_knn_query_preserves_vector_values(self, k: int, vector_values: List[float]):
        """
        **Feature: aws-deployment-prep, Property 3: k-NN query format validity**
        **Validates: Requirements 2.2**
        
        *For any* input vector values, the generated k-NN query SHALL preserve
        the exact vector values without modification.
        """
        from nodes.vector_search_node import build_knn_query
        
        # k-NN 쿼리 빌드
        query = build_knn_query(vector_values, k=k)
        
        # Property 검증: 벡터 값이 정확히 보존되는지 확인
        result_vector = query["knn"]["embedding"]["vector"]
        assert result_vector == vector_values, \
            "쿼리에서 벡터 값이 변경되었습니다."
    
    def test_knn_query_is_json_serializable(self):
        """k-NN 쿼리가 JSON 직렬화 가능한지 확인"""
        from nodes.vector_search_node import build_knn_query
        
        query_vector = [0.1] * 3072
        query = build_knn_query(query_vector, k=20)
        
        # JSON 직렬화 시도
        try:
            json_str = json.dumps(query)
            parsed = json.loads(json_str)
            assert parsed == query, "JSON 직렬화/역직렬화 후 쿼리가 변경되었습니다."
        except (TypeError, ValueError) as e:
            pytest.fail(f"k-NN 쿼리가 JSON 직렬화 불가능합니다: {e}")


class TestEsSearchNodeKnnQuery:
    """
    ES Search Node의 k-NN 쿼리 빌드 함수 테스트
    """
    
    @given(
        k=st.integers(min_value=1, max_value=100),
        vector_dim=st.integers(min_value=1, max_value=3072)
    )
    @settings(max_examples=100)
    def test_es_search_node_build_knn_query(self, k: int, vector_dim: int):
        """
        **Feature: aws-deployment-prep, Property 3: k-NN query format validity**
        **Validates: Requirements 2.2**
        
        *For any* k value and vector dimension, es_search_node.build_knn_query 
        SHALL produce a valid Elasticsearch 8.17 k-NN DSL query.
        """
        from nodes.es_search_node import build_knn_query
        
        query_vector = [0.1] * vector_dim
        query = build_knn_query(query_vector, k=k)
        
        # Property 검증
        assert validate_knn_query_structure(query), \
            f"es_search_node의 쿼리가 유효하지 않습니다: {json.dumps(query, indent=2)}"
