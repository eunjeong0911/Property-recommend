from django.db import models
from .managers import LandManager


class LandBroker(models.Model):
    """중개업소 모델"""
    landbroker_id = models.AutoField(primary_key=True)
    
    # 기본 정보
    office_name = models.CharField(max_length=200, blank=True, null=True, help_text='중개사명')
    representative = models.CharField(max_length=100, blank=True, null=True, help_text='대표자')
    phone = models.CharField(max_length=50, blank=True, null=True, help_text='전화번호')
    address = models.CharField(max_length=500, blank=True, null=True, help_text='주소')
    registration_number = models.CharField(
        max_length=100, 
        unique=True, 
        blank=True, 
        null=True,
        help_text='등록번호 (고유키)'
    )
    
    # 통계 정보 (trust_model 학습용)
    completed_deals = models.IntegerField(default=0, help_text='거래완료')
    registered_properties = models.IntegerField(default=0, help_text='등록매물')
    brokers_count = models.IntegerField(default=0, help_text='공인중개사수')
    assistants_count = models.IntegerField(default=0, help_text='중개보조원수')
    staff_count = models.IntegerField(default=0, help_text='일반직원수')
    
    # 지역 정보
    region = models.CharField(max_length=100, blank=True, null=True, help_text='지역명 (시군구)')
    registration_date = models.DateField(blank=True, null=True, help_text='등록일')
    
    # AI 예측 결과
    trust_score = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A등급 (우수)'),
            ('B', 'B등급 (보통)'),
            ('C', 'C등급 (주의)')
        ],
        blank=True,
        null=True,
        help_text='AI 모델 예측 신뢰도 등급'
    )
    trust_score_updated_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='신뢰도 점수 마지막 업데이트 시각'
    )
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'landbroker'
        ordering = ['-landbroker_id']
    
    def __str__(self):
        return f"{self.office_name or '정보없음'} ({self.registration_number or 'N/A'})"
    
    @property
    def trust_grade_display(self):
        """신뢰도 등급 한글 표시"""
        grade_map = {
            'A': '우수',
            'B': '보통',
            'C': '주의'
        }
        return grade_map.get(self.trust_score, '미평가')


class Land(models.Model):
    land_id = models.AutoField(primary_key=True)
    
    # 중개업소 정보 (ForeignKey로 연결)
    landbroker = models.ForeignKey(
        'LandBroker',
        on_delete=models.SET_NULL,
        db_column='landbroker_id',
        null=True,
        blank=True,
        related_name='properties',
        help_text='중개업소'
    )
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
    # agent_info 제거 - landbroker FK로 대체 (데이터 정규화)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    # 커스텀 Manager 적용
    objects = LandManager()

    class Meta:
        managed = False
        db_table = 'land'
        ordering = ['-land_id']

    def __str__(self):
        return self.land_num

    @property
    def images(self):
        """
        land_image 테이블에서 이미지 목록 가져오기
        prefetch 캐시가 있으면 사용, 없으면 쿼리 실행
        """
        # prefetch된 이미지가 있으면 사용 (N+1 방지)
        if hasattr(self, '_prefetched_images'):
            return [img.img_url for img in self._prefetched_images]
        # prefetch가 없으면 기존 방식으로 쿼리
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


class PriceClassificationResult(models.Model):
    """가격 분류 결과 모델"""
    id = models.AutoField(primary_key=True)
    land_num = models.CharField(max_length=20, db_column='매물번호', unique=True)
    land_url = models.TextField(db_column='매물_url', blank=True, null=True)
    
    # 예측 결과
    prediction_class = models.IntegerField(db_column='예측_클래스', help_text='예측 클래스 (0: 저렴, 1: 적정, 2: 비쌈)')
    prediction_label = models.CharField(max_length=50, db_column='예측_레이블', help_text='예측 레이블 (영문)')
    prediction_label_korean = models.CharField(max_length=50, db_column='예측_레이블_한글', help_text='예측 레이블 (한글)')
    
    # 확률
    probability_underpriced = models.FloatField(db_column='저렴_확률', help_text='저렴 확률')
    probability_fair = models.FloatField(db_column='적정_확률', help_text='적정 확률')
    probability_overpriced = models.FloatField(db_column='비쌈_확률', help_text='비쌈 확률')
    
    prediction_datetime = models.DateTimeField(db_column='예측_일시', blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'price_classification_results'
    
    def __str__(self):
        return f"{self.land_num} - {self.prediction_label_korean}"
