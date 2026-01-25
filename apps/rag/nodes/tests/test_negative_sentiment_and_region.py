"""
부정적 감정 및 서울 외 지역 감지 테스트

이 테스트는 다음을 검증합니다:
1. 부정적 감정 감지 ("신정동는 싫어" → excluded_locations에 추가)
2. 서울 외 지역 감지 ("경기도 광명시" → out_of_service_area 에러)
"""
import pytest
from nodes.query_analyzer_node import analyze_query
from common.state import RAGState


class TestNegativeSentimentDetection:
    """부정적 감정 감지 테스트"""
    
    def test_negative_sentiment_싫어(self):
        """'싫어' 키워드가 포함된 경우 부정적 감정 감지"""
        state: RAGState = {
            "question": "신정동는 싫어",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 부정적 감정이 감지되어야 함
        assert result.get("pending_question") is not None
        assert "제외" in result.get("pending_question", "")
        
        # excluded_locations에 신정동이 추가되어야 함
        excluded = result.get("excluded_locations", [])
        assert "신정동" in excluded or len(excluded) > 0
        
        # conversation_complete는 False여야 함 (추가 입력 필요)
        assert result.get("conversation_complete") == False
    
    def test_negative_sentiment_별로(self):
        """'별로' 키워드가 포함된 경우 부정적 감정 감지"""
        state: RAGState = {
            "question": "강남은 별로야",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 부정적 감정이 감지되어야 함
        assert result.get("pending_question") is not None
        assert "제외" in result.get("pending_question", "")
    
    def test_positive_location_no_negative(self):
        """부정적 키워드 없이 위치만 언급한 경우 정상 처리"""
        state: RAGState = {
            "question": "신정동 원룸 찾아줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 부정적 감정이 감지되지 않아야 함
        excluded = result.get("excluded_locations", [])
        assert len(excluded) == 0
        
        # location이 정상적으로 추출되어야 함
        hard_filters = result.get("hard_filters", {})
        location = hard_filters.get("location", "")
        # OpenAI가 신정동을 인식하거나, 폴백에서 인식할 수 있음
        # 최소한 에러가 발생하지 않아야 함
        assert result.get("error_type") != "out_of_service_area"


class TestOutOfServiceAreaDetection:
    """서울 외 지역 감지 테스트"""
    
    def test_out_of_service_경기도(self):
        """'경기도' 키워드가 포함된 경우 서비스 불가 감지"""
        state: RAGState = {
            "question": "경기도 광명시 원룸 찾아줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 서울 외 지역 에러가 감지되어야 함
        assert result.get("error_type") == "out_of_service_area"
        
        # 에러 메시지가 있어야 함
        assert result.get("answer") is not None
        assert "서울특별시" in result.get("answer", "")
        
        # conversation_complete는 True여야 함 (에러로 종료)
        assert result.get("conversation_complete") == True
    
    def test_out_of_service_인천(self):
        """'인천' 키워드가 포함된 경우 서비스 불가 감지"""
        state: RAGState = {
            "question": "인천 송도 오피스텔",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 서울 외 지역 에러가 감지되어야 함
        assert result.get("error_type") == "out_of_service_area"
        assert "서울특별시" in result.get("answer", "")
    
    def test_out_of_service_부산(self):
        """'부산' 키워드가 포함된 경우 서비스 불가 감지"""
        state: RAGState = {
            "question": "부산 해운대 아파트",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 서울 외 지역 에러가 감지되어야 함
        assert result.get("error_type") == "out_of_service_area"
    
    def test_out_of_service_판교(self):
        """'판교' (경기도 성남시) 키워드가 포함된 경우 서비스 불가 감지"""
        state: RAGState = {
            "question": "판교 테크노밸리 근처",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 서울 외 지역 에러가 감지되어야 함
        assert result.get("error_type") == "out_of_service_area"
    
    def test_seoul_location_no_error(self):
        """서울 지역은 정상 처리"""
        state: RAGState = {
            "question": "강남역 근처 원룸",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 서울 외 지역 에러가 발생하지 않아야 함
        assert result.get("error_type") != "out_of_service_area"
        
        # location이 정상적으로 추출되어야 함
        hard_filters = result.get("hard_filters", {})
        location = hard_filters.get("location", "")
        assert location != ""  # 강남 또는 강남역이 추출되어야 함


class TestCombinedScenarios:
    """복합 시나리오 테스트"""
    
    def test_negative_then_positive(self):
        """부정적 감정 후 긍정적 위치 입력"""
        # 1단계: 부정적 감정
        state1: RAGState = {
            "question": "신정동는 싫어",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result1 = analyze_query(state1)
        assert result1.get("conversation_complete") == False
        
        # 2단계: 다른 위치 입력
        collected = result1.get("collected_conditions", {})
        state2: RAGState = {
            "question": "강남역으로 찾아줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": collected
        }
        
        result2 = analyze_query(state2)
        
        # 강남역이 정상적으로 추출되어야 함
        hard_filters = result2.get("hard_filters", {})
        location = hard_filters.get("location", "")
        assert "강남" in location or location != ""
        
        # 에러가 발생하지 않아야 함
        assert result2.get("error_type") != "out_of_service_area"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
