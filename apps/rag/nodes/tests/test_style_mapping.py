"""
Style Mapping Module 단위 테스트

스타일 매핑 테이블 및 함수의 정확성을 검증합니다.

**Feature: chatbot-landlist-integration-fix**
**Validates: Requirements 10.1**
"""
import pytest
import sys
import os

# style_mapping.py 파일 직접 임포트 (패키지 __init__.py 우회)
style_mapping_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.abspath(style_mapping_path))

# 직접 모듈 로드 (패키지 임포트 우회)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "style_mapping", 
    os.path.join(style_mapping_path, "style_mapping.py")
)
style_mapping = importlib.util.module_from_spec(spec)
spec.loader.exec_module(style_mapping)

map_style_keywords = style_mapping.map_style_keywords
STYLE_MAPPING = style_mapping.STYLE_MAPPING
get_all_style_tags = style_mapping.get_all_style_tags
get_keywords_for_tag = style_mapping.get_keywords_for_tag


class TestStyleMappingBasic:
    """기본 스타일 매핑 테스트"""
    
    def test_sunlight_keywords_map_to_채광좋음(self):
        """햇살/햇빛/채광 관련 키워드가 '채광좋음'으로 매핑되는지 테스트"""
        keywords = ["햇살 잘 들어오는", "햇빛 좋은", "채광이 좋은", "밝은 집", "환한 방"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "채광좋음" in mapped
        assert len(unmapped) == 0
    
    def test_clean_keywords_map_to_깔끔함(self):
        """깔끔/청결/깨끗 관련 키워드가 '깔끔함'으로 매핑되는지 테스트"""
        keywords = ["깔끔한", "청결한", "깨끗한", "정돈된"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "깔끔함" in mapped
        assert len(unmapped) == 0
    
    def test_spacious_keywords_map_to_넓은공간(self):
        """넓은/널찍 관련 키워드가 '넓은공간'으로 매핑되는지 테스트"""
        keywords = ["넓은 방", "널찍한", "넓직한 공간"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "넓은공간" in mapped
        assert len(unmapped) == 0
    
    def test_cozy_keywords_map_to_아늑함(self):
        """아늑/포근/따뜻 관련 키워드가 '아늑함'으로 매핑되는지 테스트"""
        keywords = ["아늑한", "포근한", "따뜻한 분위기"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "아늑함" in mapped
        assert len(unmapped) == 0
    
    def test_modern_keywords_map_to_모던함(self):
        """모던/현대적 관련 키워드가 '모던함'으로 매핑되는지 테스트"""
        keywords = ["모던한", "현대적인", "미니멀한"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "모던함" in mapped
        assert len(unmapped) == 0
    
    def test_luxury_keywords_map_to_럭셔리함(self):
        """럭셔리/고급 관련 키워드가 '럭셔리함'으로 매핑되는지 테스트"""
        keywords = ["럭셔리한", "고급스러운", "프리미엄"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "럭셔리함" in mapped
        assert len(unmapped) == 0


class TestUnmappedKeywords:
    """매핑되지 않는 키워드 처리 테스트"""
    
    def test_unmapped_keyword_returned_in_unmapped_list(self):
        """매핑되지 않는 키워드가 unmapped 리스트에 포함되는지 테스트"""
        keywords = ["특이한스타일", "알수없는조건"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert len(mapped) == 0
        assert "특이한스타일" in unmapped
        assert "알수없는조건" in unmapped
    
    def test_mixed_mapped_and_unmapped(self):
        """매핑되는 키워드와 매핑되지 않는 키워드가 섞여있을 때 테스트"""
        keywords = ["햇살 좋은", "특이한조건", "깔끔한"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "채광좋음" in mapped
        assert "깔끔함" in mapped
        assert "특이한조건" in unmapped
    
    def test_empty_keyword_list(self):
        """빈 키워드 리스트 처리 테스트"""
        mapped, unmapped = map_style_keywords([])
        
        assert mapped == []
        assert unmapped == []
    
    def test_empty_string_keyword(self):
        """빈 문자열 키워드 처리 테스트"""
        keywords = ["", "햇살 좋은", ""]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "채광좋음" in mapped
        assert "" not in unmapped


class TestDuplicateHandling:
    """중복 처리 테스트"""
    
    def test_no_duplicate_tags_in_result(self):
        """동일한 태그로 매핑되는 여러 키워드가 있어도 중복 없이 반환되는지 테스트"""
        keywords = ["햇살 좋은", "햇빛 좋은", "채광 좋은", "밝은 집"]
        mapped, unmapped = map_style_keywords(keywords)
        
        # 모두 "채광좋음"으로 매핑되지만 중복 없이 1개만 있어야 함
        assert mapped.count("채광좋음") == 1
        assert len(mapped) == 1


class TestCaseInsensitivity:
    """대소문자 처리 테스트"""
    
    def test_lowercase_cctv_maps_to_보안좋음(self):
        """소문자 cctv가 '보안좋음'으로 매핑되는지 테스트"""
        keywords = ["cctv 있는"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "보안좋음" in mapped
    
    def test_uppercase_cctv_maps_to_보안좋음(self):
        """대문자 CCTV가 '보안좋음'으로 매핑되는지 테스트"""
        keywords = ["CCTV 있는"]
        mapped, unmapped = map_style_keywords(keywords)
        
        assert "보안좋음" in mapped


class TestSpaceHandling:
    """공백 처리 테스트"""
    
    def test_keyword_with_spaces_still_maps(self):
        """공백이 포함된 키워드도 올바르게 매핑되는지 테스트"""
        keywords = ["햇 살 좋 은"]
        mapped, unmapped = map_style_keywords(keywords)
        
        # 공백 제거 후 매핑되어야 함
        assert "채광좋음" in mapped


class TestHelperFunctions:
    """헬퍼 함수 테스트"""
    
    def test_get_all_style_tags_returns_unique_tags(self):
        """get_all_style_tags가 중복 없는 태그 목록을 반환하는지 테스트"""
        tags = get_all_style_tags()
        
        assert len(tags) == len(set(tags))
        assert "채광좋음" in tags
        assert "깔끔함" in tags
        assert "넓은공간" in tags
    
    def test_get_keywords_for_tag_returns_correct_keywords(self):
        """get_keywords_for_tag가 올바른 키워드 목록을 반환하는지 테스트"""
        keywords = get_keywords_for_tag("채광좋음")
        
        assert "햇살" in keywords
        assert "햇빛" in keywords
        assert "채광" in keywords
        assert "밝은" in keywords
    
    def test_get_keywords_for_nonexistent_tag_returns_empty(self):
        """존재하지 않는 태그에 대해 빈 리스트를 반환하는지 테스트"""
        keywords = get_keywords_for_tag("존재하지않는태그")
        
        assert keywords == []


class TestAllMappingKeywords:
    """모든 매핑 키워드 변환 테스트"""
    
    def test_all_mapping_keywords_produce_valid_tags(self):
        """STYLE_MAPPING의 모든 키워드가 유효한 태그로 매핑되는지 테스트"""
        for keyword, expected_tag in STYLE_MAPPING.items():
            mapped, unmapped = map_style_keywords([keyword])
            
            assert expected_tag in mapped, \
                f"키워드 '{keyword}'가 '{expected_tag}'로 매핑되지 않았습니다. 결과: {mapped}"
            assert len(unmapped) == 0, \
                f"키워드 '{keyword}'가 unmapped에 포함되었습니다."



# =============================================================================
# Property-Based Tests (Hypothesis)
# =============================================================================

from hypothesis import given, strategies as st, settings, assume


class TestStyleMappingProperties:
    """
    스타일 매핑 Property-Based 테스트
    
    **Feature: chatbot-landlist-integration-fix, Property 1: Style Mapping Consistency**
    **Validates: Requirements 1.1, 1.4, 8.1, 8.2, 8.3, 8.5**
    """
    
    @given(
        keywords=st.lists(
            st.sampled_from(list(STYLE_MAPPING.keys())),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_known_keywords_always_map_to_valid_tags(self, keywords: list):
        """
        **Feature: chatbot-landlist-integration-fix, Property 1: Style Mapping Consistency**
        **Validates: Requirements 1.1, 1.4, 8.1, 8.2, 8.3, 8.5**
        
        *For any* 자연어 스타일 표현이 STYLE_MAPPING 테이블에 정의된 경우,
        스타일 매핑 함수를 적용하면 올바른 시스템 태그로 변환되어야 한다.
        """
        mapped, unmapped = map_style_keywords(keywords)
        
        # Property 1: 알려진 키워드는 항상 매핑되어야 함
        assert len(unmapped) == 0, \
            f"알려진 키워드가 매핑되지 않았습니다: {unmapped}"
        
        # Property 2: 매핑된 태그는 유효한 시스템 태그여야 함
        all_valid_tags = set(STYLE_MAPPING.values())
        for tag in mapped:
            assert tag in all_valid_tags, \
                f"유효하지 않은 태그가 반환되었습니다: {tag}"
    
    @given(
        keywords=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('L', 'N')),
                min_size=1,
                max_size=20
            ),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_mapping_result_has_no_duplicates(self, keywords: list):
        """
        **Feature: chatbot-landlist-integration-fix, Property 1: Style Mapping Consistency**
        **Validates: Requirements 1.1**
        
        *For any* 키워드 리스트에 대해, 매핑 결과에는 중복된 태그가 없어야 한다.
        """
        mapped, unmapped = map_style_keywords(keywords)
        
        # Property: 매핑된 태그에 중복이 없어야 함
        assert len(mapped) == len(set(mapped)), \
            f"매핑 결과에 중복이 있습니다: {mapped}"
    
    @given(
        keywords=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('L', 'N')),
                min_size=0,
                max_size=20
            ),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_mapping_preserves_input_count_or_reduces(self, keywords: list):
        """
        **Feature: chatbot-landlist-integration-fix, Property 1: Style Mapping Consistency**
        **Validates: Requirements 1.4**
        
        *For any* 키워드 리스트에 대해, 매핑된 태그 수 + 매핑되지 않은 키워드 수는
        원본 키워드 수보다 작거나 같아야 한다 (중복 제거 및 빈 문자열 제외로 인해).
        """
        # 빈 문자열 제외한 원본 키워드 수
        non_empty_keywords = [k for k in keywords if k]
        
        mapped, unmapped = map_style_keywords(keywords)
        
        # Property: 결과 수는 원본 수보다 작거나 같아야 함
        assert len(mapped) + len(unmapped) <= len(non_empty_keywords), \
            f"결과 수가 원본보다 많습니다: mapped={len(mapped)}, unmapped={len(unmapped)}, original={len(non_empty_keywords)}"
    
    @given(
        keyword=st.sampled_from(list(STYLE_MAPPING.keys()))
    )
    @settings(max_examples=100)
    def test_single_keyword_maps_to_expected_tag(self, keyword: str):
        """
        **Feature: chatbot-landlist-integration-fix, Property 1: Style Mapping Consistency**
        **Validates: Requirements 8.1, 8.2, 8.3, 8.5**
        
        *For any* STYLE_MAPPING에 정의된 단일 키워드에 대해,
        해당 키워드의 예상 태그가 매핑 결과에 포함되어야 한다.
        """
        expected_tag = STYLE_MAPPING[keyword]
        mapped, unmapped = map_style_keywords([keyword])
        
        # Property: 예상 태그가 결과에 포함되어야 함
        assert expected_tag in mapped, \
            f"키워드 '{keyword}'가 '{expected_tag}'로 매핑되지 않았습니다. 결과: {mapped}"
    
    @given(
        prefix=st.text(
            alphabet=st.characters(whitelist_categories=('L',)),
            min_size=0,
            max_size=5
        ),
        keyword=st.sampled_from(list(STYLE_MAPPING.keys())),
        suffix=st.text(
            alphabet=st.characters(whitelist_categories=('L',)),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_keyword_in_context_still_maps(self, prefix: str, keyword: str, suffix: str):
        """
        **Feature: chatbot-landlist-integration-fix, Property 1: Style Mapping Consistency**
        **Validates: Requirements 1.1, 1.4**
        
        *For any* STYLE_MAPPING 키워드가 다른 텍스트에 포함되어 있어도,
        해당 키워드의 태그로 매핑되어야 한다.
        """
        # 키워드를 포함한 문장 생성
        full_text = f"{prefix}{keyword}{suffix}"
        expected_tag = STYLE_MAPPING[keyword]
        
        mapped, unmapped = map_style_keywords([full_text])
        
        # Property: 키워드가 포함된 텍스트도 올바르게 매핑되어야 함
        assert expected_tag in mapped, \
            f"'{full_text}'가 '{expected_tag}'로 매핑되지 않았습니다. 결과: {mapped}"
