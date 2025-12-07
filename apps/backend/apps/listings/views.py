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
                locations = []
                
                for record in result:
                    location_data = {
                        'id': record['id'],
                        'latitude': record['latitude'],
                        'longitude': record['longitude'],
                        'address': record['address'],
                        'name': record['name']
                    }
                    
                    # PostgreSQL에서 추가 정보 가져오기
                    try:
                        land = Land.objects.get(land_num=record['id'])
                        
                        # deal_type 필터 확인
                        if deal_type_filter:
                            if deal_type_filter == '단기임대':
                                if '단기임대' not in (land.deal_type or ''):
                                    continue
                            elif deal_type_filter == '미분류':
                                if land.deal_type:
                                    continue
                            else:
                                if land.deal_type != deal_type_filter:
                                    continue
                        
                        # 추가 정보 포함
                        location_data['deal_type'] = land.deal_type or '미분류'
                        location_data['building_type'] = land.building_type
                        
                        # 면적 추출
                        if land.listing_info and isinstance(land.listing_info, dict):
                            area = land.listing_info.get('전용/공급면적', '-')
                            location_data['area'] = area
                        else:
                            location_data['area'] = '-'
                        
                        # 가격 정보 (시리얼라이저 로직 재사용)
                        from .serializers import LandSerializer
                        serializer = LandSerializer(land)
                        location_data['price'] = serializer.data.get('price', '-')
                        
                    except Land.DoesNotExist:
                        # PostgreSQL에 없으면 기본값
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
