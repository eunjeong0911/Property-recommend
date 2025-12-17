"""PostgreSQL Connection Pool for RAG Service"""
import os
import threading
import logging
from psycopg2 import pool

logger = logging.getLogger(__name__)


class PostgresPool:
    """
    PostgreSQL 커넥션 풀 싱글톤 클래스
    
    ThreadedConnectionPool을 사용하여 스레드 안전한 연결 관리를 제공합니다.
    """
    _pool = None
    _lock = threading.Lock()
    
    @classmethod
    def _initialize_pool(cls):
        """커넥션 풀 초기화 (내부 메서드)"""
        if cls._pool is None:
            min_conn = int(os.getenv("POSTGRES_POOL_MIN", "2"))
            max_conn = int(os.getenv("POSTGRES_POOL_MAX", "10"))
            
            cls._pool = pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                dbname=os.getenv("POSTGRES_DB", "postgres"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                host=os.getenv("POSTGRES_HOST", "postgres"),
                port=os.getenv("POSTGRES_PORT", "5432")
            )
            logger.info(f"PostgreSQL connection pool initialized (min={min_conn}, max={max_conn})")
    
    @classmethod
    def get_connection(cls):
        """
        커넥션 풀에서 연결 획득
        
        Returns:
            psycopg2 connection object
            
        Raises:
            pool.PoolError: 풀이 소진되었거나 연결 실패 시
        """
        with cls._lock:
            if cls._pool is None:
                cls._initialize_pool()
        
        conn = cls._pool.getconn()
        logger.debug("Connection acquired from pool")
        return conn
    
    @classmethod
    def return_connection(cls, conn):
        """
        연결을 풀에 반환
        
        Args:
            conn: 반환할 psycopg2 connection object
        """
        if cls._pool is not None and conn is not None:
            cls._pool.putconn(conn)
            logger.debug("Connection returned to pool")
    
    @classmethod
    def close_all(cls):
        """모든 연결 종료 및 풀 정리"""
        with cls._lock:
            if cls._pool is not None:
                cls._pool.closeall()
                cls._pool = None
                logger.info("PostgreSQL connection pool closed")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """풀 초기화 여부 확인"""
        return cls._pool is not None
