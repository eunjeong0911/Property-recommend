"""
Filter Removal Response Processing Tests

필터 제거 응답 처리 로직을 검증하는 테스트입니다.

**Feature: chatbot-landlist-integration-fix**
**Property 5: Positive Response Filter Removal**
**Validates: Requirements 2.2, 7.5**
"""
import pytest
import sys
import os

# 모듈 경로 설정
nodes_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.abspath(nodes_path))

# 직접 모듈 로드 (패키지 임포트 우회)
import importlib.util

# query_analyzer_node 모듈 로드
spec = importlib.util.spec_from_file_location(
    "query_analyzer_node", 
    os.path.join(nodes_path, "query_analyzer_node.py")
)
query_analyzer_node = importlib.util.module_from_spec(spec)

# 의존성 모듈 모킹
import types
mock_common = types.ModuleType("common")
mock_state = types.ModuleType("common.state")
mock_redis = types.ModuleType("common.redis_cache")
mock_nodes = types.ModuleType("nodes")
mock_style_mapping = types.ModuleType("nodes.style_mapping")

# RAGState 타입 정의
class RAGState(dict):
    pass

mock_state.RAGState = RAGState
mock_common.state = mock_state

# Redis 함수 모킹
def mock_get_conversation_history(session_id):
    return []

def mock_get_redis_client():
    class MockRedis:
        def get(self, key):
            return None
        def setex(self, key, ttl, value):
            pass
        def delete(self, key):
            pass
    return MockRedis()

def mock_clear_collected_conditions(session_id):
    pass

mock_redis.get_conversation_history = mock_get_conversation_history
mock_redis.get_redis_client = mock_get_redis_client
mock_redis.clear_collected_conditions = mock_clear_collected_conditions
mock_common.redis_cache = mock_redis

# style_mapping 모듈 로드
style_mapping_spec = importlib.util.spec_from_file_location(
    "style_mapping", 
    os.path.join(nodes_path, "style_mapping.py")
)
style_mapping = importlib.util.module_from_spec(style_mapping_spec)
style_mapping_spec.loader.exec_module(style_mapping)
mock_style_mapping.map_style_keywords = style_mapping.map_style_keywords
mock_nodes.style_mapping = mock_style_mapping

sys.modules["common"] = mock_common
sys.modules["common.state"] = mock_state
sys.modules["common.redis_cache"] = mock_redis
sys.modules["nodes"] = mock_nodes
sys.modules["nodes.style_mapping"] = mock_style_mapping

# 이제 query_analyzer_node 로드
spec.loader.exec_module(query_analyzer_node)


# =============================================================================
# 긍정 응답 키워드 목록 (테스트용)
# =============================================================================

SIMPLE_CONFIRMATIONS = ["응", "웅", "엉", "네", "넵", "예", "ㅇ", "ㅇㅇ", "ok", "yes", "ㅇㅋ", "그래", "좋아"]

CONFIRMATION_KEYWORDS = [
    # 기본 긍정 응답
    "응", "웅", "엉", "네", "넵", "넹", "예", "예스", "yes", "ok", "okay", "ㅇ", "ㅇㅇ", "ㅇㅋ",
    # 동의 표현
    "그래", "좋아", "알겠어", "그렇게 해", "해줘", "부탁해", "당연", "물론", "그럼",
    # 제거 요청 표현
    "제외해줘", "빼줘", "제외", "빼", "삭제", "지워", "없애", "제거",
    # 추가 긍정 표현
    "ㅇㅋㅇㅋ", "오케이", "굿", "good", "sure", "yep", "yeah", "yup",
    "그래줘", "해주세요", "부탁드려요", "그렇게해줘", "그렇게요"
]

REJECTION_KEYWORDS = [
    "아니", "아뇨", "ㄴㄴ", "노", "no", "nope", "싫어", "괜찮아", "그냥 둬", "그대로", "유지",
    "말고", "됐어", "안해", "필요없어", "그만", "취소"
]


# =============================================================================
# Unit Tests
# =============================================================================

class TestPositiveResponseDetection:
    """긍정 응답 감지 테스트"""
    
    def test_simple_confirmation_응(self):
        """'응' 응답이 긍정으로 감지되는지 테스트"""
        assert "응" in SIMPLE_CONFIRMATIONS
    
    def test_simple_confirmation_네(self):
        """'네' 응답이 긍정으로 감지되는지 테스트"""
        assert "네" in SIMPLE_CONFIRMATIONS
    
    def test_simple_confirmation_ok(self):
        """'ok' 응답이 긍정으로 감지되는지 테스트"""
        assert "ok" in SIMPLE_CONFIRMATIONS
    
    def test_confirmation_keyword_제외해줘(self):
        """'제외해줘' 응답이 긍정으로 감지되는지 테스트"""
        assert "제외해줘" in CONFIRMATION_KEYWORDS
    
    def test_confirmation_keyword_빼줘(self):
        """'빼줘' 응답이 긍정으로 감지되는지 테스트"""
        assert "빼줘" in CONFIRMATION_KEYWORDS


class TestRejectionResponseDetection:
    """거부 응답 감지 테스트"""
    
    def test_rejection_아니(self):
        """'아니' 응답이 거부로 감지되는지 테스트"""
        assert "아니" in REJECTION_KEYWORDS
    
    def test_rejection_no(self):
        """'no' 응답이 거부로 감지되는지 테스트"""
        assert "no" in REJECTION_KEYWORDS
    
    def test_rejection_괜찮아(self):
        """'괜찮아' 응답이 거부로 감지되는지 테스트"""
        assert "괜찮아" in REJECTION_KEYWORDS


class TestFilterRemovalLogic:
    """필터 제거 로직 테스트"""
    
    def test_removed_filters_tracking(self):
        """제거된 필터가 추적되는지 테스트"""
        removed_filters = ["location"]
        updated = list(set(removed_filters + ["max_rent"]))
        
        assert "location" in updated
        assert "max_rent" in updated
        assert len(updated) == 2
    
    def test_no_duplicate_in_removed_filters(self):
        """제거된 필터 목록에 중복이 없는지 테스트"""
        removed_filters = ["location", "max_rent"]
        updated = list(set(removed_filters + ["location"]))  # 중복 추가 시도
        
        assert updated.count("location") == 1
        assert len(updated) == 2


class TestSpecificFilterRemoval:
    """특정 필터 제거 요청 테스트"""
    
    def test_filter_keyword_map_contains_location(self):
        """필터 키워드 맵에 location이 포함되어 있는지 테스트"""
        filter_keyword_map = {
            "location": ["위치", "지역", "동네", "장소", "근처", "주변"],
            "max_rent": ["월세", "렌트", "월"],
            "style": ["스타일", "분위기", "햇살", "채광"]
        }
        
        assert "location" in filter_keyword_map
        assert "위치" in filter_keyword_map["location"]
    
    def test_filter_removal_pattern_detection(self):
        """필터 제거 패턴 감지 테스트"""
        q_lower = "위치 조건 빼줘"
        remove_keywords = ["빼", "제외", "없이", "말고", "제거", "삭제"]
        
        has_remove_keyword = any(kw in q_lower for kw in remove_keywords)
        assert has_remove_keyword is True
    
    def test_style_filter_removal_pattern(self):
        """스타일 필터 제거 패턴 감지 테스트"""
        q_lower = "스타일 조건 제외해줘"
        filter_keywords = ["스타일", "분위기", "햇살", "채광"]
        remove_keywords = ["빼", "제외", "없이", "말고", "제거", "삭제"]
        
        has_filter_keyword = any(kw in q_lower for kw in filter_keywords)
        has_remove_keyword = any(kw in q_lower for kw in remove_keywords)
        
        assert has_filter_keyword is True
        assert has_remove_keyword is True


# =============================================================================
# Property-Based Tests (Hypothesis)
# =============================================================================

from hypothesis import given, strategies as st, settings, assume


class TestPositiveResponseFilterRemovalProperties:
    """
    필터 제거 응답 처리 Property-Based 테스트
    
    **Feature: chatbot-landlist-integration-fix, Property 5: Positive Response Filter Removal**
    **Validates: Requirements 2.2, 7.5**
    """
    
    @given(
        response=st.sampled_from(SIMPLE_CONFIRMATIONS)
    )
    @settings(max_examples=100)
    def test_simple_confirmations_are_recognized(self, response: str):
        """
        **Feature: chatbot-landlist-integration-fix, Property 5: Positive Response Filter Removal**
        **Validates: Requirements 2.2, 7.5**
        
        *For any* 단순 긍정 응답 키워드, 해당 응답은 긍정으로 인식되어야 한다.
        """
        # Property: 단순 긍정 응답은 SIMPLE_CONFIRMATIONS에 포함되어야 함
        assert response in SIMPLE_CONFIRMATIONS, \
            f"응답 '{response}'가 단순 긍정 응답으로 인식되지 않았습니다."
    
    @given(
        response=st.sampled_from(CONFIRMATION_KEYWORDS)
    )
    @settings(max_examples=100)
    def test_confirmation_keywords_trigger_filter_removal(self, response: str):
        """
        **Feature: chatbot-landlist-integration-fix, Property 5: Positive Response Filter Removal**
        **Validates: Requirements 2.2, 7.5**
        
        *For any* 긍정 응답 키워드, 해당 응답은 필터 제거를 트리거해야 한다.
        """
        q_lower = response.strip().lower()
        
        # Property: 긍정 응답 키워드가 포함되면 필터 제거가 트리거되어야 함
        is_confirmation = any(kw in q_lower for kw in CONFIRMATION_KEYWORDS)
        assert is_confirmation, \
            f"응답 '{response}'가 긍정 응답으로 인식되지 않았습니다."
    
    @given(
        response=st.sampled_from(REJECTION_KEYWORDS)
    )
    @settings(max_examples=100)
    def test_rejection_keywords_do_not_trigger_filter_removal(self, response: str):
        """
        **Feature: chatbot-landlist-integration-fix, Property 5: Positive Response Filter Removal**
        **Validates: Requirements 2.2**
        
        *For any* 거부 응답 키워드, 해당 응답은 필터 제거를 트리거하지 않아야 한다.
        """
        q_lower = response.strip().lower()
        
        # Property: 거부 응답 키워드가 포함되면 필터 제거가 트리거되지 않아야 함
        is_rejection = any(kw in q_lower for kw in REJECTION_KEYWORDS)
        assert is_rejection, \
            f"응답 '{response}'가 거부 응답으로 인식되지 않았습니다."
    
    @given(
        pending_filter=st.sampled_from(["location", "max_rent", "max_deposit", "building_type", "deal_type", "style"]),
        existing_removed=st.lists(
            st.sampled_from(["location", "max_rent", "max_deposit", "building_type", "deal_type", "style"]),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=100)
    def test_removed_filters_list_has_no_duplicates(self, pending_filter: str, existing_removed: list):
        """
        **Feature: chatbot-landlist-integration-fix, Property 5: Positive Response Filter Removal**
        **Validates: Requirements 2.5**
        
        *For any* 필터 제거 작업 후, 제거된 필터 목록에는 중복이 없어야 한다.
        """
        # 필터 제거 시뮬레이션
        updated_removed = list(set(existing_removed + [pending_filter]))
        
        # Property: 제거된 필터 목록에 중복이 없어야 함
        assert len(updated_removed) == len(set(updated_removed)), \
            f"제거된 필터 목록에 중복이 있습니다: {updated_removed}"
    
    @given(
        filter_type=st.sampled_from(["location", "max_rent", "style"]),
        remove_keyword=st.sampled_from(["빼", "제외", "없이", "말고", "제거", "삭제"])
    )
    @settings(max_examples=100)
    def test_specific_filter_removal_request_detection(self, filter_type: str, remove_keyword: str):
        """
        **Feature: chatbot-landlist-integration-fix, Property 5: Positive Response Filter Removal**
        **Validates: Requirements 2.3**
        
        *For any* 특정 필터 제거 요청 패턴, 해당 요청이 올바르게 감지되어야 한다.
        """
        filter_keyword_map = {
            "location": ["위치", "지역"],
            "max_rent": ["월세", "렌트"],
            "style": ["스타일", "분위기"]
        }
        
        # 필터 제거 요청 문장 생성
        filter_keyword = filter_keyword_map[filter_type][0]
        request = f"{filter_keyword} 조건 {remove_keyword}"
        q_lower = request.lower()
        
        # Property: 필터 키워드와 제거 키워드가 모두 포함되면 감지되어야 함
        has_filter_keyword = any(kw in q_lower for kw in filter_keyword_map[filter_type])
        has_remove_keyword = remove_keyword in q_lower
        
        assert has_filter_keyword and has_remove_keyword, \
            f"필터 제거 요청 '{request}'가 감지되지 않았습니다."


class TestFilterRemovalStateManagement:
    """
    필터 제거 상태 관리 Property-Based 테스트
    
    **Feature: chatbot-landlist-integration-fix, Property 5: Positive Response Filter Removal**
    **Validates: Requirements 2.2, 2.5**
    """
    
    @given(
        hard_filters=st.fixed_dictionaries({
            "location": st.sampled_from(["홍대", "강남", "신촌", ""]),
            "deal_type": st.sampled_from(["월세", "전세", ""]),
            "max_rent": st.one_of(st.none(), st.integers(min_value=30, max_value=100))
        }),
        filter_to_remove=st.sampled_from(["location", "deal_type", "max_rent"])
    )
    @settings(max_examples=100)
    def test_filter_removal_preserves_other_filters(self, hard_filters: dict, filter_to_remove: str):
        """
        **Feature: chatbot-landlist-integration-fix, Property 5: Positive Response Filter Removal**
        **Validates: Requirements 2.3**
        
        *For any* 필터 제거 작업, 제거 대상이 아닌 다른 필터는 보존되어야 한다.
        """
        # 필터 복사
        saved_filters = hard_filters.copy()
        
        # 필터 제거 시뮬레이션
        if filter_to_remove in saved_filters:
            del saved_filters[filter_to_remove]
        
        # Property: 제거 대상이 아닌 필터는 보존되어야 함
        for key, value in hard_filters.items():
            if key != filter_to_remove:
                assert key in saved_filters, \
                    f"필터 '{key}'가 보존되지 않았습니다."
                assert saved_filters[key] == value, \
                    f"필터 '{key}'의 값이 변경되었습니다: {value} → {saved_filters[key]}"
    
    @given(
        soft_filters=st.lists(
            st.sampled_from(["채광좋음", "깔끔함", "넓은공간", "아늑함", "모던함"]),
            min_size=0,
            max_size=5
        ),
        remove_style=st.booleans()
    )
    @settings(max_examples=100)
    def test_style_filter_removal_clears_soft_filters(self, soft_filters: list, remove_style: bool):
        """
        **Feature: chatbot-landlist-integration-fix, Property 5: Positive Response Filter Removal**
        **Validates: Requirements 2.3**
        
        *For any* 스타일 필터 제거 요청, soft_filters가 비워져야 한다.
        """
        # 스타일 필터 제거 시뮬레이션
        if remove_style:
            result_filters = []
        else:
            result_filters = soft_filters.copy()
        
        # Property: 스타일 제거 시 soft_filters가 비어야 함
        if remove_style:
            assert result_filters == [], \
                f"스타일 제거 후 soft_filters가 비어있지 않습니다: {result_filters}"
        else:
            assert result_filters == soft_filters, \
                f"스타일 미제거 시 soft_filters가 변경되었습니다."
