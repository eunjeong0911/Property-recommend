# =============================================================================
# Elasticsearch 검색 서비스 로직
# =============================================================================
#
# 역할: ES 쿼리 빌드 및 검색 로직 캡슐화
#
# Requirements:
# - 5.1: 키워드, 가격 범위, 위치 조건을 ES 쿼리로 변환
# - 5.2: 매물 ID 목록과 점수를 포함한 결과 반환
# - 5.3: ES 연결 오류 시 예외 로깅 및 빈 결과 반환
# - 5.4: bool 쿼리로 must, filter, should 조건 조합
# =============================================================================

import logging
from typing import List, Dict, Optional, Any
from .es_client import ESClient

logger = logging.getLogger(__name__)

# ES 인덱스 이름
ES_INDEX_NAME = "realestate_listings"


def build_es_query(
    keyword: Optional[str] = None,
    style_tags: Optional[List[str]] = None,
    min_deposit: Optional[int] = None,
    max_deposit: Optional[int] = None,
    min_rent: Optional[int] = None,
    max_rent: Optional[int] = None,
    location: Optional[Dict[str, Any]] = None,
    candidate_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    검색 조건을 ES bool 쿼리로 변환
    
    Args:
        keyword: 검색 키워드 (search_text 필드에서 검색)
        style_tags: 스타일 태그 목록 (정확 매칭)
        min_deposit: 최소 보증금
        max_deposit: 최대 보증금
        min_rent: 최소 월세
        max_rent: 최대 월세
        location: 위치 정보 {'lat': float, 'lng': float, 'radius': str}
        candidate_ids: Neo4j에서 추출한 후보 매물 ID 목록
    
    Returns:
        ES bool 쿼리 딕셔너리
    """
    query: Dict[str, Any] = {
        "bool": {
            "must": [],
            "filter": [],
            "should": []
        }
    }
    
    # 키워드 검색 (search_text 필드, nori 분석기 사용)
    if keyword:
        query["bool"]["must"].append({
            "match": {
                "search_text": {
                    "query": keyword,
                    "analyzer": "nori_analyzer"
                }
            }
        })
    
    # 스타일 태그 필터 (terms 쿼리로 OR 매칭)
    if style_tags:
        query["bool"]["filter"].append({
            "terms": {"style_tags": style_tags}
        })
    
    # 보증금 범위 필터
    if min_deposit is not None or max_deposit is not None:
        deposit_range: Dict[str, Any] = {"range": {"deposit": {}}}
        if min_deposit is not None:
            deposit_range["range"]["deposit"]["gte"] = min_deposit
        if max_deposit is not None:
            deposit_range["range"]["deposit"]["lte"] = max_deposit
        query["bool"]["filter"].append(deposit_range)
    
    # 월세 범위 필터
    if min_rent is not None or max_rent is not None:
        rent_range: Dict[str, Any] = {"range": {"monthly_rent": {}}}
        if min_rent is not None:
            rent_range["range"]["monthly_rent"]["gte"] = min_rent
        if max_rent is not None:
            rent_range["range"]["monthly_rent"]["lte"] = max_rent
        query["bool"]["filter"].append(rent_range)
    
    # 후보 ID 필터 (Neo4j 결과 기반)
    if candidate_ids:
        query["bool"]["filter"].append({
            "terms": {"land_num": candidate_ids}
        })
    
    # 위치 기반 필터 (geo_distance)
    if location and "lat" in location and "lng" in location:
        query["bool"]["filter"].append({
            "geo_distance": {
                "distance": location.get("radius", "1km"),
                "location": {
                    "lat": location["lat"],
                    "lon": location["lng"]
                }
            }
        })
    
    return query


def search_listings_with_es(
    keyword: Optional[str] = None,
    style_tags: Optional[List[str]] = None,
    min_deposit: Optional[int] = None,
    max_deposit: Optional[int] = None,
    min_rent: Optional[int] = None,
    max_rent: Optional[int] = None,
    location: Optional[Dict[str, Any]] = None,
    candidate_ids: Optional[List[str]] = None,
    size: int = 100
) -> Dict[str, Any]:
    """
    ES를 활용한 매물 검색
    
    Args:
        keyword: 검색 키워드
        style_tags: 스타일 태그 목록
        min_deposit: 최소 보증금
        max_deposit: 최대 보증금
        min_rent: 최소 월세
        max_rent: 최대 월세
        location: 위치 정보 {'lat': float, 'lng': float, 'radius': str}
        candidate_ids: Neo4j에서 추출한 후보 매물 ID 목록
        size: 반환할 최대 결과 수
    
    Returns:
        {
            'ids': List[str],  # 매물 ID 목록
            'scores': Dict[str, float],  # ID별 점수
            'total': int  # 전체 매칭 수
        }
    """
    # 빈 결과 기본값
    empty_result: Dict[str, Any] = {'ids': [], 'scores': {}, 'total': 0}
    
    try:
        es = ESClient.get_client()
        
        # 쿼리 빌드
        query = build_es_query(
            keyword=keyword,
            style_tags=style_tags,
            min_deposit=min_deposit,
            max_deposit=max_deposit,
            min_rent=min_rent,
            max_rent=max_rent,
            location=location,
            candidate_ids=candidate_ids
        )
        
        # ES 검색 실행
        response = es.search(
            index=ES_INDEX_NAME,
            query=query,
            size=size,
            _source=["land_num", "address", "search_text", "deposit", "monthly_rent"]
        )
        
        # 결과 파싱
        ids: List[str] = []
        scores: Dict[str, float] = {}
        
        for hit in response['hits']['hits']:
            land_num = hit['_source'].get('land_num')
            if land_num:
                ids.append(land_num)
                scores[land_num] = hit['_score'] or 0.0
        
        total = response['hits']['total']
        total_count = total['value'] if isinstance(total, dict) else total
        
        return {
            'ids': ids,
            'scores': scores,
            'total': total_count
        }
        
    except ConnectionError as e:
        logger.error(f"ES connection failed: {e}")
        return empty_result
    except Exception as e:
        logger.error(f"ES search error: {e}")
        return empty_result
