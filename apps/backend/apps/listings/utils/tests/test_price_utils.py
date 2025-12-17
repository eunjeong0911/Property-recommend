"""
Property-based tests for price_utils module.

**Feature: performance-optimization, Property 5: 가격 파싱 라운드트립**
**Validates: Requirements 4.1, 7.1**
"""
import pytest
from hypothesis import given, strategies as st, settings

from apps.listings.utils.price_utils import (
    parse_korean_price,
    format_price_in_manwon,
)


class TestPriceParsingRoundtrip:
    """
    Property 5: 가격 파싱 라운드트립
    
    *For any* 유효한 한국어 가격 문자열에 대해, parse_korean_price로 파싱 후 
    format_price_in_manwon으로 포맷팅하면 원본과 동등한 의미의 문자열이 반환되어야 한다.
    """
    
    @given(st.integers(min_value=0, max_value=100000000))
    @settings(max_examples=100)
    def test_roundtrip_manwon_amounts(self, amount_in_manwon: int):
        """
        **Feature: performance-optimization, Property 5: 가격 파싱 라운드트립**
        **Validates: Requirements 4.1, 7.1**
        
        만원 단위 금액에 대해 포맷팅 후 파싱하면 원본 값이 복원되어야 한다.
        """
        # 만원 단위를 원 단위로 변환
        amount_in_won = amount_in_manwon * 10000
        
        # 포맷팅
        formatted = format_price_in_manwon(amount_in_won)
        
        # 파싱
        parsed = parse_korean_price(formatted)
        
        # 라운드트립 검증
        assert parsed == amount_in_won, (
            f"Roundtrip failed: {amount_in_won} -> '{formatted}' -> {parsed}"
        )
    
    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=100)
    def test_roundtrip_eok_only(self, eok: int):
        """
        **Feature: performance-optimization, Property 5: 가격 파싱 라운드트립**
        **Validates: Requirements 4.1, 7.1**
        
        억 단위만 있는 금액에 대해 라운드트립이 성공해야 한다.
        """
        # 억 단위를 원 단위로 변환
        amount_in_won = eok * 100000000
        
        # 포맷팅
        formatted = format_price_in_manwon(amount_in_won)
        
        # 파싱
        parsed = parse_korean_price(formatted)
        
        # 라운드트립 검증
        assert parsed == amount_in_won, (
            f"Roundtrip failed for {eok}억: {amount_in_won} -> '{formatted}' -> {parsed}"
        )
    
    @given(
        st.integers(min_value=1, max_value=100),
        st.integers(min_value=1, max_value=9999)
    )
    @settings(max_examples=100)
    def test_roundtrip_eok_and_manwon(self, eok: int, manwon: int):
        """
        **Feature: performance-optimization, Property 5: 가격 파싱 라운드트립**
        **Validates: Requirements 4.1, 7.1**
        
        억과 만원이 모두 있는 금액에 대해 라운드트립이 성공해야 한다.
        """
        # 원 단위로 변환
        amount_in_won = (eok * 100000000) + (manwon * 10000)
        
        # 포맷팅
        formatted = format_price_in_manwon(amount_in_won)
        
        # 파싱
        parsed = parse_korean_price(formatted)
        
        # 라운드트립 검증
        assert parsed == amount_in_won, (
            f"Roundtrip failed for {eok}억 {manwon}만원: {amount_in_won} -> '{formatted}' -> {parsed}"
        )
    
    def test_zero_amount(self):
        """0원에 대한 라운드트립 테스트"""
        formatted = format_price_in_manwon(0)
        parsed = parse_korean_price(formatted)
        assert parsed == 0
    
    def test_empty_string_returns_zero(self):
        """빈 문자열은 0을 반환해야 한다"""
        assert parse_korean_price('') == 0
        assert parse_korean_price(None) == 0
        assert parse_korean_price('-') == 0
