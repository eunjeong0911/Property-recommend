from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Land
from .serializers import LandSerializer
import os
from neo4j import GraphDatabase

class LandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Land.objects.all()
    serializer_class = LandSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['land_num', 'address']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 지역 필터 (부분 일치)
        address = self.request.query_params.get('address', None)
        if address:
            queryset = queryset.filter(address__icontains=address)
        
        # 거래유형 필터
        deal_type = self.request.query_params.get('deal_type', None)
        if deal_type:
            if deal_type == '단기임대':
                # 단기임대는 deal_type에 "단기임대"가 포함된 모든 매물
                queryset = queryset.filter(deal_type__icontains='단기임대')
            elif deal_type == '미분류':
                # 미분류는 deal_type이 NULL이거나 빈 문자열인 매물
                from django.db.models import Q
                queryset = queryset.filter(Q(deal_type__isnull=True) | Q(deal_type=''))
            else:
                # 매매, 전세, 월세는 정확히 일치
                queryset = queryset.filter(deal_type=deal_type)
        
        # 건물유형 필터 (정확히 일치)
        building_type = self.request.query_params.get('building_type', None)
        if building_type:
            queryset = queryset.filter(building_type=building_type)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def locations(self, request):
        """
        매물의 위도/경도 정보를 Neo4j에서 가져옵니다.
        
        Query Parameters:
        - limit: 반환할 최대 매물 수 (기본값: 100)
        - land_id: 특정 매물 ID (이 경우 해당 매물만 반환)
        - address: 주소 필터 (부분 일치)
        - deal_type: 거래유형 필터
        """
        limit = int(request.query_params.get('limit', 100))
        land_id_filter = request.query_params.get('land_id', None)
        address_filter = request.query_params.get('address', None)
        deal_type_filter = request.query_params.get('deal_type', None)
        
        # Neo4j 연결
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        
        try:
            # land_id를 land_num으로 변환 (PostgreSQL의 land_id → land_num)
            land_num = None
            if land_id_filter:
                try:
                    land = Land.objects.get(land_id=land_id_filter)
                    land_num = land.land_num
                except Land.DoesNotExist:
                    return Response({
                        'count': 0,
                        'results': [],
                        'error': f'매물 ID {land_id_filter}를 찾을 수 없습니다.'
                    })
            
            with driver.session() as session:
                # 기본 쿼리
                query = """
                MATCH (p:Property)
                WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
                """
                
                params = {"limit": limit}
                
                # 특정 매물 ID 필터 (land_num 사용)
                if land_num:
                    query += " AND p.id = $land_num"
                    params["land_num"] = land_num
                    params["limit"] = 1  # 특정 매물은 1개만
                
                # 주소 필터 추가
                if address_filter:
                    query += " AND p.address CONTAINS $address"
                    params["address"] = address_filter
                
                query += """
                RETURN p.id as id, 
                       p.latitude as latitude, 
                       p.longitude as longitude,
                       p.address as address,
                       p.name as name
                LIMIT $limit
                """
                
                result = session.run(query, params)
                neo4j_results = list(result)
                
                # 모든 land_num을 한 번에 수집
                land_nums = [record['id'] for record in neo4j_results]
                
                # PostgreSQL에서 한 번에 조회 (N+1 문제 해결)
                lands_queryset = Land.objects.filter(land_num__in=land_nums)
                
                # deal_type 필터 적용
                if deal_type_filter:
                    if deal_type_filter == '단기임대':
                        lands_queryset = lands_queryset.filter(deal_type__icontains='단기임대')
                    elif deal_type_filter == '미분류':
                        from django.db.models import Q
                        lands_queryset = lands_queryset.filter(Q(deal_type__isnull=True) | Q(deal_type=''))
                    else:
                        lands_queryset = lands_queryset.filter(deal_type=deal_type_filter)
                
                # land_num을 키로 하는 딕셔너리 생성
                lands_dict = {land.land_num: land for land in lands_queryset}
                
                locations = []
                for record in neo4j_results:
                    land_num_key = record['id']
                    land = lands_dict.get(land_num_key)
                    
                    # deal_type 필터가 있고 해당 매물이 없으면 스킵
                    if deal_type_filter and not land:
                        continue
                    
                    location_data = {
                        'id': record['id'],
                        'latitude': record['latitude'],
                        'longitude': record['longitude'],
                        'address': record['address'],
                        'name': record['name']
                    }
                    
                    if land:
                        location_data['deal_type'] = land.deal_type or '미분류'
                        location_data['building_type'] = land.building_type
                        
                        # 면적 추출
                        if land.listing_info and isinstance(land.listing_info, dict):
                            location_data['area'] = land.listing_info.get('전용/공급면적', '-')
                        else:
                            location_data['area'] = '-'
                        
                        # 가격 정보 직접 계산 (Serializer 인스턴스화 제거)
                        location_data['price'] = self._get_price_display(land)
                    else:
                        location_data['deal_type'] = '정보없음'
                        location_data['building_type'] = '-'
                        location_data['area'] = '-'
                        location_data['price'] = '-'
                    
                    locations.append(location_data)
                
                return Response({
                    'count': len(locations),
                    'results': locations
                })
        finally:
            driver.close()
    
    def _get_price_display(self, land):
        """가격 표시 문자열 생성 (Serializer 없이 직접 계산)"""
        deal_type = land.deal_type or ''
        
        if '단기임대' in deal_type:
            return deal_type
        
        trade_info = land.trade_info or {}
        deal_text = trade_info.get('거래방식', '') if isinstance(trade_info, dict) else ''
        
        import re
        
        def parse_price(price_str):
            if not price_str:
                return 0
            price_str = price_str.replace(',', '').replace(' ', '')
            eok_match = re.search(r'(\d+)억', price_str)
            eok = int(eok_match.group(1)) * 100000000 if eok_match else 0
            man_match = re.search(r'(\d+)만원', price_str)
            man = int(man_match.group(1)) * 10000 if man_match else 0
            return eok + man
        
        def format_price(amount):
            if amount == 0:
                return "0"
            manwon = amount // 10000
            eok = manwon // 10000
            remaining = manwon % 10000
            if eok > 0:
                return f"{eok}억 {remaining:,}만원" if remaining else f"{eok}억"
            return f"{remaining:,}만원"
        
        if deal_type == '매매':
            match = re.search(r'매매\s+(\d+억\s*\d*,?\d*만원|\d+,?\d*만원|\d+억)', deal_text)
            if match:
                return f"매매 {format_price(parse_price(match.group(1)))}"
            return '매매 (가격 미정)'
        
        if deal_type == '전세':
            match = re.search(r'전세\s+(\d+억\s*\d*,?\d*만원|\d+,?\d*만원|\d+억)', deal_text)
            if match:
                return f"전세 {format_price(parse_price(match.group(1)))}"
            return '전세 (가격 미정)'
        
        if deal_type == '월세':
            match = re.search(r'월세\s+(\d+억\s*\d*,?\d*만원|\d+,?\d*만원)/(\d+,?\d*만원)', deal_text)
            if match:
                deposit = format_price(parse_price(match.group(1)))
                monthly = format_price(parse_price(match.group(2)))
                return f"월세 {deposit} / {monthly}"
            return '월세 (가격 미정)'
        
        return deal_text if deal_text else '가격 정보 없음'
