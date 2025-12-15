# =============================================================================
# Search Logging Helper - 비동기 검색 로그 저장
# =============================================================================
#
# 역할: 검색 로그를 비동기적으로 저장하여 API 응답 시간에 영향을 주지 않음
#
# Requirements: 1.3
# =============================================================================

import threading
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


def log_user_search(
    query: str,
    result_ids: List[str],
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
    session_id: Optional[str] = None,
    search_duration_ms: int = 0,
    search_type: str = 'rag'
) -> None:
    """
    검색 로그를 비동기적으로 저장합니다.
    
    별도 스레드에서 로그를 저장하여 API 응답 시간에 영향을 주지 않습니다.
    
    Args:
        query: 검색 질의 내용
        result_ids: 결과 매물 ID 목록
        filters: 적용된 필터 조건 (선택)
        user: 검색을 수행한 사용자 (선택, 비로그인 시 None)
        session_id: 세션 ID (선택, 비로그인 사용자 추적용)
        search_duration_ms: 검색 소요 시간 (밀리초)
        search_type: 검색 유형 ('rag', 'es', 'hybrid')
    
    Returns:
        None (비동기 저장이므로 반환값 없음)
    """
    def _save_log():
        try:
            # 지연 임포트로 순환 참조 방지
            from .models import UserSearchLog
            
            UserSearchLog.objects.create(
                user=user,
                session_id=session_id or 'anonymous',
                query=query,
                filters=filters or {},
                result_ids=result_ids,
                result_count=len(result_ids),
                search_duration_ms=search_duration_ms,
                search_type=search_type
            )
            logger.debug(f"Search log saved: query='{query[:50]}', results={len(result_ids)}")
        except Exception as e:
            logger.error(f"Failed to save search log: {e}")
    
    # 별도 스레드에서 저장 (API 응답 시간에 영향 없음)
    thread = threading.Thread(target=_save_log, daemon=True)
    thread.start()


def log_user_search_sync(
    query: str,
    result_ids: List[str],
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
    session_id: Optional[str] = None,
    search_duration_ms: int = 0,
    search_type: str = 'rag'
) -> Optional['UserSearchLog']:
    """
    검색 로그를 동기적으로 저장합니다.
    
    테스트 또는 로그 저장 결과가 필요한 경우 사용합니다.
    
    Args:
        query: 검색 질의 내용
        result_ids: 결과 매물 ID 목록
        filters: 적용된 필터 조건 (선택)
        user: 검색을 수행한 사용자 (선택, 비로그인 시 None)
        session_id: 세션 ID (선택, 비로그인 사용자 추적용)
        search_duration_ms: 검색 소요 시간 (밀리초)
        search_type: 검색 유형 ('rag', 'es', 'hybrid')
    
    Returns:
        UserSearchLog: 생성된 로그 객체 (실패 시 None)
    """
    try:
        from .models import UserSearchLog
        
        log = UserSearchLog.objects.create(
            user=user,
            session_id=session_id or 'anonymous',
            query=query,
            filters=filters or {},
            result_ids=result_ids,
            result_count=len(result_ids),
            search_duration_ms=search_duration_ms,
            search_type=search_type
        )
        logger.debug(f"Search log saved (sync): query='{query[:50]}', results={len(result_ids)}")
        return log
    except Exception as e:
        logger.error(f"Failed to save search log (sync): {e}")
        return None
