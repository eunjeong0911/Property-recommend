from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Land, PriceClassificationResult
from .serializers import LandSerializer, LandListSerializer
from .utils.price_utils import get_price_display
from .neo4j_client import Neo4jClient
import logging

logger = logging.getLogger(__name__)

class LandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Land.objects.all()
    # serializers.py의 LandListSerializer와 LandSerializer를 동적으로 선택

    def get_serializer_class(self):
        if self.action == 'list': # 목록 조회 API
            return LandListSerializer # 목록 조회 시리얼라이저
        return LandSerializer # 개별 조회 시리얼라이저
    filter_backends = [filters.SearchFilter]
    search_fields = ['land_num', 'address']

    def get_queryset(self):
        # with_images() + select_related로 N+1 쿼리 방지
        # price_predictions도 미리 로딩 (N+1 방지)
        # N+1 쿼리 방지: 이미지, 중개업소, 가격 정보를 한 번에 조회
        queryset = Land.objects.with_images().select_related('landbroker').prefetch_related('price_predictions')
        
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
                # 최적화: 이미 생성된 관계 개수를 직접 집계
                query = """
                MATCH (p:Property {id: $land_num})
                OPTIONAL MATCH (p)-[r]->()
                WHERE type(r) STARTS WITH 'NEAR_'
                WITH p, type(r) as rel_type, count(r) as rel_count
                RETURN 
                    p.latitude as latitude,
                    p.longitude as longitude,
                    sum(CASE WHEN rel_type IN ['NEAR_SUBWAY', 'NEAR_BUS'] THEN rel_count ELSE 0 END) as transport_count,
                    sum(CASE WHEN rel_type IN ['NEAR_HOSPITAL', 'NEAR_PHARMACY'] THEN rel_count ELSE 0 END) as medical_count,
                    sum(CASE WHEN rel_type IN ['NEAR_CCTV', 'NEAR_POLICE', 'NEAR_FIRE', 'NEAR_BELL'] THEN rel_count ELSE 0 END) as safety_count,
                    sum(CASE WHEN rel_type = 'NEAR_CONVENIENCE' THEN rel_count ELSE 0 END) as convenience_count
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
                # 안전 시설은 노드별로 다른 속성 사용:
                # - CCTV: purpose (설치목적), address
                # - EmergencyBell: location_desc (설치위치), address
                # - PoliceStation: name
                # - FireStation: name
                category_mapping = {
                    'transportation': [
                        ('SubwayStation', 'NEAR_SUBWAY', 'f.name'),
                        ('BusStation', 'NEAR_BUS', 'f.name')
                    ],
                    'medical': [
                        ('Hospital', 'NEAR_HOSPITAL', 'f.name'),
                        ('Pharmacy', 'NEAR_PHARMACY', 'f.name')
                    ],
                    'convenience': [
                        ('Store', 'NEAR_CONVENIENCE', 'f.name')
                    ],
                    'safety': [
                        ('CCTV', 'NEAR_CCTV', "COALESCE(f.purpose, 'CCTV') + ' (' + COALESCE(SPLIT(f.address, ' ')[-1], '주변') + ')'"),
                        ('PoliceStation', 'NEAR_POLICE', 'f.name'),
                        ('FireStation', 'NEAR_FIRE', 'f.name'),
                        ('EmergencyBell', 'NEAR_BELL', "'비상벨 (' + COALESCE(f.location_desc, SPLIT(f.address, ' ')[-1], '주변') + ')'")
                    ]
                }
                
                if category not in category_mapping:
                    return Response({'error': f'유효하지 않은 카테고리: {category}'}, status=400)
                
                node_rel_pairs = category_mapping[category]
                facilities = []
                
                # 각 노드 타입과 관계별로 쿼리 실행
                for node_type, rel_type, name_expr in node_rel_pairs:
                    query = f"""
                    MATCH (p:Property {{id: $land_num}})-[:{rel_type}]->(f:{node_type})
                    WHERE f.latitude IS NOT NULL AND f.longitude IS NOT NULL
                    RETURN {name_expr} as name, 
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
    
    @action(detail=True, methods=['get'])
    def similar_listings(self, request, pk=None):
        """
        현재 매물과 유사한 매물 top 3 반환 (온도 기반 content-based filtering)
        
        Algorithm:
        1. 현재 매물의 온도 벡터 가져오기
        2. 같은 지역(행정동) 매물 필터링
        3. A등급 중개사 매물 필터링
        4. 같은 거래유형 매물 필터링
        5. 가격 범위 필터링 (±30% 범위)
        6. 거리 기준 오름차순 정렬 후 top 3 반환
        """
        try:
            # 현재 매물 조회
            current_land = Land.objects.get(land_id=pk)
        except Land.DoesNotExist:
            return Response({'error': f'매물 ID {pk}를 찾을 수 없습니다.'}, status=404)
        
        # 현재 매물의 온도 데이터 가져오기
        from .utils.temperature_utils import get_land_temperatures, get_bulk_land_temperatures
        current_temps = get_land_temperatures(current_land.land_num)
        
        # 온도 벡터 생성 (5차원)
        current_vector = [
            current_temps.get('safety', 36.5),
            current_temps.get('convenience', 36.5),
            current_temps.get('pet', 36.5),
            current_temps.get('traffic', 36.5),
            current_temps.get('culture', 36.5)
        ]
        
        # 지역(행정동) 추출
        current_dong = None
        if current_land.address:
            import re
            # "서울특별시 강남구 역삼동" 형태에서 "역삼동" 추출
            # 또는 "서울특별시 강남구 역삼1동" 같은 형태도 지원
            match = re.search(r'([가-힣]+\d*동)', current_land.address)
            if match:
                current_dong = match.group(1)
        
        # 후보 매물을 신뢰도 등급별로 수집 (A → B → C 순서로 fallback)
        trust_grades = ['A', 'B', 'C']
        candidates = []
        
        for grade in trust_grades:
            # 기본 필터링: 같은 행정동 + 특정 등급 중개사 (자기 자신 제외)
            candidate_queryset = Land.objects.exclude(land_id=current_land.land_id).select_related('landbroker')
            
            if current_dong:
                candidate_queryset = candidate_queryset.filter(address__icontains=current_dong)
            
            # 현재 등급 중개사 매물 필터링
            candidate_queryset = candidate_queryset.filter(landbroker__trust_score=grade)
            
            # 거래유형 필터링 (같은 거래유형만)
            if current_land.deal_type:
                candidate_queryset = candidate_queryset.filter(deal_type=current_land.deal_type)
            
            # 가격 범위 필터링 (±30% 범위)
            # 거래유형에 따라 적절한 가격 컬럼 사용
            if current_land.deal_type:
                deal_type = current_land.deal_type.lower()
                price_margin = 0.3  # ±30%
                
                if '월세' in deal_type or '단기임대' in deal_type:
                    # 월세/단기임대: 보증금 + 월세*100 기준
                    current_price = (current_land.deposit or 0) + (current_land.monthly_rent or 0) * 100
                    if current_price > 0:
                        min_price = current_price * (1 - price_margin)
                        max_price = current_price * (1 + price_margin)
                        # 후보 매물의 환산 가격 계산 후 필터링 (Django ORM으로는 복잡하므로 나중에 Python에서 필터링)
                elif '전세' in deal_type:
                    # 전세: 전세가 기준
                    current_price = current_land.jeonse_price or 0
                    if current_price > 0:
                        min_price = current_price * (1 - price_margin)
                        max_price = current_price * (1 + price_margin)
                        candidate_queryset = candidate_queryset.filter(
                            jeonse_price__gte=min_price,
                            jeonse_price__lte=max_price
                        )
                elif '매매' in deal_type:
                    # 매매: 매매가 기준
                    current_price = current_land.sale_price or 0
                    if current_price > 0:
                        min_price = current_price * (1 - price_margin)
                        max_price = current_price * (1 + price_margin)
                        candidate_queryset = candidate_queryset.filter(
                            sale_price__gte=min_price,
                            sale_price__lte=max_price
                        )
            
            # 최대 100개로 제한 (성능 최적화)
            grade_candidates = list(candidate_queryset[:100])
            
            # 월세/단기임대의 경우 Python에서 추가 필터링
            if current_land.deal_type and ('월세' in current_land.deal_type.lower() or '단기임대' in current_land.deal_type.lower()):
                current_price = (current_land.deposit or 0) + (current_land.monthly_rent or 0) * 100
                if current_price > 0:
                    min_price = current_price * (1 - 0.3)
                    max_price = current_price * (1 + 0.3)
                    grade_candidates = [
                        c for c in grade_candidates
                        if min_price <= ((c.deposit or 0) + (c.monthly_rent or 0) * 100) <= max_price
                    ]
            
            # 현재 등급에서 찾은 후보를 전체 후보 리스트에 추가
            candidates.extend(grade_candidates)
            
            # TOP 3 이상 확보되면 더 이상 낮은 등급 검색 안 함
            if len(candidates) >= 3:
                logger.info(f"매물 {pk}에 대해 {grade}등급 중개사 매물에서 {len(grade_candidates)}개 발견 (총 {len(candidates)}개)")
                break
            elif grade_candidates:
                logger.info(f"매물 {pk}에 대해 {grade}등급 중개사 매물에서 {len(grade_candidates)}개 발견, 다음 등급 검색 중...")
        
        if not candidates:
            logger.info(f"매물 {pk}에 대한 유사 매물 후보가 없습니다.")
            return Response({'results': []})
        
        # --- 최적화: 후보 매물들의 온도 데이터를 한 번에 조회 (Bulk Fetch) ---
        candidate_land_nums = [c.land_num for c in candidates]
        try:
            bulk_temps = get_bulk_land_temperatures(candidate_land_nums)
        except Exception as e:
            logger.error(f"Bulk temperature fetch failed: {e}")
            bulk_temps = {}

        # 각 후보 매물과의 유사도 계산
        import numpy as np
        similarities = []
        
        for candidate in candidates:
            # Bulk Data에서 조회
            candidate_temps = bulk_temps.get(candidate.land_num)
            if not candidate_temps:
                candidate_temps = get_land_temperatures(candidate.land_num) # Fallback

            candidate_vector = [
                candidate_temps.get('safety', 36.5),
                candidate_temps.get('convenience', 36.5),
                candidate_temps.get('pet', 36.5),
                candidate_temps.get('traffic', 36.5),
                candidate_temps.get('culture', 36.5)
            ]
            
            # 유클리드 거리 계산
            distance = np.linalg.norm(np.array(current_vector) - np.array(candidate_vector))
            
            similarities.append({
                'land': candidate,
                'distance': distance
            })
        
        # 거리 기준 오름차순 정렬 (거리가 가까울수록 유사)
        similarities.sort(key=lambda x: x['distance'])
        
        # Top 3 추출
        top_3 = similarities[:3]
        
        # Serializer로 변환
        similar_lands = [item['land'] for item in top_3]
        serializer = self.get_serializer(similar_lands, many=True)
        
        logger.info(f"매물 {pk}에 대한 유사 매물 {len(similar_lands)}개 반환")
        
        return Response({'results': serializer.data})


# =============================================================================
# Image Proxy View
# =============================================================================
import requests
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from urllib.parse import unquote


@require_http_methods(["GET"])
@cache_page(60 * 60 * 24)  # 24시간 캐시
def proxy_image(request):
    """
    외부 이미지를 프록시하여 반환
    
    Usage: /api/proxy-image/?url=https://ic.zigbang.com/ic/items/47382502/1.jpg
    """
    image_url = request.GET.get('url')
    
    if not image_url:
        return HttpResponseBadRequest("Missing 'url' parameter")
    
    # URL 디코딩
    image_url = unquote(image_url)
    
    # 허용된 도메인 체크 (보안)
    allowed_domains = ['ic.zigbang.com', 'img.peterpanz.com', 'cdn.peterpanz.com']
    if not any(domain in image_url for domain in allowed_domains):
        return HttpResponseBadRequest("Invalid image domain")
    
    try:
        # 외부 이미지 요청 (referrer 없이)
        response = requests.get(
            image_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            timeout=10,
            stream=True
        )
        response.raise_for_status()
        
        # 이미지 반환
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        django_response = HttpResponse(response.content, content_type=content_type)
        
        # 캐시 헤더 추가
        django_response['Cache-Control'] = 'public, max-age=86400'  # 24시간
        
        return django_response
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch image {image_url}: {str(e)}")
        return HttpResponseBadRequest(f"Failed to fetch image: {str(e)}")
