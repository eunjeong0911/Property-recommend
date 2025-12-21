"""
레이더 차트 점수 계산 유틸리티

매물의 5가지 핵심 지표를 0-100점으로 계산:
1. 건물연식 (Building Age)
2. 옵션 충실도 (Options Completeness)
3. 보안 수준 (Security Level)
4. 공간 효율성 (Space Efficiency)
5. 교통 접근성 (Transportation Accessibility)
"""

from datetime import datetime
import re
from typing import Dict, Optional


def calculate_building_age_score(approval_date: str) -> int:
    """
    건물연식 점수 계산
    
    Args:
        approval_date: 사용승인일 (예: "2017.01.11")
    
    Returns:
        0-100점 사이의 점수
        - 5년 이하 (신축): 100점
        - 6-10년 (준신축): 80점
        - 11-20년 (보통): 60점
        - 21-30년 (노후): 40점
        - 31년 이상 (재건축 대상): 20점
    """
    if not approval_date or approval_date == '-':
        return 50  # 기본값
    
    try:
        # 날짜 파싱 (여러 형식 지원)
        date_formats = ['%Y.%m.%d', '%Y-%m-%d', '%Y/%m/%d']
        approval_dt = None
        
        for fmt in date_formats:
            try:
                approval_dt = datetime.strptime(approval_date, fmt)
                break
            except ValueError:
                continue
        
        if not approval_dt:
            return 50
        
        # 건물 연식 계산
        years_old = (datetime.now() - approval_dt).days / 365.25
        
        if years_old <= 5:
            return 100  # 신축
        elif years_old <= 10:
            return 80   # 준신축
        elif years_old <= 20:
            return 60   # 보통
        elif years_old <= 30:
            return 40   # 노후
        else:
            return 20   # 재건축 대상
    
    except Exception:
        return 50  # 파싱 실패 시 기본값


def calculate_options_score(living_facilities: str, other_facilities: str = None, additional_options: str = None) -> int:
    """
    옵션 충실도 점수 계산 (생활시설 + 기타 + 추가옵션 통합)
    
    Args:
        living_facilities: 생활시설 문자열 (예: "냉장고, 세탁기, 싱크대, ...")
        other_facilities: 기타 시설 문자열 (listing_info의 '기타' 필드)
        additional_options: 추가 옵션 문자열 (additional_options 컬럼)
    
    Returns:
        0-100점 사이의 점수
        - 12개 이상 (풀옵션): 100점
        - 9-11개 (준풀옵션): 80점
        - 6-8개 (기본옵션): 60점
        - 3-5개 (최소옵션): 40점
        - 2개 이하 (옵션부족): 20점
    """
    all_facilities = []
    
    # 생활시설 추가
    if living_facilities and living_facilities != '-':
        facilities = [f.strip() for f in living_facilities.split(',') if f.strip()]
        all_facilities.extend(facilities)
    
    # 기타 시설 추가
    if other_facilities and other_facilities != '-':
        facilities = [f.strip() for f in other_facilities.split(',') if f.strip()]
        all_facilities.extend(facilities)
    
    # 추가 옵션 추가
    if additional_options and additional_options != '-':
        facilities = [f.strip() for f in additional_options.split(',') if f.strip()]
        all_facilities.extend(facilities)
    
    # 중복 제거
    unique_facilities = list(set(all_facilities))
    count = len(unique_facilities)
    
    if count >= 12:
        return 100  # 풀옵션
    elif count >= 9:
        return 80   # 준풀옵션
    elif count >= 6:
        return 60   # 기본옵션
    elif count >= 3:
        return 40   # 최소옵션
    else:
        return 20   # 옵션부족


def calculate_security_score(security_facilities: str) -> int:
    """
    보안 수준 점수 계산
    
    Args:
        security_facilities: 보안시설 문자열 (예: "현관보안, CCTV, 인터폰, ...")
    
    Returns:
        0-100점 사이의 점수
        - 5개 이상 (최고 보안): 100점
        - 4개 (우수 보안): 80점
        - 3개 (양호 보안): 60점
        - 2개 (기본 보안): 40점
        - 1개 이하 (보안 취약): 20점
    """
    if not security_facilities or security_facilities == '-':
        return 20  # 보안시설 없음
    
    # 쉼표로 구분하여 개수 세기
    facilities_list = [f.strip() for f in security_facilities.split(',') if f.strip()]
    count = len(facilities_list)
    
    if count >= 5:
        return 100  # 최고 보안
    elif count >= 4:
        return 80   # 우수 보안
    elif count >= 3:
        return 60   # 양호 보안
    elif count >= 2:
        return 40   # 기본 보안
    else:
        return 20   # 보안 취약


def calculate_space_efficiency_score(area_info: str) -> int:
    """
    공간 효율성 점수 계산
    
    Args:
        area_info: 전용/공급면적 문자열 (예: "40.14m2/59.96m2 (12.14평/18.14평)")
    
    Returns:
        0-100점 사이의 점수
        - 85% 이상: 100점
        - 75-84%: 80점
        - 65-74%: 60점
        - 55-64%: 40점
        - 55% 미만: 20점
    """
    if not area_info or area_info == '-':
        return 50  # 기본값
    
    try:
        # 정규식으로 전용면적과 공급면적 추출
        # 예: "40.14m2/59.96m2" 또는 "40.14㎡/59.96㎡"
        pattern = r'([\d.]+)\s*(?:m2|㎡)\s*/\s*([\d.]+)\s*(?:m2|㎡)'
        match = re.search(pattern, area_info)
        
        if match:
            exclusive_area = float(match.group(1))
            supply_area = float(match.group(2))
            
            if supply_area > 0:
                efficiency = (exclusive_area / supply_area) * 100
                
                if efficiency >= 85:
                    return 100
                elif efficiency >= 75:
                    return 80
                elif efficiency >= 65:
                    return 60
                elif efficiency >= 55:
                    return 40
                else:
                    return 20
        
        return 50  # 파싱 실패 시 기본값
    
    except Exception:
        return 50


def calculate_transportation_score(land_address: str) -> int:
    """
    교통 접근성 점수 계산
    
    TODO: Neo4j 연동하여 실제 지하철역/버스정류장 거리 계산
    현재는 임시로 기본값 반환
    
    Args:
        land_address: 매물 주소
    
    Returns:
        0-100점 사이의 점수
    """
    # TODO: Neo4j에서 가장 가까운 지하철역 거리 조회
    # - 300m 이내: 100점
    # - 300-500m: 80점
    # - 500-700m: 60점
    # - 700-1000m: 40점
    # - 1000m 이상: 20점
    
    return 70  # 임시 기본값


def calculate_radar_chart_data(land) -> Dict[str, int]:
    """
    매물의 레이더 차트 데이터 계산
    
    Args:
        land: Land 모델 인스턴스
    
    Returns:
        5가지 지표의 점수 딕셔너리
    """
    listing_info = land.listing_info or {}
    
    # 1. 건물연식
    approval_date = listing_info.get('사용승인일', '-')
    building_age = calculate_building_age_score(approval_date)
    
    # 2. 옵션 충실도 (생활시설 + 기타 + 추가옵션 통합)
    living_facilities = listing_info.get('생활시설', '-')
    other_facilities = listing_info.get('기타', '-')
    additional_options = land.additional_options or '-'
    options = calculate_options_score(living_facilities, other_facilities, additional_options)
    
    # 3. 보안 수준
    security_facilities = listing_info.get('보안시설', '-')
    security = calculate_security_score(security_facilities)
    
    # 4. 공간 효율성
    area_info = listing_info.get('전용/공급면적', '-')
    space_efficiency = calculate_space_efficiency_score(area_info)
    
    # 5. 교통 접근성
    transportation = calculate_transportation_score(land.address or '')
    
    return {
        'building_age': building_age,
        'options': options,
        'security': security,
        'space_efficiency': space_efficiency,
        'transportation': transportation
    }
