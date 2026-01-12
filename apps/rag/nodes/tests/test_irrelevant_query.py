"""
부동산 관련 없는 질문 감지 테스트

이 테스트는 다음을 검증합니다:
1. 인사/잡담 감지 ("안녕", "반가워" 등) - OpenAI 기반
2. 챗봇 정보 질문 감지 ("네 이름은?", "누가 만들었어?" 등) - OpenAI 기반
3. 일반 상식 질문 감지 ("대통령 이름", "날씨" 등) - OpenAI 기반
4. 불가능한 요청 감지 ("우주에 있는 집" 등) - OpenAI 기반
5. 기타 주제 질문 감지 (음식, 여행, 쇼핑 등) - OpenAI 기반

주의: 이 테스트는 OpenAI API 키가 필요합니다.
      API 키가 없으면 일부 테스트는 폴백 로직으로 처리됩니다.
"""
import pytest
import os
from nodes.query_analyzer_node import analyze_query
from common.state import RAGState


# OpenAI API 키 확인
HAS_OPENAI_KEY = bool(os.getenv("OPENAI_API_KEY"))
skip_if_no_openai = pytest.mark.skipif(
    not HAS_OPENAI_KEY,
    reason="OpenAI API key not available"
)


class TestGreetingsAndSmallTalk:
    """인사 및 잡담 감지 테스트"""
    
    def test_greeting_안녕(self):
        """'안녕' 인사 감지 - 규칙 기반으로도 처리 가능"""
        state: RAGState = {
            "question": "안녕",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 관련 없는 질문으로 감지되어야 함
        assert result.get("error_type") == "irrelevant_query"
        assert result.get("conversation_complete") == True
        assert result.get("answer") is not None
        assert "부동산" in result.get("answer", "")
    
    @skip_if_no_openai
    def test_greeting_반가워(self):
        """'반가워' 인사 감지 - OpenAI 필요"""
        state: RAGState = {
            "question": "반가워",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
        assert "부동산" in result.get("answer", "")
    
    def test_greeting_야(self):
        """'야' 호칭 감지 - 규칙 기반으로도 처리 가능"""
        state: RAGState = {
            "question": "야",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
    
    @skip_if_no_openai
    def test_small_talk_뭐해(self):
        """'뭐해' 잡담 감지 - OpenAI 필요"""
        state: RAGState = {
            "question": "뭐해?",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"


class TestChatbotInfoQuestions:
    """챗봇 정보 질문 감지 테스트 - OpenAI 필요"""
    
    @skip_if_no_openai
    def test_chatbot_name(self):
        """챗봇 이름 질문 감지"""
        state: RAGState = {
            "question": "네 이름은 뭐니?",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
        assert "부동산" in result.get("answer", "")
    
    @skip_if_no_openai
    def test_chatbot_creator(self):
        """챗봇 제작자 질문 감지"""
        state: RAGState = {
            "question": "누가 만들었어?",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
    
    @skip_if_no_openai
    def test_chatbot_identity(self):
        """챗봇 정체 질문 감지"""
        state: RAGState = {
            "question": "너 누구야?",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"


class TestGeneralKnowledgeQuestions:
    """일반 상식 질문 감지 테스트 - OpenAI 필요"""
    
    @skip_if_no_openai
    def test_president_question(self):
        """대통령 관련 질문 감지"""
        state: RAGState = {
            "question": "우리나라 대통령 이름이 뭐야?",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
        assert "부동산" in result.get("answer", "")
    
    @skip_if_no_openai
    def test_weather_question(self):
        """날씨 질문 감지"""
        state: RAGState = {
            "question": "오늘 날씨 어때?",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
    
    @skip_if_no_openai
    def test_time_question(self):
        """시간 질문 감지"""
        state: RAGState = {
            "question": "지금 몇 시야?",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"


class TestImpossibleRequests:
    """불가능한 요청 감지 테스트 - OpenAI 필요"""
    
    @skip_if_no_openai
    def test_space_house(self):
        """우주 집 요청 감지"""
        state: RAGState = {
            "question": "우주에 있는 집 찾아줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
        assert "부동산" in result.get("answer", "")
    
    @skip_if_no_openai
    def test_mars_house(self):
        """화성 집 요청 감지"""
        state: RAGState = {
            "question": "화성 부동산 알려줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
    
    @skip_if_no_openai
    def test_underwater_house(self):
        """바다 속 집 요청 감지"""
        state: RAGState = {
            "question": "바다 속 집 찾아줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"


class TestOtherTopics:
    """기타 주제 질문 감지 테스트 - OpenAI 필요"""
    
    @skip_if_no_openai
    def test_food_question(self):
        """음식 관련 질문 감지"""
        state: RAGState = {
            "question": "맛집 추천해줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
    
    @skip_if_no_openai
    def test_travel_question(self):
        """여행 관련 질문 감지"""
        state: RAGState = {
            "question": "여행지 추천해줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"
    
    @skip_if_no_openai
    def test_shopping_question(self):
        """쇼핑 관련 질문 감지"""
        state: RAGState = {
            "question": "옷 어디서 사?",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") == "irrelevant_query"


class TestRealEstateQuestions:
    """부동산 관련 질문은 정상 처리되는지 테스트"""
    
    def test_valid_search_강남역(self):
        """정상적인 부동산 검색 질문"""
        state: RAGState = {
            "question": "강남역 근처 원룸 찾아줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        # 관련 없는 질문으로 감지되지 않아야 함
        assert result.get("error_type") != "irrelevant_query"
    
    def test_valid_search_월세(self):
        """가격 조건이 포함된 부동산 검색"""
        state: RAGState = {
            "question": "월세 50만원 이하 집",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") != "irrelevant_query"
    
    def test_valid_search_오피스텔(self):
        """건물 타입이 포함된 부동산 검색"""
        state: RAGState = {
            "question": "홍대 오피스텔 추천해줘",
            "session_id": "test_session",
            "cached_property_ids": [],
            "accumulated_results": {},
            "collected_conditions": {}
        }
        
        result = analyze_query(state)
        
        assert result.get("error_type") != "irrelevant_query"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
