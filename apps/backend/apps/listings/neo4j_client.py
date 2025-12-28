"""
Neo4j 드라이버 싱글톤 클래스

Requirements 2.1, 2.2, 2.3을 충족하기 위한 싱글톤 패턴 구현
- 애플리케이션 시작 시 드라이버를 한 번만 생성하여 재사용
- 스레드 안전성을 위한 Lock 적용
- 애플리케이션 종료 시 드라이버 연결 정상 종료
"""
import os
import threading
import logging
from typing import Optional

from neo4j import GraphDatabase, Driver

logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Neo4j 연결 오류"""
    pass


class Neo4jClient:
    """
    Neo4j 드라이버 싱글톤 클래스
    
    스레드 안전한 싱글톤 패턴으로 Neo4j 드라이버를 관리합니다.
    """
    _instance: Optional['Neo4jClient'] = None
    _driver: Optional[Driver] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'Neo4jClient':
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_driver(cls) -> Driver:
        """
        싱글톤 패턴으로 Neo4j 드라이버 반환
        
        Returns:
            Driver: Neo4j 드라이버 인스턴스
            
        Raises:
            Neo4jConnectionError: Neo4j 연결 실패 시
        """
        if cls._driver is None:
            with cls._lock:
                # Double-checked locking
                if cls._driver is None:
                    try:
                        uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
                        user = os.getenv("NEO4J_USER", "neo4j")
                        password = os.getenv("NEO4J_PASSWORD")
                        
                        if not all([uri, user, password]):
                            raise Neo4jConnectionError(
                                "Neo4j 환경 변수가 설정되지 않았습니다. "
                                "NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD를 확인하세요."
                            )
                        
                        cls._driver = GraphDatabase.driver(
                            uri,
                            auth=(user, password)
                        )
                        logger.info("Neo4j 드라이버가 생성되었습니다.")
                    except Exception as e:
                        logger.error(f"Neo4j 연결 실패: {e}")
                        raise Neo4jConnectionError(f"Neo4j 연결에 실패했습니다: {e}")
        
        return cls._driver
    
    @classmethod
    def close(cls) -> None:
        """
        애플리케이션 종료 시 드라이버 정리
        
        드라이버가 존재하면 연결을 종료하고 인스턴스를 정리합니다.
        """
        with cls._lock:
            if cls._driver is not None:
                try:
                    cls._driver.close()
                    logger.info("Neo4j 드라이버가 종료되었습니다.")
                except Exception as e:
                    logger.error(f"Neo4j 드라이버 종료 중 오류: {e}")
                finally:
                    cls._driver = None
    
    @classmethod
    def reset(cls) -> None:
        """
        테스트용: 싱글톤 인스턴스 초기화
        
        주의: 이 메서드는 테스트 목적으로만 사용해야 합니다.
        """
        with cls._lock:
            if cls._driver is not None:
                try:
                    cls._driver.close()
                except Exception:
                    pass
                cls._driver = None
            cls._instance = None
