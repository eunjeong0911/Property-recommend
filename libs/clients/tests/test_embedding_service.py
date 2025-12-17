"""Property-based tests for EmbeddingService"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from libs.clients.embedding_service import EmbeddingService


class TestEmbeddingDimensionConsistency:
    """
    **Feature: vector-search, Property 1: 임베딩 차원 일관성**
    **Validates: Requirements 2.3, 3.1**
    
    For any generated embedding, the vector dimension must always be 3072.
    """
    
    @settings(max_examples=100)
    @given(text=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()))
    def test_embedding_dimension_consistency(self, text):
        """
        **Feature: vector-search, Property 1: 임베딩 차원 일관성**
        
        For any non-empty text input, the embedding dimension must be 3072.
        """
        # Create a mock embedding with exactly 3072 dimensions
        mock_embedding = [0.1] * EmbeddingService.DIMENSIONS
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]
        
        with patch.object(EmbeddingService, 'client', new_callable=lambda: MagicMock()) as mock_client:
            mock_client.embeddings.create.return_value = mock_response
            
            service = EmbeddingService.get_instance()
            # Temporarily replace client
            original_client = service._client
            service._client = mock_client
            
            try:
                embedding = service.embed_text(text)
                
                # Property: embedding dimension must always be 3072
                assert len(embedding) == 3072, f"Expected 3072 dimensions, got {len(embedding)}"
                assert len(embedding) == EmbeddingService.DIMENSIONS
            finally:
                service._client = original_client


class TestSingletonInstanceIdentity:
    """
    **Feature: vector-search, Property 11: 싱글톤 인스턴스 동일성**
    **Validates: Requirements 5.1, 5.2**
    
    For any EmbeddingService.get_instance() call, the returned instance must always be the same.
    """
    
    def test_singleton_instance_identity(self):
        """
        **Feature: vector-search, Property 11: 싱글톤 인스턴스 동일성**
        
        Multiple calls to get_instance() and constructor must return the same instance.
        """
        # Reset singleton for clean test
        EmbeddingService._instance = None
        
        instance1 = EmbeddingService.get_instance()
        instance2 = EmbeddingService.get_instance()
        instance3 = EmbeddingService()
        
        # Property: all instances must be identical
        assert instance1 is instance2, "get_instance() calls should return same instance"
        assert instance2 is instance3, "Constructor should return same instance as get_instance()"
        assert instance1 is instance3, "All instances must be identical"
    
    @settings(max_examples=100)
    @given(n_calls=st.integers(min_value=2, max_value=50))
    def test_singleton_multiple_calls(self, n_calls):
        """
        **Feature: vector-search, Property 11: 싱글톤 인스턴스 동일성**
        
        For any number of get_instance() calls, all returned instances must be identical.
        """
        # Reset singleton for clean test
        EmbeddingService._instance = None
        
        instances = [EmbeddingService.get_instance() for _ in range(n_calls)]
        
        # Property: all instances must be the same object
        first_instance = instances[0]
        for i, instance in enumerate(instances[1:], start=2):
            assert instance is first_instance, f"Instance {i} differs from first instance"
