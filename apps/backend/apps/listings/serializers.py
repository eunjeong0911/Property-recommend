from rest_framework import serializers
from .models import Land, LandBroker, PriceClassificationResult
from .utils.price_utils import (
    parse_korean_price,
    format_price_in_manwon,
    extract_deposit_from_deal_text,
    extract_monthly_rent_from_deal_text,
    get_price_display,
    extract_area_pyeong,
    extract_area_supply,
    extract_area_exclusive,
    extract_total_floors,
)
import random


class BrokerSerializer(serializers.ModelSerializer):
    """중개업소 시리얼라이저"""
    id = serializers.IntegerField(source='landbroker_id')
    trust_grade = serializers.CharField(source='trust_grade_display', read_only=True)
    
    class Meta:
        model = LandBroker
        fields = [
            'id', 'office_name', 'representative', 'phone', 'address',
            'registration_number', 'trust_score', 'trust_grade',
            'trust_score_updated_at'
        ]


class PriceClassificationSerializer(serializers.ModelSerializer):
    """가격 분류 시리얼라이저"""
    class Meta:
        model = PriceClassificationResult
        fields = [
            'prediction_class',
            'prediction_label',
            'prediction_label_korean',
            'probability_underpriced',
            'probability_fair',
            'probability_overpriced'
        ]


class LandSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='land_id')
    title = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    temperature = serializers.SerializerMethodField()
    deposit = serializers.SerializerMethodField()
    monthly_rent = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    region = serializers.CharField(source='address')
    transaction_type = serializers.CharField(source='deal_type')
    
    # Detail fields
    land_num = serializers.CharField()
    address = serializers.CharField()
    building_type = serializers.CharField()
    floor = serializers.SerializerMethodField()
    room_count = serializers.SerializerMethodField()
    area_supply = serializers.SerializerMethodField()
    area_exclusive = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()
    parking = serializers.SerializerMethodField()
    move_in_date = serializers.SerializerMethodField()
    maintenance_fee = serializers.SerializerMethodField()
    heating_method = serializers.SerializerMethodField()
    elevator = serializers.SerializerMethodField()
    description = serializers.CharField()
    
    # 중개업소 정보
    broker = BrokerSerializer(source='landbroker', read_only=True)
    
    # 가격 분류 정보
    price_prediction = serializers.SerializerMethodField()

    class Meta:
        model = Land
        fields = [
            'id', 
            'title', 
            'image', 
            'images',
            'temperature', 
            'deposit', 
            'monthly_rent', 
            'price',
            'region',
            'transaction_type',
            'building_type',
            'land_num',
            'address',
            'floor',
            'room_count',
            'area_supply',
            'area_exclusive',
            'direction',
            'parking',
            'move_in_date',
            'maintenance_fee',
            'heating_method',
            'elevator',
            'description',
            'broker',
            'price_prediction'
        ]

    def get_title(self, obj):
        """매물 제목 생성"""
        if obj.listing_info and isinstance(obj.listing_info, dict):
            building_form = obj.listing_info.get('건물형태', obj.building_type)
            area = obj.listing_info.get('전용/공급면적', '')
            if area:
                # 사전 컴파일된 정규식 사용
                pyeong = extract_area_pyeong(area)
                if pyeong:
                    area = pyeong
            return f"{building_form} {area}".strip() or obj.land_num
        return obj.land_num

    def get_image(self, obj):
        """첫 번째 이미지 반환"""
        if obj.images and isinstance(obj.images, list) and len(obj.images) > 0:
            return obj.images[0]
        return None

    def get_images(self, obj):
        """모든 이미지 반환"""
        if obj.images and isinstance(obj.images, list) and len(obj.images) > 0:
            return obj.images
        return []

    def get_temperature(self, obj):
        """부동산 온도 (임시로 랜덤 값, 추후 실제 계산 로직으로 대체)"""
        # TODO: 실제 온도 계산 로직 구현
        return round(random.uniform(30.0, 45.0), 1)

    def get_deposit(self, obj):
        """보증금 추출 - price_utils 사용"""
        deal_text = ''
        if obj.trade_info and isinstance(obj.trade_info, dict):
            deal_text = obj.trade_info.get('거래방식', '')
        
        return extract_deposit_from_deal_text(deal_text, obj.deal_type or '')

    def get_monthly_rent(self, obj):
        """월세 추출 - price_utils 사용"""
        deal_text = ''
        if obj.trade_info and isinstance(obj.trade_info, dict):
            deal_text = obj.trade_info.get('거래방식', '')
        
        return extract_monthly_rent_from_deal_text(deal_text, obj.deal_type or '')

    def get_price(self, obj):
        """가격 포맷팅 (만원 단위) - price_utils 사용"""
        return get_price_display(obj)

    def _get_listing_info_field(self, obj, field_name):
        """listing_info에서 필드 추출"""
        if obj.listing_info and isinstance(obj.listing_info, dict):
            return obj.listing_info.get(field_name, '-')
        return '-'

    def get_floor(self, obj):
        """층수 정보"""
        return self._get_listing_info_field(obj, '해당층/전체층')
    
    def get_room_count(self, obj):
        """방/욕실 개수"""
        return self._get_listing_info_field(obj, '방/욕실개수')
    
    def get_area_supply(self, obj):
        """공급면적 - price_utils 사용"""
        area = self._get_listing_info_field(obj, '전용/공급면적')
        return extract_area_supply(area)
    
    def get_area_exclusive(self, obj):
        """전용면적 - price_utils 사용"""
        area = self._get_listing_info_field(obj, '전용/공급면적')
        return extract_area_exclusive(area)
    
    def get_direction(self, obj):
        """방향"""
        return self._get_listing_info_field(obj, '주실기준/방향')
    
    def get_parking(self, obj):
        """주차 정보"""
        return self._get_listing_info_field(obj, '주차')
    
    def get_move_in_date(self, obj):
        """입주가능일"""
        if obj.trade_info and isinstance(obj.trade_info, dict):
            return obj.trade_info.get('입주가능일', '-')
        return '-'
    
    def get_maintenance_fee(self, obj):
        """관리비"""
        if obj.trade_info and isinstance(obj.trade_info, dict):
            return obj.trade_info.get('관리비', '-')
        return '-'
    
    def get_heating_method(self, obj):
        """난방방식"""
        return self._get_listing_info_field(obj, '난방방식')
    
    def get_elevator(self, obj):
        """엘리베이터 (층수 정보에서 유추) - price_utils 사용"""
        floor_info = self._get_listing_info_field(obj, '해당층/전체층')
        total_floors = extract_total_floors(floor_info)
        if total_floors is not None:
            return '있음' if total_floors >= 5 else '없음'
        return '-'
    
    def get_price_prediction(self, obj):
        """가격 분류 정보 조회 (캐싱 적용)"""
        # context에 캐시된 price_predictions 사용 (N+1 쿼리 방지)
        price_cache = self.context.get('price_predictions')
        
        if price_cache is not None:
            # 캐시에서 조회
            price_class = price_cache.get(obj.land_num)
            if price_class:
                return {
                    'prediction_class': price_class.prediction_class,
                    'prediction_label': price_class.prediction_label,
                    'prediction_label_korean': price_class.prediction_label_korean,
                    'probability_underpriced': price_class.probability_underpriced,
                    'probability_fair': price_class.probability_fair,
                    'probability_overpriced': price_class.probability_overpriced
                }
            return None
        
        # 캐시가 없으면 개별 쿼리 (폴백)
        try:
            price_class = PriceClassificationResult.objects.filter(land_num=obj.land_num).first()
            if price_class:
                return PriceClassificationSerializer(price_class).data
        except Exception as e:
            print(f"Error fetching price classification: {e}")
        return None
    
