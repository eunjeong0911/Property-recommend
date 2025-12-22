"""
Listings 앱 설정

Requirements 2.3을 충족하기 위해 애플리케이션 종료 시 Neo4j 드라이버를 정상 종료합니다.
"""
import atexit
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ListingsConfig(AppConfig):
    """Listings 앱 설정 클래스"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.listings'
    verbose_name = '매물 관리'
    
    def ready(self):
        """
        앱이 준비되면 호출됩니다.
        
        atexit 핸들러를 등록하여 애플리케이션 종료 시 
        Neo4j 드라이버를 정상적으로 종료합니다.
        """
        # atexit 핸들러 등록
        atexit.register(self._cleanup_neo4j_driver)
        logger.debug("Neo4j 드라이버 종료 핸들러가 등록되었습니다.")
    
    def _cleanup_neo4j_driver(self):
        """
        애플리케이션 종료 시 Neo4j 드라이버를 정리합니다.
        """
        try:
            from .neo4j_client import Neo4jClient
            Neo4jClient.close()
            logger.info("애플리케이션 종료: Neo4j 드라이버가 정상적으로 종료되었습니다.")
        except Exception as e:
            logger.error(f"Neo4j 드라이버 종료 중 오류 발생: {e}")
