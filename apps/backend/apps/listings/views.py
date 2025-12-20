from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Land, PriceClassificationResult
from .serializers import LandSerializer
from .utils.price_utils import get_price_display
from .neo4j_client import Neo4jClient

class LandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Land.objects.all()
    serializer_class = LandSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['land_num', 'address']

    def get_queryset(self):
        # with_images() + select_related로 N+1 쿼리 방지
        queryset = Land.objects.with_images().select_related('landbroker')
        
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
    
    def get_serializer_context(self):
        """Serializer context에 price_predictions 캐시 추가 (N+1 쿼리 방지)"""
        context = super().get_serializer_context()
        
        # 모든 price_classification을 한 번에 조회하여 캐싱
        price_predictions = PriceClassificationResult.objects.all()
        context['price_predictions'] = {p.land_num: p for p in price_predictions}
        
        return context
    
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
        
        # Neo4j 연결 (싱글톤 드라이버 사용)
        driver = Neo4jClient.get_driver()
        
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
                        
                        # 가격 정보 직접 계산 (price_utils 사용)
                        location_data['price'] = get_price_display(land)
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
        except Exception as e:
            # 에러 발생 시에도 드라이버는 종료하지 않음 (싱글톤 재사용)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Neo4j 쿼리 실행 중 오류: {e}")
            return Response({
                'count': 0,
                'results': [],
                'error': str(e)
            }, status=500)
    
    @action(detail=True, methods=['get'])
    def nearby_facilities(self, request, pk=None):
        """
        매물 주변 시설 정보를 Neo4j에서 가져옵니다.
        
        Returns:
            - medical: 의료시설 개수
            - convenience: 편의시설 개수
            - transportation: 대중교통 개수
            - safety: 안전시설(CCTV) 개수
        """
        try:
            land = Land.objects.get(land_id=pk)
            land_num = land.land_num
        except Land.DoesNotExist:
            return Response({'error': f'매물 ID {pk}를 찾을 수 없습니다.'}, status=404)
        
        # Neo4j 연결
        driver = Neo4jClient.get_driver()
        
        try:
            with driver.session() as session:
                # 매물 주변 시설 개수 조회 쿼리
                # 대중교통: 지하철역, 버스정류장
                # 의료시설: 병원, 약국, 종합병원
                # 안전시설: CCTV, 경찰서, 소방서, 비상벨
                # 편의시설: 편의점
                query = """
                MATCH (p:Property {id: $land_num})
                OPTIONAL MATCH (p)-[:NEAR]->(subway:Subway)
                OPTIONAL MATCH (p)-[:NEAR]->(bus:Bus)
                OPTIONAL MATCH (p)-[:NEAR]->(hospital:Hospital)
                OPTIONAL MATCH (p)-[:NEAR]->(pharmacy:Pharmacy)
                OPTIONAL MATCH (p)-[:NEAR]->(general_hospital:GeneralHospital)
                OPTIONAL MATCH (p)-[:NEAR]->(cctv:CCTV)
                OPTIONAL MATCH (p)-[:NEAR]->(police:Police)
                OPTIONAL MATCH (p)-[:NEAR]->(fire:Fire)
                OPTIONAL MATCH (p)-[:NEAR]->(emergency:Emergency)
                OPTIONAL MATCH (p)-[:NEAR]->(convenience:ConvenienceStore)
                RETURN 
                    count(DISTINCT subway) + count(DISTINCT bus) as transport_count,
                    count(DISTINCT hospital) + count(DISTINCT pharmacy) + count(DISTINCT general_hospital) as medical_count,
                    count(DISTINCT cctv) + count(DISTINCT police) + count(DISTINCT fire) + count(DISTINCT emergency) as safety_count,
                    count(DISTINCT convenience) as convenience_count,
                    p.latitude as latitude,
                    p.longitude as longitude
                """
                
                result = session.run(query, {"land_num": land_num})
                record = result.single()
                
                if record:
                    facilities = {
                        'medical': {
                            'count': record.get('medical_count', 0),
                            'name': '의료시설',
                            'icon': '/assets/map_pin/medical_facilities.png',
                        },
                        'convenience': {
                            'count': record.get('convenience_count', 0),
                            'name': '편의시설',
                            'icon': '/assets/map_pin/convenience.png',
                        },
                        'transportation': {
                            'count': record.get('transport_count', 0),
                            'name': '대중교통',
                            'icon': '/assets/map_pin/bus.png',
                        },
                        'safety': {
                            'count': record.get('safety_count', 0),
                            'name': 'CCTV',
                            'icon': '/assets/map_pin/cctv.png',
                        },
                        'location': {
                            'latitude': record.get('latitude'),
                            'longitude': record.get('longitude')
                        }
                    }
                    return Response(facilities)
                else:
                    return Response({
                        'medical': {'count': 0, 'name': '의료시설', 'icon': '/assets/map_pin/medical_facilities.png'},
                        'convenience': {'count': 0, 'name': '편의시설', 'icon': '/assets/map_pin/convenience.png'},
                        'transportation': {'count': 0, 'name': '대중교통', 'icon': '/assets/map_pin/bus.png'},
                        'safety': {'count': 0, 'name': 'CCTV', 'icon': '/assets/map_pin/cctv.png'},
                        'location': None
                    })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Neo4j nearby_facilities 쿼리 오류: {e}")
            return Response({
                'error': str(e),
                'medical': {'count': 0, 'name': '의료시설', 'icon': '/assets/map_pin/medical_facilities.png'},
                'convenience': {'count': 0, 'name': '편의시설', 'icon': '/assets/map_pin/convenience.png'},
                'transportation': {'count': 0, 'name': '대중교통', 'icon': '/assets/map_pin/bus.png'},
                'safety': {'count': 0, 'name': 'CCTV', 'icon': '/assets/map_pin/cctv.png'},
                'location': None
            }, status=500)

