"""
Property-based tests for ES bulk indexing module.

**Feature: search-logging-elasticsearch, Property 2: ES 문서 필드 완전성**
**Validates: Requirements 3.2, 3.3, 3.5, 4.2**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
import string
import sys
import os

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from es_bulk_index import transform_to_es_doc, parse_price, INDEX_NAME


# Strategy definitions for generating realistic test data
safe_chars = string.ascii_letters + string.digits + ' '
korean_chars = '가나다라마바사아자차카타파하서울강남역세권'

# Land number strategy (numeric string)
land_num_strategy = st.text(alphabet=string.digits, min_size=1, max_size=15)

# Address strategy
address_strategy = st.text(
    alphabet=safe_chars + korean_chars,
    min_size=0,
    max_size=200
)

# Search text strategy
search_text_strategy = st.text(
    alphabet=safe_chars + korean_chars + '.,()[]',
    min_size=0,
    max_size=500
)

# Style tags strategy
style_tag_strategy = st.sampled_from([
    '풀옵션', '역세권', '신축', '주차가능', '분리형원룸',
    '수납공간많음', '엘리베이터있음', '반려동물가능', '옥탑방'
])
style_tags_strategy = st.lists(style_tag_strategy, min_size=0, max_size=10)

# Price strategy (만원 단위)
price_strategy = st.integers(min_value=0, max_value=1000000)

# Coordinate strategy
lat_strategy = st.floats(min_value=33.0, max_value=39.0, allow_nan=False, allow_infinity=False)
lon_strategy = st.floats(min_value=124.0, max_value=132.0, allow_nan=False, allow_infinity=False)

# Building type strategy
building_type_strategy = st.sampled_from(['원룸', '빌라', '아파트', '오피스텔', ''])

# Deal type strategy
deal_type_strategy = st.sampled_from(['월세', '전세', '매매', ''])


@st.composite
def listing_strategy(draw):
    """Generate a realistic listing dictionary"""
    land_num = draw(land_num_strategy)
    assume(land_num)  # Ensure non-empty land_num
    
    lat = draw(lat_strategy)
    lon = draw(lon_strategy)
    
    # Generate price strings
    deposit = draw(price_strategy)
    monthly_rent = draw(st.integers(min_value=0, max_value=500))
    jeonse = draw(price_strategy)
    sale = draw(price_strategy)
    
    return {
        "매물번호": land_num,
        "주소_정보": {
            "전체주소": draw(address_strategy)
        },
        "좌표_정보": {
            "위도": lat,
            "경도": lon
        },
        "거래_정보": {
            "거래유형": draw(deal_type_strategy),
            "보증금": f"{deposit}만원" if deposit > 0 else "-",
            "월세": f"{monthly_rent}만원" if monthly_rent > 0 else "-",
            "전세": f"{jeonse}만원" if jeonse > 0 else "-",
            "매매가": f"{sale}만원" if sale > 0 else "-",
        },
        "매물_정보": {
            "건물형태": draw(building_type_strategy)
        },
        "search_text": draw(search_text_strategy),
        "style_tags": draw(style_tags_strategy),
        "매물_URL": f"https://example.com/house/{land_num}",
    }


class TestESDocumentCompleteness:
    """
    Property 2: ES 문서 필드 완전성
    
    *For any* 유효한 매물 JSON 데이터에 대해, transform_to_es_doc() 변환 후 
    ES 문서에는 land_num, address, search_text, style_tags, deposit, location 
    필드가 모두 포함되어야 한다.
    """
    
    @given(listing=listing_strategy())
    @settings(max_examples=100)
    def test_es_document_contains_all_required_fields(self, listing: dict):
        """
        **Feature: search-logging-elasticsearch, Property 2: ES 문서 필드 완전성**
        **Validates: Requirements 3.2, 3.3, 3.5, 4.2**
        
        변환된 ES 문서에 모든 필수 필드가 포함되어 있는지 검증합니다.
        """
        doc = transform_to_es_doc(listing)
        
        # Document should be created for valid listings
        assert doc is not None, "Document should be created for valid listing"
        
        # Check document structure
        assert "_index" in doc, "Document should have _index"
        assert "_id" in doc, "Document should have _id"
        assert "_source" in doc, "Document should have _source"
        
        # Check index name
        assert doc["_index"] == INDEX_NAME, f"Index should be {INDEX_NAME}"
        
        source = doc["_source"]
        
        # Required fields per Requirements 3.2, 4.2
        required_fields = [
            "land_num",
            "address", 
            "search_text",
            "style_tags",
            "deposit",
            "location",
            "building_type",
            "deal_type",
            "monthly_rent",
            "jeonse_price",
            "sale_price",
            "url"
        ]
        
        for field in required_fields:
            assert field in source, f"Missing required field: {field}"
    
    @given(listing=listing_strategy())
    @settings(max_examples=100)
    def test_land_num_preserved(self, listing: dict):
        """
        **Feature: search-logging-elasticsearch, Property 2: ES 문서 필드 완전성**
        **Validates: Requirements 3.2, 4.2**
        
        매물번호가 정확히 보존되는지 검증합니다.
        """
        doc = transform_to_es_doc(listing)
        assert doc is not None
        
        source = doc["_source"]
        assert source["land_num"] == str(listing["매물번호"]), (
            f"land_num mismatch: expected {listing['매물번호']}, got {source['land_num']}"
        )
        
        # _id should also match land_num
        assert doc["_id"] == str(listing["매물번호"]), (
            f"_id should match land_num"
        )
    
    @given(listing=listing_strategy())
    @settings(max_examples=100)
    def test_style_tags_is_list(self, listing: dict):
        """
        **Feature: search-logging-elasticsearch, Property 2: ES 문서 필드 완전성**
        **Validates: Requirements 3.5**
        
        style_tags가 리스트 타입인지 검증합니다.
        """
        doc = transform_to_es_doc(listing)
        assert doc is not None
        
        source = doc["_source"]
        assert isinstance(source["style_tags"], list), (
            f"style_tags should be a list, got {type(source['style_tags'])}"
        )
    
    @given(listing=listing_strategy())
    @settings(max_examples=100)
    def test_deposit_is_integer(self, listing: dict):
        """
        **Feature: search-logging-elasticsearch, Property 2: ES 문서 필드 완전성**
        **Validates: Requirements 3.3**
        
        deposit이 정수 타입인지 검증합니다.
        """
        doc = transform_to_es_doc(listing)
        assert doc is not None
        
        source = doc["_source"]
        assert isinstance(source["deposit"], int), (
            f"deposit should be an integer, got {type(source['deposit'])}"
        )
        assert source["deposit"] >= 0, "deposit should be non-negative"
    
    @given(listing=listing_strategy())
    @settings(max_examples=100)
    def test_location_structure(self, listing: dict):
        """
        **Feature: search-logging-elasticsearch, Property 2: ES 문서 필드 완전성**
        **Validates: Requirements 3.4**
        
        location이 올바른 geo_point 구조인지 검증합니다.
        """
        doc = transform_to_es_doc(listing)
        assert doc is not None
        
        source = doc["_source"]
        location = source["location"]
        
        # Location can be None if coordinates are invalid
        if location is not None:
            assert "lat" in location, "location should have 'lat' field"
            assert "lon" in location, "location should have 'lon' field"
            assert isinstance(location["lat"], float), "lat should be float"
            assert isinstance(location["lon"], float), "lon should be float"
    
    @given(listing=listing_strategy())
    @settings(max_examples=100)
    def test_search_text_preserved(self, listing: dict):
        """
        **Feature: search-logging-elasticsearch, Property 2: ES 문서 필드 완전성**
        **Validates: Requirements 4.2**
        
        search_text가 원본 그대로 보존되는지 검증합니다.
        """
        doc = transform_to_es_doc(listing)
        assert doc is not None
        
        source = doc["_source"]
        assert source["search_text"] == listing.get("search_text", ""), (
            "search_text should be preserved from original listing"
        )


class TestPriceParser:
    """
    가격 파싱 함수 테스트
    """
    
    @given(amount=st.integers(min_value=0, max_value=100000))
    @settings(max_examples=50)
    def test_parse_price_만원_format(self, amount: int):
        """만원 형식 가격 파싱 테스트"""
        price_str = f"{amount}만원"
        result = parse_price(price_str)
        assert result == amount, f"Expected {amount}, got {result}"
    
    @given(억=st.integers(min_value=1, max_value=50))
    @settings(max_examples=30)
    def test_parse_price_억_format(self, 억: int):
        """억 형식 가격 파싱 테스트"""
        price_str = f"{억}억"
        result = parse_price(price_str)
        expected = 억 * 10000
        assert result == expected, f"Expected {expected}, got {result}"
    
    @given(
        억=st.integers(min_value=1, max_value=20),
        만=st.integers(min_value=0, max_value=9999)
    )
    @settings(max_examples=50)
    def test_parse_price_억_만원_format(self, 억: int, 만: int):
        """억 + 만원 형식 가격 파싱 테스트"""
        price_str = f"{억}억 {만}만원"
        result = parse_price(price_str)
        expected = 억 * 10000 + 만
        assert result == expected, f"Expected {expected}, got {result}"
    
    def test_parse_price_invalid_values(self):
        """유효하지 않은 가격 값 테스트"""
        assert parse_price("-") == 0
        assert parse_price("") == 0
        assert parse_price(None) == 0
        assert parse_price("정보없음") == 0
    
    def test_parse_price_with_commas(self):
        """쉼표가 포함된 가격 파싱 테스트"""
        assert parse_price("3,000만원") == 3000
        assert parse_price("1억 5,000만원") == 15000


class TestInvalidListings:
    """
    유효하지 않은 매물 데이터 처리 테스트
    """
    
    def test_missing_land_num_returns_none(self):
        """매물번호가 없는 경우 None 반환"""
        listing = {
            "주소_정보": {"전체주소": "서울시 강남구"},
            "search_text": "test"
        }
        doc = transform_to_es_doc(listing)
        assert doc is None, "Should return None for listing without land_num"
    
    def test_empty_land_num_returns_none(self):
        """매물번호가 빈 문자열인 경우 None 반환"""
        listing = {
            "매물번호": "",
            "주소_정보": {"전체주소": "서울시 강남구"},
        }
        doc = transform_to_es_doc(listing)
        assert doc is None, "Should return None for empty land_num"
    
    def test_missing_optional_fields_handled(self):
        """선택적 필드가 없어도 정상 처리"""
        listing = {
            "매물번호": "12345"
            # 다른 필드 없음
        }
        doc = transform_to_es_doc(listing)
        assert doc is not None, "Should handle missing optional fields"
        
        source = doc["_source"]
        assert source["land_num"] == "12345"
        assert source["address"] == ""
        assert source["search_text"] == ""
        assert source["style_tags"] == []
        assert source["deposit"] == 0
