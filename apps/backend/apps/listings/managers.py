"""
Land 모델용 커스텀 QuerySet 및 Manager

N+1 쿼리 문제를 해결하기 위해 prefetch_related를 자동 적용합니다.
Requirements: 1.1, 1.2
"""
from django.db import models
from django.apps import apps


class LandQuerySet(models.QuerySet):
    """Land 모델용 커스텀 QuerySet"""
    
    def with_images(self):
        """
        이미지를 prefetch하여 N+1 쿼리 문제를 해결합니다.
        
        Returns:
            QuerySet: 이미지가 prefetch된 QuerySet
        """
        # 순환 import 방지를 위해 apps.get_model 사용
        LandImage = apps.get_model('listings', 'LandImage')
        return self.select_related('landbroker').prefetch_related(
            models.Prefetch(
                'landimage_set',
                queryset=LandImage.objects.only('img_url', 'land_id'),
                to_attr='_prefetched_images'
            )
        )


class LandManager(models.Manager):
    """Land 모델용 커스텀 Manager"""
    
    def get_queryset(self):
        return LandQuerySet(self.model, using=self._db)
    
    def with_images(self):
        """이미지를 prefetch하여 반환"""
        return self.get_queryset().with_images()
