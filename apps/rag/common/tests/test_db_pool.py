"""
PostgresPool 커넥션 풀 테스트

**Feature: performance-optimization, Property 3: 커넥션 풀 연결 관리**
**Validates: Requirements 5.3**
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from hypothesis import given, strategies as st, settings

import sys
import os

# apps/rag 디렉토리를 path에 추가
rag_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.abspath(rag_path))

from common.db_pool import PostgresPool


class TestPostgresPoolConnectionManagement:
    """PostgresPool 커넥션 풀 연결 관리 테스트"""
    
    @pytest.fixture(autouse=True)
    def reset_pool(self):
        """각 테스트 전후로 풀 인스턴스 초기화"""
        PostgresPool.close_all()
        yield
        PostgresPool.close_all()
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_connection_pool_reusability(self, num_connections: int):
        """
        **Feature: performance-optimization, Property 3: 커넥션 풀 연결 관리**
        **Validates: Requirements 5.3**
        
        *For any* PostgresPool에서 획득한 연결에 대해, 
        반환 후에도 풀에서 재사용 가능해야 한다.
        """
        from common.db_pool import PostgresPool
        
        # 각 hypothesis 예제마다 풀 초기화
        PostgresPool.close_all()
        
        # Mock ThreadedConnectionPool - 각 예제마다 새로운 mock 생성
        mock_pool = MagicMock()
        # getconn을 람다로 설정하여 매번 새 MagicMock 반환
        mock_pool.getconn.side_effect = lambda: MagicMock()
        
        with patch('common.db_pool.pool.ThreadedConnectionPool', return_value=mock_pool):
            with patch.dict(os.environ, {
                'POSTGRES_DB': 'test_db',
                'POSTGRES_USER': 'test_user',
                'POSTGRES_PASSWORD': 'test_pass',
                'POSTGRES_HOST': 'localhost',
                'POSTGRES_PORT': '5432',
                'POSTGRES_POOL_MIN': '2',
                'POSTGRES_POOL_MAX': '10'
            }):
                # 연결 획득
                acquired_connections = []
                for _ in range(num_connections):
                    conn = PostgresPool.get_connection()
                    acquired_connections.append(conn)
                
                # 모든 연결 반환
                for conn in acquired_connections:
                    PostgresPool.return_connection(conn)
                
                # 반환된 연결 수 확인
                assert mock_pool.putconn.call_count == num_connections, \
                    f"반환된 연결 수가 일치하지 않습니다. " \
                    f"예상: {num_connections}, 실제: {mock_pool.putconn.call_count}"
                
                # 풀 정리
                PostgresPool.close_all()
    
    def test_pool_initialization_once(self):
        """풀이 한 번만 초기화되는지 확인"""
        from common.db_pool import PostgresPool
        
        mock_pool = MagicMock()
        
        with patch('common.db_pool.pool.ThreadedConnectionPool', return_value=mock_pool) as mock_create:
            with patch.dict(os.environ, {
                'POSTGRES_DB': 'test_db',
                'POSTGRES_USER': 'test_user',
                'POSTGRES_PASSWORD': 'test_pass',
                'POSTGRES_HOST': 'localhost',
                'POSTGRES_PORT': '5432'
            }):
                # 여러 번 연결 획득
                PostgresPool.get_connection()
                PostgresPool.get_connection()
                PostgresPool.get_connection()
                
                # ThreadedConnectionPool은 한 번만 생성되어야 함
                assert mock_create.call_count == 1
    
    def test_close_all_terminates_pool(self):
        """close_all()이 풀을 정상적으로 종료하는지 확인"""
        from common.db_pool import PostgresPool
        
        mock_pool = MagicMock()
        
        with patch('common.db_pool.pool.ThreadedConnectionPool', return_value=mock_pool):
            with patch.dict(os.environ, {
                'POSTGRES_DB': 'test_db',
                'POSTGRES_USER': 'test_user',
                'POSTGRES_PASSWORD': 'test_pass',
                'POSTGRES_HOST': 'localhost',
                'POSTGRES_PORT': '5432'
            }):
                # 풀 초기화
                PostgresPool.get_connection()
                
                # 풀 종료
                PostgresPool.close_all()
                
                # closeall()이 호출되었는지 확인
                mock_pool.closeall.assert_called_once()
                
                # 풀이 None으로 설정되었는지 확인
                assert not PostgresPool.is_initialized()
    
    def test_return_connection_with_none_pool(self):
        """풀이 초기화되지 않은 상태에서 return_connection 호출 시 오류 없이 처리"""
        from common.db_pool import PostgresPool
        
        # 풀이 초기화되지 않은 상태
        PostgresPool.close_all()
        
        # None 연결 반환 시 오류 없이 처리
        PostgresPool.return_connection(None)
        
        # 임의의 연결 반환 시도 (풀이 없으므로 무시됨)
        mock_conn = MagicMock()
        PostgresPool.return_connection(mock_conn)
    
    def test_pool_configuration_from_env(self):
        """환경 변수에서 풀 설정을 올바르게 읽는지 확인"""
        from common.db_pool import PostgresPool
        
        mock_pool = MagicMock()
        
        with patch('common.db_pool.pool.ThreadedConnectionPool', return_value=mock_pool) as mock_create:
            with patch.dict(os.environ, {
                'POSTGRES_DB': 'custom_db',
                'POSTGRES_USER': 'custom_user',
                'POSTGRES_PASSWORD': 'custom_pass',
                'POSTGRES_HOST': 'custom_host',
                'POSTGRES_PORT': '5433',
                'POSTGRES_POOL_MIN': '5',
                'POSTGRES_POOL_MAX': '20'
            }):
                PostgresPool.get_connection()
                
                # 올바른 설정으로 풀이 생성되었는지 확인
                mock_create.assert_called_once_with(
                    minconn=5,
                    maxconn=20,
                    dbname='custom_db',
                    user='custom_user',
                    password='custom_pass',
                    host='custom_host',
                    port='5433'
                )
