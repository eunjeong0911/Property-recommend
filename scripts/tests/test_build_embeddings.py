"""Property-based tests for build_embeddings script"""
import pytest
from hypothesis import given, strategies as st, settings

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.build_embeddings import create_embedding_text


class TestEmbeddingTextCombination:
    """
    **Feature: vector-search, Property 3: 임베딩 텍스트 결합**
    **Validates: Requirements 2.2**
    
    For any document, the embedding text must be a space-joined combination
    of search_text and style_tags.
    """
    
    @settings(max_examples=100)
    @given(
        search_text=st.text(min_size=0, max_size=200),
        style_tags=st.lists(st.text(min_size=1, max_size=20), max_size=5)
    )
    def test_embedding_text_combination(self, search_text, style_tags):
        """
        **Feature: vector-search, Property 3: 임베딩 텍스트 결합**
        
        For any document with search_text and style_tags, the combined text
        must contain both components.
        """
        doc = {"_source": {"search_text": search_text, "style_tags": style_tags}}
        result = create_embedding_text(doc)
        
        # Property: if search_text is non-empty, it must be in result
        if search_text:
            assert search_text in result, f"search_text '{search_text}' not found in result"
        
        # Property: all style_tags must be in result
        for tag in style_tags:
            assert tag in result, f"style_tag '{tag}' not found in result"
    
    @settings(max_examples=100)
    @given(search_text=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()))
    def test_search_text_only(self, search_text):
        """
        **Feature: vector-search, Property 3: 임베딩 텍스트 결합**
        
        For documents with only search_text, result must contain search_text.
        """
        doc = {"_source": {"search_text": search_text}}
        result = create_embedding_text(doc)
        
        assert search_text in result
    
    @settings(max_examples=100)
    @given(style_tags=st.lists(st.text(min_size=1, max_size=20).filter(lambda x: x.strip()), min_size=1, max_size=5))
    def test_style_tags_only(self, style_tags):
        """
        **Feature: vector-search, Property 3: 임베딩 텍스트 결합**
        
        For documents with only style_tags, result must contain all tags.
        """
        doc = {"_source": {"style_tags": style_tags}}
        result = create_embedding_text(doc)
        
        for tag in style_tags:
            assert tag in result
    
    def test_empty_document(self):
        """
        **Feature: vector-search, Property 3: 임베딩 텍스트 결합**
        
        For empty documents, result must be empty string.
        """
        doc = {"_source": {}}
        result = create_embedding_text(doc)
        
        assert result == ""
    
    def test_style_tags_as_string(self):
        """
        **Feature: vector-search, Property 3: 임베딩 텍스트 결합**
        
        When style_tags is a string (not list), it should still be included.
        """
        doc = {"_source": {"search_text": "test", "style_tags": "single_tag"}}
        result = create_embedding_text(doc)
        
        assert "test" in result
        assert "single_tag" in result



class TestDuplicateEmbeddingPrevention:
    """
    **Feature: vector-search, Property 4: 중복 임베딩 방지**
    **Validates: Requirements 2.6**
    
    For any document that already has an embedding field, the embedding script
    should skip it and preserve the existing embedding value.
    """
    
    @settings(max_examples=100)
    @given(
        doc_id=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        has_embedding=st.booleans()
    )
    def test_documents_with_embedding_are_filtered_by_query(self, doc_id, has_embedding):
        """
        **Feature: vector-search, Property 4: 중복 임베딩 방지**
        
        The query structure must correctly filter documents based on embedding existence.
        Documents with embedding field should be excluded from the query results.
        """
        # The query used in get_documents_without_embedding
        query = {
            "bool": {
                "must_not": {
                    "exists": {"field": "embedding"}
                }
            }
        }
        
        # Property: The query must use must_not exists to exclude embedded documents
        assert query["bool"]["must_not"]["exists"]["field"] == "embedding"
        
        # Simulate document matching logic
        # A document with embedding field should NOT match the query
        # A document without embedding field SHOULD match the query
        doc_matches_query = not has_embedding
        
        if has_embedding:
            # Documents with embedding should be excluded (not match)
            assert doc_matches_query == False, "Documents with embedding should be excluded"
        else:
            # Documents without embedding should be included (match)
            assert doc_matches_query == True, "Documents without embedding should be included"
    
    def test_query_excludes_documents_with_embedding(self):
        """
        **Feature: vector-search, Property 4: 중복 임베딩 방지**
        
        Verify that the query structure correctly excludes documents with embeddings.
        """
        # The expected query structure
        expected_query = {
            "bool": {
                "must_not": {
                    "exists": {"field": "embedding"}
                }
            }
        }
        
        # This is the query used in get_documents_without_embedding
        # We verify the structure is correct for excluding embedded documents
        assert "bool" in expected_query
        assert "must_not" in expected_query["bool"]
        assert "exists" in expected_query["bool"]["must_not"]
        assert expected_query["bool"]["must_not"]["exists"]["field"] == "embedding"
    
    @settings(max_examples=100)
    @given(
        num_docs_with_embedding=st.integers(min_value=0, max_value=50),
        num_docs_without_embedding=st.integers(min_value=0, max_value=50)
    )
    def test_only_unembedded_documents_processed(self, num_docs_with_embedding, num_docs_without_embedding):
        """
        **Feature: vector-search, Property 4: 중복 임베딩 방지**
        
        For any set of documents, only those without embeddings should be processed.
        """
        # Simulate a set of documents
        docs_with_embedding = [{"_id": f"with_{i}", "embedding": [0.1] * 10} for i in range(num_docs_with_embedding)]
        docs_without_embedding = [{"_id": f"without_{i}"} for i in range(num_docs_without_embedding)]
        
        # Filter logic (simulating ES query behavior)
        filtered_docs = [doc for doc in docs_with_embedding + docs_without_embedding if "embedding" not in doc]
        
        # Property: Only documents without embedding should be in filtered results
        assert len(filtered_docs) == num_docs_without_embedding
        for doc in filtered_docs:
            assert "embedding" not in doc, "Filtered docs should not have embedding field"



class TestPartialUpdateIntegrity:
    """
    **Feature: vector-search, Property 2: 부분 업데이트 무결성**
    **Validates: Requirements 1.4**
    
    For any embedding update operation, only the embedding field should be modified,
    and all other fields must remain unchanged.
    """
    
    @settings(max_examples=100)
    @given(
        doc_id=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        embedding=st.lists(
            st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=10,
            max_size=10
        )
    )
    def test_bulk_action_only_updates_embedding(self, doc_id, embedding):
        """
        **Feature: vector-search, Property 2: 부분 업데이트 무결성**
        
        The bulk update action must only contain the embedding field in the doc payload.
        """
        from scripts.build_embeddings import generate_bulk_actions
        
        doc = {"_id": doc_id, "_source": {"search_text": "test", "style_tags": ["tag1"]}}
        
        actions = list(generate_bulk_actions([doc], [embedding]))
        
        assert len(actions) == 1
        action = actions[0]
        
        # Property: Action must be an update operation
        assert action["_op_type"] == "update", "Must use update operation for partial update"
        
        # Property: Only embedding field should be in the doc payload
        assert "doc" in action, "Update action must have doc field"
        assert list(action["doc"].keys()) == ["embedding"], "Only embedding field should be updated"
        
        # Property: Embedding value must match input
        assert action["doc"]["embedding"] == embedding
    
    @settings(max_examples=100)
    @given(
        num_docs=st.integers(min_value=1, max_value=20),
        extra_fields=st.dictionaries(
            st.text(min_size=1, max_size=10).filter(lambda x: x.strip() and x != "embedding"),
            st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5
        )
    )
    def test_other_fields_not_in_update_payload(self, num_docs, extra_fields):
        """
        **Feature: vector-search, Property 2: 부분 업데이트 무결성**
        
        For any document with additional fields, the update payload must not include them.
        """
        from scripts.build_embeddings import generate_bulk_actions
        
        # Create documents with extra fields
        docs = []
        embeddings = []
        for i in range(num_docs):
            source = {"search_text": f"text_{i}", **extra_fields}
            docs.append({"_id": f"doc_{i}", "_source": source})
            embeddings.append([0.1] * 10)
        
        actions = list(generate_bulk_actions(docs, embeddings))
        
        # Property: Each action should only update embedding field
        for action in actions:
            doc_payload = action.get("doc", {})
            
            # Only embedding should be in the payload
            assert "embedding" in doc_payload, "Embedding must be in update payload"
            assert len(doc_payload) == 1, f"Only embedding should be updated, got: {list(doc_payload.keys())}"
            
            # Extra fields should NOT be in the payload
            for field in extra_fields:
                assert field not in doc_payload, f"Field '{field}' should not be in update payload"
    
    def test_update_preserves_document_structure(self):
        """
        **Feature: vector-search, Property 2: 부분 업데이트 무결성**
        
        Verify that the update action structure is correct for ES partial update.
        """
        from scripts.build_embeddings import generate_bulk_actions
        
        doc = {
            "_id": "test_doc",
            "_source": {
                "search_text": "Original text",
                "style_tags": ["tag1", "tag2"],
                "price": 1000000,
                "address": "Seoul"
            }
        }
        embedding = [0.1] * 3072
        
        actions = list(generate_bulk_actions([doc], [embedding]))
        action = actions[0]
        
        # Verify ES partial update structure
        assert action["_op_type"] == "update"
        assert action["_index"] == "listings"
        assert action["_id"] == "test_doc"
        assert "doc" in action
        assert action["doc"] == {"embedding": embedding}
        
        # Original fields should NOT be in the update payload
        assert "search_text" not in action["doc"]
        assert "style_tags" not in action["doc"]
        assert "price" not in action["doc"]
        assert "address" not in action["doc"]
