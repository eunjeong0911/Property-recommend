from rest_framework import serializers
from .models import Land
import random

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
    agent_info = serializers.SerializerMethodField()

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
            'agent_info'
        ]

    def get_title(self, obj):
        """매물 제목 생성"""
        if obj.listing_info and isinstance(obj.listing_info, dict):
            building_form = obj.listing_info.get('건물형태', obj.building_type)
            area = obj.listing_info.get('전용/공급면적', '')
            if area:
                # "30m2/38.68m2 (9.07평/11.7평)" 형식에서 평수만 추출
                import re
                match = re.search(r'\(([^)]+평)', area)
                if match:
                    area = match.group(1)
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
        """보증금 추출"""
        if obj.trade_info and isinstance(obj.trade_info, dict):
            deal_text = obj.trade_info.get('거래방식', '')
            import re
            
            # 전세: "전세   1억 2,500만원"
            if '전세' in deal_text:
                match = re.search(r'전세\s+(\d+억\s*\d*,?\d*만원|\d+,?\d*만원|\d+억)', deal_text)
                if match:
                    return self._parse_korean_price(match.group(1))
            
            # 월세: "월세   2,500만원/104만원" 형식 (보증금/월세)
            elif '월세' in deal_text:
                match = re.search(r'월세\s+(\d+억\s*\d*,?\d*만원|\d+,?\d*만원|\d+억)/(\d+,?\d*만원)', deal_text)
                if match:
                    return self._parse_korean_price(match.group(1))
            
            # 매매: "매매   4억 5,000만원"
            elif '매매' in deal_text:
                match = re.search(r'매매\s+(\d+억\s*\d*,?\d*만원|\d+,?\d*만원|\d+억)', deal_text)
                if match:
                    return self._parse_korean_price(match.group(1))
        
        # deal_type이 단기임대인 경우 (예: "단기임대   100만원/100만원")
        if obj.deal_type and '단기임대' in obj.deal_type:
            import re
            match = re.search(r'(\d+,?\d*만원)/(\d+,?\d*만원)', obj.deal_type)
            if match:
                return self._parse_korean_price(match.group(1))
        
        return 0

    def get_monthly_rent(self, obj):
        """월세 추출"""
        if obj.trade_info and isinstance(obj.trade_info, dict):
            deal_text = obj.trade_info.get('거래방식', '')
            import re
            
            # 월세: "월세   2,500만원/104만원" 형식
            if '월세' in deal_text:
                match = re.search(r'/(\d+,?\d*만원)', deal_text)
                if match:
                    return self._parse_korean_price(match.group(1))
        
        # deal_type이 단기임대인 경우
        if obj.deal_type and '단기임대' in obj.deal_type:
            import re
            match = re.search(r'/(\d+,?\d*만원)', obj.deal_type)
            if match:
                return self._parse_korean_price(match.group(1))
        
        return 0

    def _parse_korean_price(self, price_str):
        """한국어 가격 문자열을 숫자로 변환 (예: '1억 2,500만원' -> 125000000)"""
        import re
        price_str = price_str.replace(',', '').replace(' ', '')
        
        # 억 단위
        eok_match = re.search(r'(\d+)억', price_str)
        eok = int(eok_match.group(1)) * 100000000 if eok_match else 0
        
        # 만원 단위
        man_match = re.search(r'(\d+)만원', price_str)
        man = int(man_match.group(1)) * 10000 if man_match else 0
        
        return eok + man

    def _format_price_in_manwon(self, amount):
        """금액을 만원 단위로 포맷팅"""
        if amount == 0:
            return "0"
        
        manwon = amount // 10000
        eok = manwon // 10000
        remaining_manwon = manwon % 10000
        
        if eok > 0:
            if remaining_manwon > 0:
                return f"{eok}억 {remaining_manwon:,}만원"
            else:
                return f"{eok}억"
        else:
            return f"{remaining_manwon:,}만원"
    
    def get_price(self, obj):
        """가격 포맷팅 (만원 단위)"""
        deal_type = obj.deal_type or ''
        
        # 단기임대는 deal_type에 이미 가격이 포함되어 있음
        if '단기임대' in deal_type:
            return deal_type
        
        # 매매
        if deal_type == '매매':
            deposit = self.get_deposit(obj)
            if deposit > 0:
                return f"매매 {self._format_price_in_manwon(deposit)}"
            return '매매 (가격 미정)'
        
        # 전세
        if deal_type == '전세':
            deposit = self.get_deposit(obj)
            if deposit > 0:
                return f"전세 {self._format_price_in_manwon(deposit)}"
            return '전세 (가격 미정)'
        
        # 월세
        if deal_type == '월세':
            deposit = self.get_deposit(obj)
            monthly_rent = self.get_monthly_rent(obj)
            if monthly_rent > 0:
                return f"월세 {self._format_price_in_manwon(deposit)} / {self._format_price_in_manwon(monthly_rent)}"
            return '월세 (가격 미정)'
        
        # 기타 (trade_info에서 직접 가져오기)
        if obj.trade_info and isinstance(obj.trade_info, dict):
            deal_text = obj.trade_info.get('거래방식', '')
            if deal_text:
                return deal_text
        
        return '가격 정보 없음'

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
        """공급면적"""
        area = self._get_listing_info_field(obj, '전용/공급면적')
        if area and area != '-':
            # "30m2/38.68m2 (9.07평/11.7평)" 형식에서 공급면적 추출
            import re
            match = re.search(r'/([^(]+)\(', area)
            if match:
                return match.group(1).strip()
        return area
    
    def get_area_exclusive(self, obj):
        """전용면적"""
        area = self._get_listing_info_field(obj, '전용/공급면적')
        if area and area != '-':
            # "30m2/38.68m2 (9.07평/11.7평)" 형식에서 전용면적 추출
            import re
            match = re.search(r'(\d+\.?\d*m2)', area)
            if match:
                return match.group(1)
        return area
    
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
        """엘리베이터 (층수 정보에서 유추)"""
        floor_info = self._get_listing_info_field(obj, '해당층/전체층')
        if floor_info and floor_info != '-':
            import re
            match = re.search(r'/(\d+)층', floor_info)
            if match:
                total_floors = int(match.group(1))
                return '있음' if total_floors >= 5 else '없음'
        return '-'
    
    def get_agent_info(self, obj):
        """중개사 정보"""
        if obj.agent_info and isinstance(obj.agent_info, dict):
            return obj.agent_info
        # agent_info가 비어있으면 기본값 반환
        return {
            'name': '-',
            'phone': '-',
            'representative': '-',
            'address': '-'
        }
