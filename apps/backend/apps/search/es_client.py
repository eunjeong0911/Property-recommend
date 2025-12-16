# =============================================================================
# Elasticsearch Client Singleton
# =============================================================================
#
# 역할: ES 연결 관리를 위한 싱글톤 클라이언트
#
# Requirements: 5.3 - ES 연결 오류 발생 시 예외를 로깅하고 빈 결과 반환
# =============================================================================

import os
import logging
from typing import Optional
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


class ESClient:
    """
    Elasticsearch 클라이언트 싱글톤 클래스
    
    애플리케이션 전체에서 단일 ES 연결을 공유하여 리소스 효율성 유지
    """
    _instance: Optional[Elasticsearch] = None
    
    @classmethod
    def get_client(cls) -> Elasticsearch:
        """
        ES 클라이언트 인스턴스 반환 (싱글톤)
        
        Returns:
            Elasticsearch: ES 클라이언트 인스턴스
        """
        if cls._instance is None:
            es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
            es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
            es_url = f"http://{es_host}:{es_port}"
            
            try:
                cls._instance = Elasticsearch(
                    hosts=[es_url],
                    timeout=30,
                    max_retries=3,
                    retry_on_timeout=True
                )
                # 연결 확인
                if cls._instance.ping():
                    logger.info(f"Elasticsearch connected: {es_url}")
                else:
                    logger.warning(f"Elasticsearch ping failed: {es_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Elasticsearch: {e}")
                raise
        
        return cls._instance
    
    @classmethod
    def close(cls) -> None:
        """ES 클라이언트 연결 종료"""
        if cls._instance is not None:
            try:
                cls._instance.close()
                logger.info("Elasticsearch connection closed")
            except Exception as e:
                logger.error(f"Error closing Elasticsearch connection: {e}")
            finally:
                cls._instance = None
    
    @classmethod
    def is_connected(cls) -> bool:
        """ES 연결 상태 확인"""
        if cls._instance is None:
            return False
        try:
            return cls._instance.ping()
        except Exception:
            return False
    
    @classmethod
    def reset(cls) -> None:
        """클라이언트 인스턴스 리셋 (테스트용)"""
        cls._instance = None
