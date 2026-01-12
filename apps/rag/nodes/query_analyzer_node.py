"""
Query Analyzer Node - OpenAI 기반 하드/소프트 필터 분석 + 세션 위치 관리

사용자 질문을 분석하여:
1. 하드 필터 추출 (위치, 가격, 건물타입, 시설 등)
2. 소프트 필터 추출 (깨끗한, 럭셔리한 등 - 없을 수 있음)
3. 검색 전략 결정 (neo4j | es_keyword | hybrid)
4. 캐시된 대화와의 관련성 판단 → 관련 있으면 컨텍스트로 활용
5. 세션 위치 저장/비교 (Redis) → 위치 변경 시 캐시 무효화
6. 스타일 매핑 적용 (자연어 → 시스템 태그 변환)
"""
import os
import json
import time
from typing import Dict, List, Any, Optional
from common.state import RAGState
from common.redis_cache import get_conversation_history, get_redis_client, clear_collected_conditions
from nodes.style_mapping import map_style_keywords


def analyze_query(state: RAGState) -> RAGState:
    """
    OpenAI를 사용하여 사용자 질문을 하드/소프트 필터로 분류
    + 캐시된 대화 컨텍스트와의 관련성 판단
    + Redis 세션 위치 저장/비교
    + 멀티턴 조건 수집 인터럽트
    
    Returns:
        state with hard_filters, soft_filters, search_strategy, use_cached_context populated
    """
    question = state.get("question", "")
    session_id = state.get("session_id", "")
    
    if not question:
        return state
    
    print(f"\n{'='*60}")
    print(f"[QueryAnalyzer] 🔍 질문 분석 시작: {question}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    # 기본값 설정
    state["query_type"] = "graph_search"
    state["is_followup"] = False
    state["conversation_complete"] = False
    
    # 이전에 수집된 조건 로드
    collected = state.get("collected_conditions") or {}
    print(f"[QueryAnalyzer] 📦 기존 수집 조건: {list(collected.keys())}")
    
    # ★★★ 이미 제거된 필터 목록 로드 (무한 루프 방지) - Requirements 2.5 ★★★
    removed_filters = collected.get("removed_filters", [])
    state["removed_filters"] = removed_filters
    if removed_filters:
        print(f"[QueryAnalyzer] 🗑️ 이미 제거된 필터: {removed_filters}")
    
    # =====================================================================
    # 필터 제거 확인 응답 처리 (Low Result Fallback) - Requirements 2.2, 2.3
    # =====================================================================
    pending_filter = collected.get("pending_filter_removal")
    if pending_filter:
        # ★★★ 확장된 긍정 응답 키워드 (다양한 표현 지원) - Requirements 2.2 ★★★
        confirmation_keywords = [
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
        rejection_keywords = [
            "아니", "아뇨", "ㄴㄴ", "노", "no", "nope", "싫어", "괜찮아", "그냥 둬", "그대로", "유지",
            "말고", "됐어", "안해", "필요없어", "그만", "취소"
        ]
        
        q_lower = question.strip().lower()
        
        # ★★★ 단순 긍정 응답 먼저 체크 (정확 매칭) ★★★
        q_stripped = question.strip()
        simple_confirmations = ["응", "웅", "엉", "네", "넵", "예", "ㅇ", "ㅇㅇ", "ok", "yes", "ㅇㅋ", "그래", "좋아"]
        if q_stripped in simple_confirmations:
            print(f"[QueryAnalyzer] ✅ 단순 긍정 응답 감지: '{q_stripped}' → 필터 '{pending_filter}' 제거")
            
            # 저장된 필터 스냅샷에서 복원
            saved_hard_filters = collected.get("saved_hard_filters", {}).copy()
            saved_soft_filters = list(collected.get("saved_soft_filters", []))
            
            # 제안된 필터 제거 (hard_filters 또는 soft_filters에서)
            filter_removed = False
            if pending_filter in saved_hard_filters:
                del saved_hard_filters[pending_filter]
                filter_removed = True
            elif pending_filter == "style" and saved_soft_filters:
                saved_soft_filters = []
                filter_removed = True
            
            # 복원된 필터를 state에 설정
            state["hard_filters"] = saved_hard_filters
            state["soft_filters"] = saved_soft_filters
            
            # ★★★ removed_filters를 collected_conditions에도 저장 (영속성) - Requirements 2.5 ★★★
            updated_removed = list(set(removed_filters + [pending_filter]))
            collected["removed_filters"] = updated_removed
            state["removed_filters"] = updated_removed
            
            # collected_conditions에서 임시 데이터 제거
            collected.pop("pending_filter_removal", None)
            collected.pop("saved_hard_filters", None)
            collected.pop("saved_soft_filters", None)
            state["collected_conditions"] = collected
            
            # 재검색 트리거
            state["conversation_complete"] = True
            state["pending_question"] = None
            
            print(f"[QueryAnalyzer] 🔄 필터 '{pending_filter}' 제거 완료 → 재검색 실행")
            print(f"[QueryAnalyzer] 📋 제거된 필터 목록: {updated_removed}")
            return state
        
        # ★★★ 사용자가 다른 필터를 제거해달라고 요청하는 경우 - Requirements 2.3 ★★★
        # 필터 키워드 매핑: 사용자가 언급할 수 있는 키워드 → 실제 필터 키
        filter_keyword_map = {
            # 위치 관련
            "location": ["위치", "지역", "동네", "장소", "근처", "주변", "홍대", "강남", "신촌", "대학교", "역", "구", "동"],
            # 방향 관련  
            "direction": ["남향", "북향", "동향", "서향", "방향"],
            # 층수 제외 관련
            "excluded_floors": ["1층", "반지하", "탑층", "층수", "층"],
            # 가격 관련
            "max_rent": ["월세", "렌트", "월"],
            "max_deposit": ["보증금", "전세금", "deposit", "보증"],
            # 건물 타입
            "building_type": ["원룸", "투룸", "오피스텔", "아파트", "빌라", "건물", "타입"],
            # 거래 유형
            "deal_type": ["전세", "매매", "거래"],
            # 시설 관련
            "facilities": ["시설", "편의점", "병원", "공원", "지하철", "역세권"],
            # 옵션 관련
            "options": ["옵션", "풀옵션", "에어컨", "세탁기", "냉장고"],
            # 스타일 관련 (soft_filters)
            "style": ["스타일", "분위기", "햇살", "채광", "깔끔", "모던", "럭셔리", "아늑", "조용"]
        }
        
        # 사용자가 특정 필터 제거를 요청했는지 확인
        requested_filter = None
        for filter_key, keywords in filter_keyword_map.items():
            if any(kw in q_lower for kw in keywords):
                # "X 빼줘", "X 제외해줘" 패턴 확인
                if any(remove_kw in q_lower for remove_kw in ["빼", "제외", "없이", "말고", "제거", "삭제"]):
                    requested_filter = filter_key
                    print(f"[QueryAnalyzer] 🎯 사용자가 '{filter_key}' 필터 제거 요청")
                    break
        
        if requested_filter:
            # 사용자가 요청한 필터 제거
            print(f"[QueryAnalyzer] ✅ 사용자 지정 필터 제거: '{requested_filter}'")
            
            # ★★★ 저장된 필터 스냅샷에서 복원 (핵심 수정!) ★★★
            saved_hard_filters = collected.get("saved_hard_filters", {}).copy()
            saved_soft_filters = list(collected.get("saved_soft_filters", []))
            
            # 요청한 필터 제거 (hard_filters 또는 soft_filters에서)
            if requested_filter in saved_hard_filters:
                del saved_hard_filters[requested_filter]
            elif requested_filter == "style" and saved_soft_filters:
                saved_soft_filters = []
            
            # 복원된 필터를 state에 설정
            state["hard_filters"] = saved_hard_filters
            state["soft_filters"] = saved_soft_filters
            
            print(f"[QueryAnalyzer] 📋 복원된 필터: {list(saved_hard_filters.keys())}")
            
            # ★★★ removed_filters를 collected_conditions에도 저장 (영속성) - Requirements 2.5 ★★★
            updated_removed = list(set(removed_filters + [requested_filter]))
            collected["removed_filters"] = updated_removed
            state["removed_filters"] = updated_removed
            
            # collected에서 임시 데이터 제거
            collected.pop("pending_filter_removal", None)
            collected.pop("saved_hard_filters", None)
            collected.pop("saved_soft_filters", None)
            state["collected_conditions"] = collected
            state["conversation_complete"] = True
            state["pending_question"] = None
            
            print(f"[QueryAnalyzer] 🔄 필터 '{requested_filter}' 제거 완료 → 재검색 실행")
            print(f"[QueryAnalyzer] 📋 제거된 필터 목록: {updated_removed}")
            return state
        
        elif any(kw in q_lower for kw in confirmation_keywords):
            # 사용자가 제안된 필터 제거 확인 → 해당 필터 삭제
            print(f"[QueryAnalyzer] ✅ 제안 필터 제거 확인! '{pending_filter}' 제거하고 재검색")
            
            # ★★★ 저장된 필터 스냅샷에서 복원 (핵심 수정!) ★★★
            saved_hard_filters = collected.get("saved_hard_filters", {}).copy()
            saved_soft_filters = list(collected.get("saved_soft_filters", []))
            
            # 제안된 필터 제거 (hard_filters 또는 soft_filters에서)
            if pending_filter in saved_hard_filters:
                del saved_hard_filters[pending_filter]
            elif pending_filter == "style" and saved_soft_filters:
                saved_soft_filters = []
            
            # 복원된 필터를 state에 설정
            state["hard_filters"] = saved_hard_filters
            state["soft_filters"] = saved_soft_filters
            
            print(f"[QueryAnalyzer] 📋 복원된 필터: {list(saved_hard_filters.keys())}")
            
            # ★★★ removed_filters를 collected_conditions에도 저장 (영속성) - Requirements 2.5 ★★★
            updated_removed = list(set(removed_filters + [pending_filter]))
            collected["removed_filters"] = updated_removed
            state["removed_filters"] = updated_removed
            
            # collected_conditions에서 임시 데이터 제거
            collected.pop("pending_filter_removal", None)
            collected.pop("saved_hard_filters", None)
            collected.pop("saved_soft_filters", None)
            state["collected_conditions"] = collected
            
            # 재검색 트리거 (조건 완성 상태로)
            state["conversation_complete"] = True
            state["pending_question"] = None
            
            print(f"[QueryAnalyzer] 🔄 필터 '{pending_filter}' 제거 완료 → 재검색 실행")
            print(f"[QueryAnalyzer] 📋 제거된 필터 목록: {updated_removed}")
            return state
            
        elif any(kw in q_lower for kw in rejection_keywords):
            # 사용자가 거부 → 기존 결과 유지
            print(f"[QueryAnalyzer] ❌ 필터 제거 거부 → 기존 결과 유지")
            collected.pop("pending_filter_removal", None)
            state["collected_conditions"] = collected
            state["conversation_complete"] = True
            state["pending_question"] = None
            return state

    
    # 최근 대화 히스토리 로드 (내부적으로 5개 제한됨)
    conversation_history = []
    if session_id:
        conversation_history = get_conversation_history(session_id)
        print(f"[QueryAnalyzer] 📚 대화 히스토리: {len(conversation_history)}개")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # OpenAI로 필터 분석 + 캐시 관련성 판단
        analysis = _analyze_with_openai(client, question, conversation_history)
        
        elapsed = time.time() - start_time
        print(f"[QueryAnalyzer] ⏱️ 분석 완료: {elapsed:.2f}s")
        
        # 상태 업데이트
        state["hard_filters"] = analysis.get("hard_filters", {})
        state["soft_filters"] = analysis.get("soft_filters", [])
        state["search_strategy"] = analysis.get("search_strategy", "hybrid")
        
        # ★★★ 스타일 매핑 적용 (Requirements 1.1, 1.4, 8.5) ★★★
        # 자연어 스타일 표현을 시스템 태그로 변환
        raw_soft_filters = state.get("soft_filters", [])
        if raw_soft_filters:
            mapped_tags, unmapped_styles = map_style_keywords(raw_soft_filters)
            state["soft_filters"] = mapped_tags
            state["unmapped_styles"] = unmapped_styles
            print(f"[QueryAnalyzer] 🎨 스타일 매핑: {raw_soft_filters} → 매핑됨: {mapped_tags}, 미매핑: {unmapped_styles}")
        else:
            state["unmapped_styles"] = []
        
        # 캐시 관련성 판단 결과
        use_cached_context = analysis.get("use_cached_context", False)
        cached_context_reason = analysis.get("cached_context_reason", "")
        state["use_cache"] = use_cached_context
        state["is_followup"] = use_cached_context
        
        # 현재 위치 추출
        current_location = state["hard_filters"].get("location", "")
        
        # 세션 위치 비교 및 관리
        if session_id and current_location:
            cached_location = _get_session_location(session_id)
            print(f"[QueryAnalyzer] 📍 현재 위치: '{current_location}', 캐시 위치: '{cached_location}'")
            
            if cached_location and cached_location != current_location:
                # 위치가 바뀜 → 캐시 무효화 + collected_conditions 초기화
                print(f"[QueryAnalyzer] ⚡ 위치 변경 감지: '{cached_location}' → '{current_location}' → 전체 초기화")
                state["cached_property_ids"] = []
                state["accumulated_results"] = {}
                state["is_followup"] = False
                state["use_cache"] = False
                # ★★★ collected_conditions도 초기화 ★★★
                collected = {}
                state["collected_conditions"] = {}
                if session_id:
                    clear_collected_conditions(session_id)
            elif not cached_location:
                # 첫 검색 → 위치 저장
                print(f"[QueryAnalyzer] 📍 첫 검색, 위치 저장: '{current_location}'")
            
            # 현재 위치 저장
            _save_session_location(session_id, current_location)
        
        # ★★★ LLM 기반 조건 변경 의도 감지 ★★★
        change_intent = analysis.get("condition_change_intent")
        if change_intent and change_intent != "null":
            print(f"[QueryAnalyzer] 🔄 조건 변경 요청 감지 (LLM): {change_intent}")
            # 해당 조건을 초기화하고 다시 질문
            if change_intent == "deal_type":
                collected.pop("deal_type", None)
                state["collected_conditions"] = collected
            elif change_intent == "location":
                collected.pop("location", None)
                state["collected_conditions"] = collected
            elif change_intent == "style":
                collected.pop("style", None)
                state["collected_conditions"] = collected
        
        # 로그 출력
        print(f"[QueryAnalyzer] 📋 하드 필터: {json.dumps(state['hard_filters'], ensure_ascii=False)}")
        print(f"[QueryAnalyzer] 🎨 소프트 필터: {state['soft_filters']}")
        print(f"[QueryAnalyzer] 🎯 검색 전략: {state['search_strategy']}")
        print(f"[QueryAnalyzer] 💾 후속 질문: {state['is_followup']}")
        
        # 가격 조건을 price_conditions에도 동기화 (기존 호환성)
        _sync_price_conditions(state)
        
        # =====================================================================
        # 멀티턴 조건 수집: 기존 조건과 병합 + 누락 체크
        # =====================================================================
        merged_conditions = _merge_conditions(collected, state["hard_filters"], state["soft_filters"])
        
        # ★ 스타일 폴백: 스타일 질문 상태에서 OpenAI가 스타일 추출 실패 시
        # 사용자 응답 전체를 스타일로 사용 (위치+거래유형은 있는데 스타일만 없을 때)
        if (collected.get("location") and collected.get("deal_type") 
            and not merged_conditions.get("style") 
            and not state["soft_filters"]
            and question.strip()):
            # 사용자 응답을 스타일로 처리
            user_style = question.strip()
            merged_conditions["style"] = [user_style]
            print(f"[QueryAnalyzer] 🔄 스타일 폴백: 사용자 응답 '{user_style}'를 스타일로 사용")
        
        state["collected_conditions"] = merged_conditions
        
        # 필수 조건 누락 체크
        missing = _check_missing_conditions(merged_conditions)
        state["missing_conditions"] = missing
        
        if missing:
            # 인터럽트: 첫 번째 누락 조건에 대한 질문 생성
            pending_q = _generate_followup_question(missing[0], merged_conditions)
            state["pending_question"] = pending_q
            state["conversation_complete"] = False
            print(f"[QueryAnalyzer] ❓ 누락 조건: {missing} → 인터럽트 질문 생성")
        else:
            state["pending_question"] = None
            state["conversation_complete"] = True
            print(f"[QueryAnalyzer] ✅ 모든 조건 수집 완료 → 검색 실행")
            
            # ★★★ 핵심: 수집된 조건을 hard_filters/soft_filters에 동기화 ★★★
            # 멀티턴에서 수집된 조건이 실제 검색에 반영되도록 함
            _sync_collected_to_filters(state, merged_conditions)
        
    except Exception as e:
        print(f"[QueryAnalyzer] ❌ OpenAI 분석 실패: {e}, 규칙 기반 폴백 사용")
        _fallback_analysis(state, question)
        
        # ★★★ 폴백에서도 스타일 매핑 적용 (Requirements 1.1, 1.4, 8.5) ★★★
        raw_soft_filters = state.get("soft_filters", [])
        if raw_soft_filters:
            mapped_tags, unmapped_styles = map_style_keywords(raw_soft_filters)
            state["soft_filters"] = mapped_tags
            state["unmapped_styles"] = unmapped_styles
            print(f"[QueryAnalyzer] 🎨 폴백 스타일 매핑: {raw_soft_filters} → 매핑됨: {mapped_tags}, 미매핑: {unmapped_styles}")
        else:
            state["unmapped_styles"] = []
        
        # 폴백에서도 조건 체크
        merged_conditions = _merge_conditions(collected, state.get("hard_filters", {}), state.get("soft_filters", []))
        state["collected_conditions"] = merged_conditions
        missing = _check_missing_conditions(merged_conditions)
        state["missing_conditions"] = missing
        
        if missing:
            state["pending_question"] = _generate_followup_question(missing[0], merged_conditions)
            state["conversation_complete"] = False
        else:
            state["pending_question"] = None
            state["conversation_complete"] = True
            # 폴백에서도 수집된 조건 동기화
            _sync_collected_to_filters(state, merged_conditions)
    
    return state


# =============================================================================
# Redis 세션 위치 관리
# =============================================================================

def _get_session_location(session_id: str) -> str:
    """세션의 저장된 위치 조회"""
    try:
        r = get_redis_client()
        key = f"session_loc:{session_id}"
        return r.get(key) or ""
    except Exception:
        return ""


def _save_session_location(session_id: str, location: str, ttl: int = 86400):
    """세션의 위치 저장 (24시간 유지)"""
    try:
        r = get_redis_client()
        key = f"session_loc:{session_id}"
        r.setex(key, ttl, location)
    except Exception as e:
        print(f"[QueryAnalyzer] 위치 저장 실패: {e}")


def _clear_session_location(session_id: str):
    """세션의 위치 삭제"""
    try:
        r = get_redis_client()
        r.delete(f"session_loc:{session_id}")
    except Exception:
        pass




def _analyze_with_openai(client, question: str, history: List[Dict] = None) -> Dict[str, Any]:
    """OpenAI API를 사용하여 질문 분석 + 검색 전략 결정"""
    
    history_text = ""
    if history and len(history) > 0:
        history_text = "\n\n이전 대화 (최근 5개):\n"
        for i, turn in enumerate(history[-5:], 1):
            q = turn.get('question', '')[:80]
            a = turn.get('answer', '')[:100]
            history_text += f"Q{i}: {q}\nA{i}: {a}...\n"
    
    def normalize_price(val):
        """가격 문자열(예: '1억', '1억 5천')을 만원 단위 숫자로 변환"""
        if val is None: return None
        if isinstance(val, (int, float)): return int(val)
        if not isinstance(val, str): return val
        
        val = val.replace(',', '').replace(' ', '')
        try:
            # "1억 5000" 또는 "1억 5천" -> 15000
            if '억' in val:
                parts = val.split('억')
                eok = int(re.sub(r'[^0-9]', '', parts[0])) if parts[0] else 0
                man = 0
                if len(parts) > 1 and parts[1]:
                    man_part = parts[1]
                    if '천' in man_part:
                        # "5천" -> 5000
                        cheon_match = re.search(r'(\d+)천', man_part)
                        if cheon_match:
                            man = int(cheon_match.group(1)) * 1000
                        else:
                            # "천"만 있는 경우 (예: "억천") - 드물지만 처리
                            man = 1000
                    else:
                        man_str = re.sub(r'[^0-9]', '', man_part)
                        man = int(man_str) if man_str else 0
                return eok * 10000 + man
            
            if '천' in val:
                match = re.search(r'(\d+)천', val)
                if match:
                    return int(match.group(1)) * 1000
                return 1000
                
            # 숫자만 있는 경우
            return int(re.sub(r'[^0-9]', '', val))
        except Exception:
            return val

    prompt = f"""사용자의 부동산 검색 질문을 분석하여 JSON 형식으로 반환하세요.

⚠️ 중요 규칙:
- 사용자가 **명시적으로 언급한 조건만** 추출하세요.
- 언급되지 않은 조건은 절대로 추론하거나 추가하지 마세요.
- 예: "중앙대 원룸 추천"에서 거래유형(월세/전세)은 언급되지 않았으므로 deal_type은 빈 문자열이어야 합니다.

💰 가격 추출 규칙:
- "60" 또는 "60만원" -> 60
- "1억" -> "1억"
- "1억 5천" -> "1억 5천"
- "2000/60" -> max_deposit: 2000, max_rent: 60
- 숫자가 모호할 경우(예: "60정도") 한국 부동산 관례에 따라 월세는 만원 단위(60 = 60만원)로 해석하세요.
- **절대로 60을 6000으로 변환하지 마세요.** (60은 60만원을 의미합니다)
- **"1억"과 같은 표현은 그대로 "1억"으로 추출해도 됩니다.** (시스템에서 자동으로 10000으로 변환합니다)

{history_text}
현재 질문: "{question}"

다음 형식으로 JSON만 반환하세요 (다른 텍스트 없이):
{{
    "hard_filters": {{
        "location": "지하철역 또는 지역명 (없으면 빈 문자열)",
        "deal_type": "월세|전세|매매|단기임대 (없으면 빈 문자열)",
        "building_type": "원투룸|빌라주택|오피스텔|아파트 (없으면 빈 문자열)",
        "max_deposit": 보증금 상한 만원 단위 숫자 (없으면 null),
        "min_deposit": 보증금 하한 만원 단위 숫자 (없으면 null),
        "max_rent": 월세 상한 만원 단위 숫자 (없으면 null),
        "max_size": 평수 상한 숫자 (없으면 null),
        "max_distance": 역까지 도보 분 숫자 (없으면 null),
        "facilities": ["subway", "convenience", "safety", "hospital", "park", "university"] 중 필요한 것들,
        "options": ["세탁기", "에어컨", "냉장고", "인덕션", "가스레인지", "전자레인지", "건조기", "TV", "침대", "옷장", "책상", "풀옵션"] 중 사용자가 원하는 것들 (없으면 빈 배열),
        "excluded_floors": ["1층", "반지하", "저층", "탑층"] 중 기피하는 층수 (없으면 빈 배열),
        "direction": "남향|동향|서향|북향|남동향 등 (없으면 빈 문자열)"
    }},
    "soft_filters": ["사용자가 원하는 스타일/분위기/선호도 키워드 - 정확한 태그명이 아니어도 됨 (예: 햇살좋은, 밝은, 아늑한, 조용한, 깔끔한, 넓은 등), 없으면 빈 배열"],
    "search_strategy": "neo4j_only|keyword_only|neo4j_keyword|keyword_vector|full",
    "use_cached_context": true 또는 false,
    "cached_context_reason": "관련성 판단 이유 (한 줄)",
    "condition_change_intent": "location|deal_type|style|null (사용자가 이미 설정한 조건을 변경하려는 의도가 있으면 해당 조건명, 없으면 null)"
}}

검색 전략 결정 규칙:
- "neo4j_only": 위치 + 시설(치안, 편의점, 공원 등)만 있고 가격/타입 없음
- "keyword_only": 가격 + 건물타입 + 거래타입만 있고 위치/시설 없음
- "neo4j_keyword": 위치/시설 + 가격/타입 모두 있음 (가장 일반적)
- "keyword_vector": 가격/타입 + 소프트 필터(깨끗한, 럭셔리한 등) 있음
- "full": 위치/시설 + 가격/타입 + 소프트 필터 모두 있음

캐시 관련성 판단 규칙:
- use_cached_context = true: 이전 대화의 후속 질문 (예: "더 싼 거", "그 중에서")
- use_cached_context = false: 새로운 위치/조건 언급
- 이전 대화가 없으면 항상 false

조건 변경 의도 감지 규칙:
- 사용자가 "아니 월세 말고 전세", "전세로 바꿔줘", "다른 지역으로" 등 이미 설정된 조건을 변경하려는 표현을 사용하면 해당 조건 타입 반환
- "location": 위치 변경 요청 (예: "다른 지역으로", "강남 말고 홍대로")
- "deal_type": 거래 유형 변경 요청 (예: "월세 말고 전세", "전세로 바꿔줘", "아니 매매로")
- "style": 스타일 조건 변경 요청 (예: "다른 스타일로", "조건 바꿔")
- 변경 의도가 없으면 null"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0
    )
    
    result_text = response.choices[0].message.content.strip()
    
    # JSON 파싱 (```json``` 블록 제거)
    if result_text.startswith("```"):
        result_text = result_text.split("```")[1]
        if result_text.startswith("json"):
            result_text = result_text[4:]
    
    result = json.loads(result_text)
    
    # 가격 정보 정규화 (만원 단위 숫자로 통일)
    hf = result.get("hard_filters", {})
    for key in ["max_deposit", "min_deposit", "max_rent"]:
        if key in hf:
            hf[key] = normalize_price(hf[key])
            
    return result


def _fallback_analysis(state: RAGState, question: str) -> None:
    """OpenAI 실패 시 규칙 기반 분석"""
    import re
    
    hard_filters: Dict[str, Any] = {
        "location": "",
        "deal_type": "",
        "building_type": "",
        "max_deposit": None,
        "max_rent": None,
        "facilities": [],
        "excluded_floors": [],
        "direction": ""
    }
    soft_filters: List[str] = []
    
    # 위치 추출 (기존 neo4j_search_node 패턴 재사용)
    location_pattern = r"(홍대|강남|신촌|이태원|잠실|여의도|명동|역삼|선릉|삼성|건대|왕십리|성수|합정|망원|연남|마포|용산|영등포|구로|노원|송파|동작|서초|강서|양천|은평|독산|금천|시흥|가산)"
    location_match = re.search(location_pattern, question)
    if location_match:
        hard_filters["location"] = location_match.group(1)
    
    # 역 패턴 추출
    station_pattern = r"(\w+역)"
    station_match = re.search(station_pattern, question)
    if station_match and not hard_filters["location"]:
        hard_filters["location"] = station_match.group(1).replace("역", "")
    
    # 거래 타입
    if "월세" in question:
        hard_filters["deal_type"] = "월세"
    elif "전세" in question:
        hard_filters["deal_type"] = "전세"
    elif "매매" in question:
        hard_filters["deal_type"] = "매매"
    
    # 건물 타입
    if "원룸" in question or "투룸" in question or "2룸" in question:
        hard_filters["building_type"] = "원투룸"
    elif "오피스텔" in question:
        hard_filters["building_type"] = "오피스텔"
    elif "아파트" in question:
        hard_filters["building_type"] = "아파트"
    elif "빌라" in question:
        hard_filters["building_type"] = "빌라주택"
    
    # 가격 추출
    deposit_pattern = r"보증금\s*(\d+)"
    deposit_match = re.search(deposit_pattern, question)
    if deposit_match:
        hard_filters["max_deposit"] = int(deposit_match.group(1))
    
    rent_pattern = r"월세\s*(\d+)"
    rent_match = re.search(rent_pattern, question)
    if rent_match:
        hard_filters["max_rent"] = int(rent_match.group(1))
    
    # 시설 키워드
    facility_keywords = {
        "subway": ["역세권", "지하철", "역 ", "역근처"],
        "convenience": ["편의점", "편세권", "마트"],
        "safety": ["치안", "안전", "cctv", "경찰"],
        "hospital": ["병원", "의원", "약국"],
        "park": ["공원", "산책", "녹지"],
        "university": ["대학", "학교", "캠퍼스"]
    }
    
    for facility, keywords in facility_keywords.items():
        if any(kw in question.lower() for kw in keywords):
            hard_filters["facilities"].append(facility)
            
    # 기피 층수 추출
    if "1층" in question and ("싫" in question or "제외" in question or "빼" in question):
        hard_filters["excluded_floors"].append("1층")
    if "반지하" in question and ("싫" in question or "제외" in question or "빼" in question):
        hard_filters["excluded_floors"].append("반지하")
        
    # 방향 추출
    if "남향" in question:
        hard_filters["direction"] = "남향"
    elif "동향" in question:
        hard_filters["direction"] = "동향"
    elif "서향" in question:
        hard_filters["direction"] = "서향"
    
    # 소프트 필터 추출
    soft_keywords = ["깨끗", "럭셔리", "가성비", "조용", "채광", "신축", "넓은", "아늑", "예쁜", "모던", "깔끔"]
    for kw in soft_keywords:
        if kw in question:
            soft_filters.append(kw)
    
    # 검색 전략 결정 (새 전략 체계)
    has_location = bool(hard_filters["location"]) or bool(hard_filters["facilities"])
    has_price_type = bool(hard_filters["deal_type"]) or bool(hard_filters["max_deposit"]) or bool(hard_filters["max_rent"])
    has_soft = bool(soft_filters)
    
    # 위치 키워드가 행정구역("~동", "~구")인 경우 Neo4j만으로는 부족할 수 있으므로
    # ES 키워드 검색을 함께 수행하는 전략을 선택해야 함
    is_admin_region = False
    if hard_filters["location"]:
        loc = hard_filters["location"]
        if loc.endswith("동") or loc.endswith("구") or loc.endswith("시"):
            is_admin_region = True
    
    if has_location and has_price_type and has_soft:
        search_strategy = "full"
    elif has_location and has_price_type:
        search_strategy = "neo4j_keyword"
    elif has_price_type and has_soft:
        search_strategy = "keyword_vector"
    elif has_location:
        # ★ 수정: 행정구역이면 neo4j_only 대신 neo4j_keyword(ES포함) 사용
        if is_admin_region:
             search_strategy = "neo4j_keyword"
        else:
             search_strategy = "neo4j_only"
    elif has_price_type:
        search_strategy = "keyword_only"
    else:
        search_strategy = "neo4j_keyword"  # 기본값
    
    state["hard_filters"] = hard_filters
    state["soft_filters"] = soft_filters
    state["search_strategy"] = search_strategy


def _sync_price_conditions(state: RAGState) -> None:
    """하드 필터의 가격 조건을 price_conditions에 동기화 (기존 호환성 유지)"""
    hard_filters = state.get("hard_filters", {})
    price_conditions = state.get("price_conditions", {}) or {}
    
    if hard_filters.get("max_deposit"):
        price_conditions["deposit_max"] = hard_filters["max_deposit"]
    if hard_filters.get("min_deposit"):
        price_conditions["deposit_min"] = hard_filters["min_deposit"]
    if hard_filters.get("max_rent"):
        price_conditions["rent_max"] = hard_filters["max_rent"]
    
    if price_conditions:
        state["price_conditions"] = price_conditions


# 단축 함수 (그래프 노드용)
def analyze(state: RAGState) -> RAGState:
    """그래프 노드 진입점"""
    return analyze_query(state)


# =============================================================================
# 멀티턴 조건 수집 헬퍼 함수
# =============================================================================

# 지원하는 거래 유형
DEAL_TYPES = ["전세", "월세", "매매", "단기임대"]

# 지원하는 스타일 태그 (34개)
STYLE_TAGS = [
    "깔끔함", "세련됨", "아늑함", "모던함", "럭셔리함", "탁트인전망", "화이트톤인테리어",
    "실용적임", "풀옵션", "채광좋음", "조용함", "넓은공간", "수납공간많음", "복층구조", "테라스있음",
    "1인가구추천", "신혼부부추천", "직장인추천", "학생추천", "재택근무추천",
    "신축", "가성비좋음", "반려동물가능", "주차가능", "보안좋음", "엘리베이터있음", "분리형원룸",
    "에어컨있음", "세탁기있음", "냉장고있음", "인덕션있음", "고층", "저층", "남향",
    "1층제외", "반지하제외", "탑층제외"
]


def _merge_conditions(existing: Dict, hard_filters: Dict, soft_filters: List[str]) -> Dict:
    """
    기존 수집 조건과 새 분석 결과를 병합
    
    병합 규칙:
    - 새 값이 있으면 기존 값을 덮어씀 (위치 변경 등)
    - soft_filters는 리스트에 추가
    """
    merged = existing.copy() if existing else {}
    
    # 위치 조건 병합
    new_location = hard_filters.get("location", "")
    if new_location:
        merged["location"] = new_location
    
    # 거래 유형 병합
    new_deal_type = hard_filters.get("deal_type", "")
    if new_deal_type:
        merged["deal_type"] = new_deal_type
    
    # 스타일/소프트 필터 병합 (기존 + 새로운)
    existing_styles = merged.get("style", [])
    if isinstance(existing_styles, str):
        existing_styles = [existing_styles] if existing_styles else []
    new_styles = soft_filters or []
    combined_styles = list(set(existing_styles + new_styles))
    if combined_styles:
        merged["style"] = combined_styles
    
    # 가격 정보 병합
    price_info = merged.get("price_info", {})
    if hard_filters.get("max_deposit"):
        price_info["max_deposit"] = hard_filters["max_deposit"]
    if hard_filters.get("min_deposit"):
        price_info["min_deposit"] = hard_filters["min_deposit"]
    if hard_filters.get("max_rent"):
        price_info["max_rent"] = hard_filters["max_rent"]
    if price_info:
        merged["price_info"] = price_info
    
    # 건물 타입 병합
    if hard_filters.get("building_type"):
        merged["building_type"] = hard_filters["building_type"]
    
    # 시설 병합
    if hard_filters.get("facilities"):
        existing_facilities = merged.get("facilities", [])
        merged["facilities"] = list(set(existing_facilities + hard_filters["facilities"]))
    
    return merged


def _check_missing_conditions(conditions: Dict) -> List[str]:
    """
    필수 조건 누락 체크
    
    필수 조건 (모두 충족해야 검색 실행):
    1. location: 위치 조건 (구/동/역/시설 기반)
    2. deal_type: 거래 유형 (전세/월세/매매/단기임대)
    
    선택 조건 (있으면 추가 필터로 사용):
    - style: 스타일/옵션 조건 (깨끗한, 밝은, 조용한 등)
    - price_info: 가격 조건
    - building_type: 건물 타입
    
    Returns:
        누락된 조건 목록 (순서대로 질문)
    """
    missing = []
    
    # 1. 위치 조건 체크
    has_location = bool(conditions.get("location")) or bool(conditions.get("facilities"))
    if not has_location:
        missing.append("location")
    
    # 2. 거래 유형 체크
    if not conditions.get("deal_type"):
        missing.append("deal_type")
    
    # 3. 스타일 조건 체크 (Requirements 4.1)
    # 위치와 거래유형이 있어도 스타일이 없으면 질문함
    if not conditions.get("style"):
        missing.append("style")
    
    return missing


def _generate_followup_question(missing_type: str, current_conditions: Dict) -> str:
    """
    누락된 조건에 대한 자연스러운 후속 질문 생성
    
    Args:
        missing_type: "location" | "deal_type" | "style"
        current_conditions: 현재까지 수집된 조건 (컨텍스트용)
    
    Returns:
        사용자에게 보낼 질문 문자열
    """
    # 현재 수집된 조건 컨텍스트
    location = current_conditions.get("location", "")
    deal_type = current_conditions.get("deal_type", "")
    
    if missing_type == "location":
        return f"""원하시는 **지역**을 알려주세요.

지하철역, 동네 이름, 혹은 주변 시설을 말씀해 주시면 해당 지역의 매물을 검색해 드립니다.

**입력 예시**
• "강남역 근처로 찾아줘"
• "마포구 서교동 쪽"
• "공원 가까운 곳"
"""
    
    elif missing_type == "deal_type":
        location_str = f"**{location}**에서 " if location else ""
        return f"""{location_str}어떤 **거래 유형**을 원하시나요?

계획하신 예산이나 보증금/월세 범위를 함께 말씀해 주셔도 좋습니다.

**선택 가능한 유형**
• 전세
• 월세
• 매매
• 단기임대
• "보증금 1000에 월세 50 정도"
"""
    
    elif missing_type == "style":
        context_parts = []
        if location:
            context_parts.append(f"**{location}**")
        if deal_type:
            context_parts.append(f"**{deal_type}**")
        context_str = " ".join(context_parts) + " 조건으로 " if context_parts else ""
        
        return f"""{context_str}원하시는 **스타일**이나 **상세 조건**이 있으신가요?

선호하는 인테리어, 필요한 옵션, 혹은 주변 환경에 대해 자유롭게 말씀해 주세요. AI가 분석하여 최적의 매물을 추천해 드립니다.

**입력 예시**
• "채광이 좋고 밝은 남향 집"
• "조용하고 보안이 좋은 안전한 곳"
• "풀옵션에 수납공간이 넉넉한 집"
• "주차가 편리한 신축 오피스텔"
"""
    
    # 기본 폴백
    return "추가 조건을 알려주세요!"


def _sync_collected_to_filters(state: RAGState, collected: Dict) -> None:
    """
    ★★★ 핵심 함수 ★★★
    멀티턴에서 수집된 조건을 hard_filters/soft_filters에 동기화
    
    이 함수가 없으면 멀티턴에서 수집한 location, deal_type이 
    실제 검색에 반영되지 않음!
    
    Requirements 4.5: 수집된 조건을 hard_filters와 soft_filters에 정확하게 동기화
    """
    hard_filters = state.get("hard_filters", {}) or {}
    soft_filters = state.get("soft_filters", []) or []
    unmapped_styles = state.get("unmapped_styles", []) or []
    
    # 1. 위치 동기화 (가장 중요!)
    if collected.get("location") and not hard_filters.get("location"):
        hard_filters["location"] = collected["location"]
        print(f"[Sync] 📍 위치 동기화: {collected['location']}")
    
    # 2. 거래 유형 동기화
    if collected.get("deal_type") and not hard_filters.get("deal_type"):
        hard_filters["deal_type"] = collected["deal_type"]
        print(f"[Sync] 🏠 거래유형 동기화: {collected['deal_type']}")
    
    # 3. 건물 타입 동기화
    if collected.get("building_type") and not hard_filters.get("building_type"):
        hard_filters["building_type"] = collected["building_type"]
        print(f"[Sync] 🏢 건물타입 동기화: {collected['building_type']}")
    
    # 4. 가격 정보 동기화
    if collected.get("price_info"):
        price_info = collected["price_info"]
        if price_info.get("max_deposit") and not hard_filters.get("max_deposit"):
            hard_filters["max_deposit"] = price_info["max_deposit"]
            print(f"[Sync] 💰 보증금 동기화: {price_info['max_deposit']}")
        if price_info.get("min_deposit") and not hard_filters.get("min_deposit"):
            hard_filters["min_deposit"] = price_info["min_deposit"]
        if price_info.get("max_rent") and not hard_filters.get("max_rent"):
            hard_filters["max_rent"] = price_info["max_rent"]
            print(f"[Sync] 💵 월세 동기화: {price_info['max_rent']}")
    
    # 5. 시설 동기화
    if collected.get("facilities") and not hard_filters.get("facilities"):
        hard_filters["facilities"] = collected["facilities"]
        print(f"[Sync] 🏪 시설 동기화: {collected['facilities']}")
        
    # 6. 기피 층수 및 방향 동기화
    if collected.get("excluded_floors") and not hard_filters.get("excluded_floors"):
        hard_filters["excluded_floors"] = collected["excluded_floors"]
        print(f"[Sync] 🚫 기피층수 동기화: {collected['excluded_floors']}")
    if collected.get("direction") and not hard_filters.get("direction"):
        hard_filters["direction"] = collected["direction"]
        print(f"[Sync] 🧭 방향 동기화: {collected['direction']}")
    
    # 7. 옵션 동기화
    if collected.get("options") and not hard_filters.get("options"):
        hard_filters["options"] = collected["options"]
        print(f"[Sync] ⚙️ 옵션 동기화: {collected['options']}")
    
    # ★★★ 8. 스타일 동기화 (Requirements 4.5) - 스타일 매핑 적용 ★★★
    if collected.get("style"):
        collected_styles = collected["style"]
        if isinstance(collected_styles, str):
            collected_styles = [collected_styles]
        
        # 스타일 매핑 적용 (자연어 → 시스템 태그)
        mapped_tags, new_unmapped = map_style_keywords(collected_styles)
        
        # ★★★ 핵심 수정: 기존 필터를 덮어씌워 중복 제거 (Requirements 4.5) ★★★
        # 기존에 있던 soft_filters와 unmapped_styles를 새로운 매핑 결과로 대체
        soft_filters = mapped_tags
        unmapped_styles = new_unmapped
        
        # ★★★ UI 동기화 수정: collected["style"]도 업데이트하여 프론트엔드 중복 제거 ★★★
        # 프론트엔드 필터바는 collected_conditions["style"]을 사용하므로 이를 정리해줘야 함
        new_style_list = list(set(mapped_tags + new_unmapped))
        collected["style"] = new_style_list
        
        print(f"[Sync] ✨ 스타일 동기화 (교체): 원본={collected_styles}, 매핑됨={mapped_tags}, 미매핑={new_unmapped}")
    
    # state 업데이트
    state["hard_filters"] = hard_filters
    state["soft_filters"] = soft_filters
    state["unmapped_styles"] = unmapped_styles
    
    # ★★★ 핵심 수정: 검색 전략 재계산 ★★★
    # 멀티턴에서 수집된 조건을 기반으로 검색 전략을 다시 결정
    _recalculate_search_strategy(state, hard_filters, soft_filters)
    
    print(f"[Sync] ✅ 최종 hard_filters: {hard_filters}")
    print(f"[Sync] ✅ 최종 soft_filters: {soft_filters}")
    if unmapped_styles:
        print(f"[Sync] ✅ 최종 unmapped_styles: {unmapped_styles}")


def _recalculate_search_strategy(state: RAGState, hard_filters: Dict, soft_filters: List[str]) -> None:
    """
    동기화된 조건을 기반으로 검색 전략 재계산
    
    검색 전략:
    - neo4j_only: 위치/시설만 있고 가격/타입 없음
    - keyword_only: 가격/타입만 있고 위치/시설 없음
    - neo4j_keyword: 위치/시설 + 가격/타입 모두 있음
    - keyword_vector: 가격/타입 + 소프트 필터 있음
    - full: 위치/시설 + 가격/타입 + 소프트 필터 모두 있음
    """
    has_location = bool(hard_filters.get("location")) or bool(hard_filters.get("facilities"))
    has_price_type = (
        bool(hard_filters.get("deal_type")) or 
        bool(hard_filters.get("max_deposit")) or 
        bool(hard_filters.get("max_rent")) or
        bool(hard_filters.get("building_type"))
    )
    has_soft = bool(soft_filters)
    
    if has_location and has_price_type and has_soft:
        strategy = "full"
    elif has_location and has_price_type:
        strategy = "neo4j_keyword"
    elif has_price_type and has_soft:
        strategy = "keyword_vector"
    elif has_location:
        strategy = "neo4j_only"
    elif has_price_type:
        strategy = "keyword_only"
    else:
        strategy = "neo4j_keyword"  # 기본값
    
    old_strategy = state.get("search_strategy", "")
    if old_strategy != strategy:
        print(f"[Sync] 🔄 검색 전략 변경: {old_strategy} → {strategy}")
    
    state["search_strategy"] = strategy






