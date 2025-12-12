"""
Neo4jClient 싱글톤 테스트

**Feature: performance-optimization, Property 2: Neo4j 드라이버 싱글톤 일관성**
**Validates: Requirements 2.1, 2.2**
"""
import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings

import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestNeo4jClientSingleton:
    """Neo4jClient 싱글톤 패턴 테스트"""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """각 테스트 전후로 싱글톤 인스턴스 초기화"""
        from apps.listings.neo4j_client import Neo4jClient
        Neo4jClient.reset()
        yield
        Neo4jClient.reset()
    
    @given(st.integers(min_value=2, max_value=10))
    @settings(max_examples=100)
    def test_neo4j_singleton_consistency(self, num_calls: int):
        """
        **Feature: performance-optimization, Property 2: Neo4j 드라이버 싱글톤 일관성**
        **Validates: Requirements 2.1, 2.2**
        
        *For any* Neo4jClient.get_driver() 호출에 대해, 
        항상 동일한 드라이버 인스턴스가 반환되어야 한다.
        """
        from apps.listings.neo4j_client import Neo4jClient
        
        # Mock Neo4j driver
        mock_driver = MagicMock()
        
        with patch('apps.listings.neo4j_client.GraphDatabase.driver', return_value=mock_driver):
            with patch.dict(os.environ, {
                'NEO4J_URI': 'bolt://localhost:7687',
                'NEO4J_USER': 'neo4j',
                'NEO4J_PASSWORD': 'password'
            }):
                # 여러 번 호출
                drivers = [Neo4jClient.get_driver() for _ in range(num_calls)]
                
                # 모든 호출이 동일한 인스턴스를 반환해야 함
                first_driver = drivers[0]
                for driver in drivers[1:]:
                    assert driver is first_driver, \
                        f"get_driver()가 다른 인스턴스를 반환했습니다. " \
                        f"첫 번째: {id(first_driver)}, 현재: {id(driver)}"
    
    def test_get_driver_creates_driver_once(self):
        """get_driver()가 드라이버를 한 번만 생성하는지 확인"""
        from apps.listings.neo4j_client import Neo4jClient
        
        mock_driver = MagicMock()
        
        with patch('apps.listings.neo4j_client.GraphDatabase.driver', return_value=mock_driver) as mock_create:
            with patch.dict(os.environ, {
                'NEO4J_URI': 'bolt://localhost:7687',
                'NEO4J_USER': 'neo4j',
                'NEO4J_PASSWORD': 'password'
            }):
                # 여러 번 호출
                Neo4jClient.get_driver()
                Neo4jClient.get_driver()
                Neo4jClient.get_driver()
                
                # GraphDatabase.driver는 한 번만 호출되어야 함
                assert mock_create.call_count == 1
    
    def test_close_terminates_driver(self):
        """close()가 드라이버를 정상적으로 종료하는지 확인"""
        from apps.listings.neo4j_client import Neo4jClient
        
        mock_driver = MagicMock()
        
        with patch('apps.listings.neo4j_client.GraphDatabase.driver', return_value=mock_driver):
            with patch.dict(os.environ, {
                'NEO4J_URI': 'bolt://localhost:7687',
                'NEO4J_USER': 'neo4j',
                'NEO4J_PASSWORD': 'password'
            }):
                # 드라이버 생성
                Neo4jClient.get_driver()
                
                # 드라이버 종료
                Neo4jClient.close()
                
                # close()가 호출되었는지 확인
                mock_driver.close.assert_called_once()
    
    def test_missing_env_vars_raises_error(self):
        """환경 변수가 없을 때 오류가 발생하는지 확인"""
        from apps.listings.neo4j_client import Neo4jClient, Neo4jConnectionError
        
        with patch.dict(os.environ, {}, clear=True):
            # 환경 변수 제거
            os.environ.pop('NEO4J_URI', None)
            os.environ.pop('NEO4J_USER', None)
            os.environ.pop('NEO4J_PASSWORD', None)
            
            with pytest.raises(Neo4jConnectionError):
                Neo4jClient.get_driver()
