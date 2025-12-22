"""
Search Logging Utility for RAG Service

RAG 파이프라인에서 검색 로그를 PostgreSQL에 직접 저장합니다.
Django의 UserSearchLog 모델과 동일한 테이블 구조를 사용합니다.

**Validates: Requirements 1.1, 6.4**
"""
import json
import threading
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from .db_pool import PostgresPool

logger = logging.getLogger(__name__)


def log_user_search(
    query: str,
    result_ids: List[str],
    filters: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    search_duration_ms: int = 0,
    search_type: str = 'rag'
) -> None:
    """
    검색 로그를 비동기적으로 PostgreSQL에 저장합니다.
    
    별도 스레드에서 로그를 저장하여 API 응답 시간에 영향을 주지 않습니다.
    Django의 UserSearchLog 모델과 동일한 테이블(user_search_log)에 저장합니다.
    
    Args:
        query: 검색 질의 내용
        result_ids: 결과 매물 ID 목록
        filters: 적용된 필터 조건 (선택)
        user_id: 검색을 수행한 사용자 ID (선택, 비로그인 시 None)
        session_id: 세션 ID (선택, 비로그인 사용자 추적용)
        search_duration_ms: 검색 소요 시간 (밀리초)
        search_type: 검색 유형 ('rag', 'es', 'hybrid')
    
    Returns:
        None (비동기 저장이므로 반환값 없음)
    """
    def _save_log():
        conn = None
        try:
            conn = PostgresPool.get_connection()
            cur = conn.cursor()
            
            # user_search_log 테이블에 INSERT
            insert_query = """
                INSERT INTO user_search_log 
                (user_id, session_id, query, filters, result_ids, result_count, 
                 search_duration_ms, search_type, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(insert_query, (
                user_id,
                session_id or 'anonymous',
                query,
                json.dumps(filters or {}, ensure_ascii=False),
                json.dumps(result_ids, ensure_ascii=False),
                len(result_ids),
                search_duration_ms,
                search_type,
                datetime.now()
            ))
            
            conn.commit()
            cur.close()
            logger.debug(f"[RAG Logging] Search log saved: query='{query[:50]}', results={len(result_ids)}")
            
        except Exception as e:
            logger.error(f"[RAG Logging] Failed to save search log: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                PostgresPool.return_connection(conn)
    
    # 별도 스레드에서 저장 (API 응답 시간에 영향 없음)
    thread = threading.Thread(target=_save_log, daemon=True)
    thread.start()


def log_user_search_sync(
    query: str,
    result_ids: List[str],
    filters: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    search_duration_ms: int = 0,
    search_type: str = 'rag'
) -> Optional[int]:
    """
    검색 로그를 동기적으로 PostgreSQL에 저장합니다.
    
    테스트 또는 로그 저장 결과가 필요한 경우 사용합니다.
    
    Args:
        query: 검색 질의 내용
        result_ids: 결과 매물 ID 목록
        filters: 적용된 필터 조건 (선택)
        user_id: 검색을 수행한 사용자 ID (선택, 비로그인 시 None)
        session_id: 세션 ID (선택, 비로그인 사용자 추적용)
        search_duration_ms: 검색 소요 시간 (밀리초)
        search_type: 검색 유형 ('rag', 'es', 'hybrid')
    
    Returns:
        int: 생성된 로그의 ID (실패 시 None)
    """
    conn = None
    try:
        conn = PostgresPool.get_connection()
        cur = conn.cursor()
        
        # user_search_log 테이블에 INSERT하고 ID 반환
        insert_query = """
            INSERT INTO user_search_log 
            (user_id, session_id, query, filters, result_ids, result_count, 
             search_duration_ms, search_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        cur.execute(insert_query, (
            user_id,
            session_id or 'anonymous',
            query,
            json.dumps(filters or {}, ensure_ascii=False),
            json.dumps(result_ids, ensure_ascii=False),
            len(result_ids),
            search_duration_ms,
            search_type,
            datetime.now()
        ))
        
        log_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        
        logger.debug(f"[RAG Logging] Search log saved (sync): id={log_id}, query='{query[:50]}', results={len(result_ids)}")
        return log_id
        
    except Exception as e:
        logger.error(f"[RAG Logging] Failed to save search log (sync): {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            PostgresPool.return_connection(conn)
