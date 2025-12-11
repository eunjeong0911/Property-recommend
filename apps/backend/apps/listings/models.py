from django.db import models

class Land(models.Model):
    land_id = models.AutoField(primary_key=True)
    landbroker_id = models.IntegerField(blank=True, null=True)
    land_num = models.CharField(unique=True, max_length=20)
    building_type = models.CharField(max_length=20)
    address = models.CharField(max_length=200, blank=True, null=True)
    like_count = models.IntegerField(blank=True, null=True, default=0)
    view_count = models.IntegerField(blank=True, null=True, default=0)
    deal_type = models.CharField(max_length=50, blank=True, null=True)
    
    # 가격 컬럼 (만원 단위)
    deposit = models.IntegerField(blank=True, null=True, default=0)          # 보증금
    monthly_rent = models.IntegerField(blank=True, null=True, default=0)     # 월세
    jeonse_price = models.IntegerField(blank=True, null=True, default=0)     # 전세가
    sale_price = models.IntegerField(blank=True, null=True, default=0)       # 매매가
    
    url = models.TextField(blank=True, null=True)
    # images 제거 - land_image 테이블로 분리
    trade_info = models.JSONField(blank=True, null=True)
    listing_info = models.JSONField(blank=True, null=True)
    additional_options = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    agent_info = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'land'
        ordering = ['-land_id']

    def __str__(self):
        return self.land_num

    @property
    def images(self):
        """land_image 테이블에서 이미지 목록 가져오기"""
        return list(LandImage.objects.filter(land_id=self.land_id).values_list('img_url', flat=True))


class LandImage(models.Model):
    """부동산 이미지 (ERD 기반)"""
    landimage_id = models.AutoField(primary_key=True)
    land = models.ForeignKey(Land, on_delete=models.CASCADE, db_column='land_id')
    img_url = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'land_image'

    def __str__(self):
        return self.img_url

