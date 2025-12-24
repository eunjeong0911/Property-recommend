"""
Classify Node - 질문 분류 및 캐시 무효화 결정

핵심 로직:
- 새 질문에서 위치 추출
- 세션의 기존 위치와 비교
- 위치가 바뀌면 캐시 무효화 (새로 검색)
- 위치가 같으면 캐시 유지 (후속 질문으로 필터링)
"""
from common.state import RAGState
from common.redis_cache import get_redis_client
import json


def classify(state: RAGState) -> RAGState:
    """
    질문 분류 및 캐시 무효화 결정
    
    - 새 질문에서 위치 추출
    - 세션의 기존 위치와 비교
    - 위치가 바뀌면 cached_property_ids 초기화 → 새 검색
    """
    question = state.get("question", "")
    session_id = state.get("session_id", "")
    cached_ids = state.get("cached_property_ids", [])
    
    # 기본값 설정
    state["query_type"] = "graph_search"
    
    # 세션 ID가 없으면 그대로 반환
    if not session_id:
        return state
    
    # 현재 질문에서 위치 추출 (neo4j_search_node의 함수 사용)
    try:
        from nodes.neo4j_search_node import extract_location
        current_location, location_type = extract_location(question)
    except Exception as e:
        print(f"[Classify] Location extraction failed: {e}")
        current_location = ""
        location_type = ""
    
    print(f"[Classify] Current location: '{current_location}' (type: {location_type})")
    
    # 위치가 감지되면 세션의 기존 위치와 비교
    if current_location:
        cached_location = _get_session_location(session_id)
        print(f"[Classify] Cached location: '{cached_location}'")
        
        if cached_location and cached_location != current_location:
            # 위치가 바뀜 → 캐시 무효화
            print(f"[Classify] ⚡ Location changed: '{cached_location}' → '{current_location}' → CLEAR CACHE")
            state["cached_property_ids"] = []  # 캐시 무효화
            state["accumulated_results"] = {}
            _save_session_location(session_id, current_location)
        elif not cached_location:
            # 첫 검색 → 위치 저장
            print(f"[Classify] 📍 First search, saving location: '{current_location}'")
            _save_session_location(session_id, current_location)
        else:
            # 위치가 같음 → 후속 질문 (캐시 유지)
            print(f"[Classify] ✓ Same location, keeping cache ({len(cached_ids)} IDs)")
    
    return state


def _get_session_location(session_id: str) -> str:
    """세션의 저장된 위치 조회"""
    try:
        r = get_redis_client()
        key = f"session_loc:{session_id}"
        return r.get(key) or ""
    except Exception:
        return ""


def _save_session_location(session_id: str, location: str, ttl: int = 7200):
    """세션의 위치 저장"""
    try:
        r = get_redis_client()
        key = f"session_loc:{session_id}"
        r.setex(key, ttl, location)
    except Exception as e:
        print(f"[Classify] Failed to save location: {e}")
