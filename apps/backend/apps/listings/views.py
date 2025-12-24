from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Land, PriceClassificationResult
from .serializers import LandSerializer
from .utils.price_utils import get_price_display
from .neo4j_client import Neo4jClient
import logging

logger = logging.getLogger(__name__)

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
            # Neo4j의 Property 노드 id는 land_num과 매칭됨
            land_id_for_neo4j = str(land.land_num)
        except Land.DoesNotExist:
            return Response({'error': f'매물 ID {pk}를 찾을 수 없습니다.'}, status=404)
        
        # Neo4j 연결
        driver = Neo4jClient.get_driver()
        
        try:
            with driver.session() as session:
                # 매물 주변 시설 개수 조회 쿼리
                # 실제 Neo4j 스키마에 맞게 수정:
                # - 관계: NEAR_SUBWAY, NEAR_BUS, NEAR_HOSPITAL 등
                # - 노드: SubwayStation, BusStation, Hospital, Convenience 등
                query = """
                MATCH (p:Property {id: $land_num})
                OPTIONAL MATCH (p)-[:NEAR_SUBWAY]->(subway:SubwayStation)
                OPTIONAL MATCH (p)-[:NEAR_BUS]->(bus:BusStation)
                OPTIONAL MATCH (p)-[:NEAR_HOSPITAL]->(hospital:Hospital)
                OPTIONAL MATCH (p)-[:NEAR_PHARMACY]->(pharmacy:Pharmacy)
                OPTIONAL MATCH (p)-[:NEAR_CCTV]->(cctv:CCTV)
                OPTIONAL MATCH (p)-[:NEAR_POLICE]->(police:PoliceStation)
                OPTIONAL MATCH (p)-[:NEAR_FIRE]->(fire:FireStation)
                OPTIONAL MATCH (p)-[:NEAR_BELL]->(bell:EmergencyBell)
                OPTIONAL MATCH (p)-[:NEAR_CONVENIENCE]->(conv:Store:Convenience)
                RETURN 
                    count(DISTINCT subway) + count(DISTINCT bus) as transport_count,
                    count(DISTINCT hospital) + count(DISTINCT pharmacy) as medical_count,
                    count(DISTINCT cctv) + count(DISTINCT police) + count(DISTINCT fire) + count(DISTINCT bell) as safety_count,
                    count(DISTINCT conv) as convenience_count,
                    p.latitude as latitude,
                    p.longitude as longitude
                """
                
                logger.info(f"Neo4j 쿼리 실행: land_id={land_id_for_neo4j}")
                result = session.run(query, {"land_num": land_id_for_neo4j})
                record = result.single()
                
                if record:
                    logger.info(f"Neo4j 결과: transport={record.get('transport_count')}, medical={record.get('medical_count')}, safety={record.get('safety_count')}, convenience={record.get('convenience_count')}")
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
                    logger.warning(f"Neo4j에서 land_id={land_id_for_neo4j}에 대한 데이터를 찾을 수 없습니다.")
                    return Response({
                        'medical': {'count': 0, 'name': '의료시설', 'icon': '/assets/map_pin/medical_facilities.png'},
                        'convenience': {'count': 0, 'name': '편의시설', 'icon': '/assets/map_pin/convenience.png'},
                        'transportation': {'count': 0, 'name': '대중교통', 'icon': '/assets/map_pin/bus.png'},
                        'safety': {'count': 0, 'name': 'CCTV', 'icon': '/assets/map_pin/cctv.png'},
                        'location': None
                    })
        except Exception as e:
            import traceback
            logger.error(f"Neo4j nearby_facilities 쿼리 오류 (land_id={land_id_for_neo4j}): {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # 500 에러 대신 200으로 빈 데이터 반환
            return Response({
                'medical': {'count': 0, 'name': '의료시설', 'icon': '/assets/map_pin/medical_facilities.png'},
                'convenience': {'count': 0, 'name': '편의시설', 'icon': '/assets/map_pin/convenience.png'},
                'transportation': {'count': 0, 'name': '대중교통', 'icon': '/assets/map_pin/bus.png'},
                'safety': {'count': 0, 'name': 'CCTV', 'icon': '/assets/map_pin/cctv.png'},
                'location': None
            }, status=200)
    
    @action(detail=True, methods=['get'])
    def facility_locations(self, request, pk=None):
        """
        매물 주변 특정 카테고리의 시설 위치 정보를 Neo4j에서 가져옵니다.
        
        Query Parameters:
            - category: 시설 카테고리 (transportation, medical, convenience, safety)
        
        Returns:
            - List of facilities with name, latitude, longitude, type
        """
        category = request.query_params.get('category', None)
        
        if not category:
            return Response({'error': 'category 파라미터가 필요합니다.'}, status=400)
        
        try:
            land = Land.objects.get(land_id=pk)
            # Neo4j의 Property 노드 id는 land_num과 매칭됨
            land_id_for_neo4j = str(land.land_num)
        except Land.DoesNotExist:
            return Response({'error': f'매물 ID {pk}를 찾을 수 없습니다.'}, status=404)
        
        # Neo4j 연결
        driver = Neo4jClient.get_driver()
        
        try:
            with driver.session() as session:
                # 카테고리별 노드 타입과 관계 매핑 (실제 Neo4j 스키마)
                category_mapping = {
                    'transportation': [
                        ('SubwayStation', 'NEAR_SUBWAY'),
                        ('BusStation', 'NEAR_BUS')
                    ],
                    'medical': [
                        ('Hospital', 'NEAR_HOSPITAL'),
                        ('Pharmacy', 'NEAR_PHARMACY')
                    ],
                    'convenience': [
                        ('Store', 'NEAR_CONVENIENCE')
                    ],
                    'safety': [
                        ('CCTV', 'NEAR_CCTV'),
                        ('PoliceStation', 'NEAR_POLICE'),
                        ('FireStation', 'NEAR_FIRE'),
                        ('EmergencyBell', 'NEAR_BELL')
                    ]
                }
                
                if category not in category_mapping:
                    return Response({'error': f'유효하지 않은 카테고리: {category}'}, status=400)
                
                node_rel_pairs = category_mapping[category]
                facilities = []
                
                # 각 노드 타입과 관계별로 쿼리 실행
                for node_type, rel_type in node_rel_pairs:
                    query = f"""
                    MATCH (p:Property {{id: $land_num}})-[:{rel_type}]->(f:{node_type})
                    WHERE f.latitude IS NOT NULL AND f.longitude IS NOT NULL
                    RETURN f.name as name, 
                           f.latitude as latitude, 
                           f.longitude as longitude,
                           '{node_type}' as type
                    LIMIT 50
                    """
                    
                    result = session.run(query, {"land_num": land_id_for_neo4j})
                    
                    for record in result:
                        facilities.append({
                            'name': record.get('name', ''),
                            'latitude': record.get('latitude'),
                            'longitude': record.get('longitude'),
                            'type': record.get('type'),
                            'category': category
                        })
                
                return Response({
                    'category': category,
                    'count': len(facilities),
                    'facilities': facilities
                })
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Neo4j facility_locations 쿼리 오류: {e}")
            return Response({
                'error': str(e),
                'category': category,
                'count': 0,
                'facilities': []
            }, status=500)

