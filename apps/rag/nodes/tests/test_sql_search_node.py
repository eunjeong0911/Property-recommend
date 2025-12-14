"""
SQL Search Node 이미지 조회 결과 일관성 테스트

**Feature: performance-optimization, Property 4: 이미지 조회 결과 일관성**
**Validates: Requirements 6.2, 6.3**
"""
import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings

import sys
import os

# apps/rag 디렉토리를 path에 추가
rag_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.abspath(rag_path))


class TestImageQueryConsistency:
    """이미지 조회 결과 일관성 Property 테스트"""
    
    @given(st.lists(st.booleans(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_image_query_result_consistency(self, has_images_list: list):
        """
        **Feature: performance-optimization, Property 4: 이미지 조회 결과 일관성**
        **Validates: Requirements 6.2, 6.3**
        
        *For any* 매물 목록 조회에 대해, 이미지가 있는 매물은 이미지 URL 배열을 반환하고,
        이미지가 없는 매물은 빈 배열을 반환해야 한다.
        """
        from nodes.sql_search_node import search
        from common.db_pool import PostgresPool
        
        # 테스트 데이터 생성 - 각 매물에 대해 이미지 유무 결정
        mock_rows = []
        for i, has_images in enumerate(has_images_list):
            land_id = i + 1
            land_num = f"test_{land_id}"
            
            # 이미지가 있는 경우 URL 배열, 없는 경우 빈 배열
            if has_images:
                images = [f"http://example.com/img_{land_id}_{j}.jpg" for j in range(1, 4)]
            else:
                images = []
            
            mock_rows.append({
                'land_id': land_id,
                'land_num': land_num,
                'building_type': '아파트',
                'address': f'서울시 강남구 테스트동 {land_id}',
                'deal_type': '월세',
                'deposit': 5000,
                'monthly_rent': 50,
                'jeonse_price': None,
                'sale_price': None,
                'url': f'http://example.com/land/{land_id}',
                'trade_info': {'거래유형': '월세', '보증금': '5000만원', '월세': '50만원', '매매가': '-'},
                'listing_info': {},
                'additional_options': {},
                'description': '테스트 매물',
                'agent_info': {},
                'like_count': 0,
                'view_count': 0,
                'distance_unit': 'm',
                'images': images
            })
        
        # Mock 설정
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_rows
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # graph_results 생성 (Neo4j 결과 시뮬레이션)
        graph_results = [{'p.id': f"test_{i+1}"} for i in range(len(has_images_list))]
        
        state = {
            'question': '강남구 매물 보여줘',
            'graph_results': graph_results,
            'sql_results': []
        }
        
        with patch.object(PostgresPool, 'get_connection', return_value=mock_conn):
            with patch.object(PostgresPool, 'return_connection'):
                result_state = search(state)
        
        sql_results = result_state.get('sql_results', [])
        
        # Property 검증: 각 매물의 이미지 결과 일관성 확인
        for i, (has_images, result) in enumerate(zip(has_images_list, sql_results)):
            images = result.get('images', None)
            
            # 이미지 필드는 항상 리스트여야 함
            assert isinstance(images, list), \
                f"매물 {i+1}: images 필드가 리스트가 아닙니다. 타입: {type(images)}"
            
            if has_images:
                # 이미지가 있는 매물은 비어있지 않은 배열 반환
                assert len(images) > 0, \
                    f"매물 {i+1}: 이미지가 있어야 하는데 빈 배열입니다."
                # 모든 이미지 URL이 문자열인지 확인
                for img_url in images:
                    assert isinstance(img_url, str), \
                        f"매물 {i+1}: 이미지 URL이 문자열이 아닙니다. 타입: {type(img_url)}"
            else:
                # 이미지가 없는 매물은 빈 배열 반환
                assert len(images) == 0, \
                    f"매물 {i+1}: 이미지가 없어야 하는데 {len(images)}개의 이미지가 있습니다."
    
    def test_empty_images_returns_empty_array(self):
        """이미지가 없는 매물은 빈 배열을 반환해야 함"""
        from nodes.sql_search_node import search
        from common.db_pool import PostgresPool
        
        mock_rows = [{
            'land_id': 1,
            'land_num': 'test_1',
            'building_type': '아파트',
            'address': '서울시 강남구',
            'deal_type': '월세',
            'deposit': 5000,
            'monthly_rent': 50,
            'jeonse_price': None,
            'sale_price': None,
            'url': 'http://example.com/land/1',
            'trade_info': {'거래유형': '월세', '보증금': '5000만원', '월세': '50만원', '매매가': '-'},
            'listing_info': {},
            'additional_options': {},
            'description': '테스트 매물',
            'agent_info': {},
            'like_count': 0,
            'view_count': 0,
            'distance_unit': 'm',
            'images': []  # 빈 배열
        }]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_rows
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        state = {
            'question': '강남구 매물',
            'graph_results': [{'p.id': 'test_1'}],
            'sql_results': []
        }
        
        with patch.object(PostgresPool, 'get_connection', return_value=mock_conn):
            with patch.object(PostgresPool, 'return_connection'):
                result_state = search(state)
        
        sql_results = result_state.get('sql_results', [])
        assert len(sql_results) == 1
        assert sql_results[0]['images'] == []
    
    def test_multiple_images_returns_array(self):
        """여러 이미지가 있는 매물은 이미지 URL 배열을 반환해야 함"""
        from nodes.sql_search_node import search
        from common.db_pool import PostgresPool
        
        expected_images = [
            'http://example.com/img1.jpg',
            'http://example.com/img2.jpg',
            'http://example.com/img3.jpg'
        ]
        
        mock_rows = [{
            'land_id': 1,
            'land_num': 'test_1',
            'building_type': '아파트',
            'address': '서울시 강남구',
            'deal_type': '월세',
            'deposit': 5000,
            'monthly_rent': 50,
            'jeonse_price': None,
            'sale_price': None,
            'url': 'http://example.com/land/1',
            'trade_info': {'거래유형': '월세', '보증금': '5000만원', '월세': '50만원', '매매가': '-'},
            'listing_info': {},
            'additional_options': {},
            'description': '테스트 매물',
            'agent_info': {},
            'like_count': 0,
            'view_count': 0,
            'distance_unit': 'm',
            'images': expected_images
        }]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_rows
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        state = {
            'question': '강남구 매물',
            'graph_results': [{'p.id': 'test_1'}],
            'sql_results': []
        }
        
        with patch.object(PostgresPool, 'get_connection', return_value=mock_conn):
            with patch.object(PostgresPool, 'return_connection'):
                result_state = search(state)
        
        sql_results = result_state.get('sql_results', [])
        assert len(sql_results) == 1
        assert sql_results[0]['images'] == expected_images
        assert len(sql_results[0]['images']) == 3
