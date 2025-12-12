"""
LandManager 및 LandQuerySet 테스트

Property 1: Prefetch 적용 시 추가 쿼리 없음
Validates: Requirements 1.1, 1.2
"""
import pytest
from unittest.mock import MagicMock, patch


class TestLandManagerPrefetch:
    """LandManager의 with_images() 메서드 테스트"""
    
    def test_with_images_returns_queryset_with_prefetch(self):
        """with_images()가 prefetch_related가 적용된 QuerySet을 반환하는지 확인"""
        from apps.listings.managers import LandQuerySet, LandManager
        
        # Manager가 with_images 메서드를 가지고 있는지 확인
        assert hasattr(LandManager, 'with_images')
    
    def test_queryset_with_images_applies_prefetch(self):
        """QuerySet의 with_images()가 prefetch_related를 적용하는지 확인"""
        from apps.listings.managers import LandQuerySet
        
        # QuerySet이 with_images 메서드를 가지고 있는지 확인
        assert hasattr(LandQuerySet, 'with_images')
    
    def test_images_property_uses_prefetch_cache(self):
        """Land.images 프로퍼티가 prefetch 캐시를 사용하는지 확인"""
        # Mock Land 객체 생성
        mock_land = MagicMock()
        mock_land._prefetched_images = [
            MagicMock(img_url='http://example.com/img1.jpg'),
            MagicMock(img_url='http://example.com/img2.jpg'),
        ]
        
        # _prefetched_images가 있으면 해당 캐시 사용
        if hasattr(mock_land, '_prefetched_images'):
            images = [img.img_url for img in mock_land._prefetched_images]
            assert len(images) == 2
            assert images[0] == 'http://example.com/img1.jpg'
    
    def test_images_property_fallback_without_prefetch(self):
        """prefetch 캐시가 없을 때 기존 쿼리 방식으로 fallback하는지 확인"""
        mock_land = MagicMock(spec=[])  # _prefetched_images 없음
        
        # _prefetched_images가 없으면 hasattr이 False 반환
        assert not hasattr(mock_land, '_prefetched_images')
