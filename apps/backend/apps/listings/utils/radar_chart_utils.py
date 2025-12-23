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
    옵션 충실도 점수 계산 (5분위수 방식 + 최저주거기준)
    
    1단계: 최저주거기준 검증 (난방, 채광, 환기)
    2단계: 옵션 개수에 따른 5분위수 분류
    
    Args:
        living_facilities: 생활시설 문자열 (예: "냉장고, 세탁기, 싱크대, ...")
        other_facilities: 기타 시설 문자열 (listing_info의 '기타' 필드)
        additional_options: 추가 옵션 문자열 (additional_options 컬럼)
    
    Returns:
        0-100점 사이의 점수 (20점 단위)
        - 0점: 최저주거기준 미달
        - 20점: 1분위 (0~2개 옵션)
        - 40점: 2분위 (3~4개 옵션)
        - 60점: 3분위 (5~7개 옵션) ← 평균 6.2개
        - 80점: 4분위 (8~10개 옵션)
        - 100점: 5분위 (11개 이상 옵션)
    
    Note:
        최저주거기준은 calculate_radar_chart_data()에서 검증
        이 함수는 옵션 개수만 계산
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
    
    # 5분위수 분류 (평균 6.2개가 3분위 중앙에 위치)
    if count <= 2:
        return 20  # 1분위
    elif count <= 4:
        return 40  # 2분위
    elif count <= 7:
        return 60  # 3분위 (평균)
    elif count <= 10:
        return 80  # 4분위
    else:  # 11개 이상
        return 100  # 5분위



def calculate_security_score(security_facilities: str, other_facilities: str = None) -> int:
    """
    보안 수준 점수 계산 (5분위수 방식, 컬럼 기반 카운팅)
    
    최소기준 없이 순수하게 보안 시설 개수로만 점수 계산
    컬럼에서 쉼표로 구분된 항목을 그대로 카운팅 (키워드 하드코딩 없음)
    
    Args:
        security_facilities: 보안시설 문자열 (예: "현관보안, CCTV, 인터폰, ...")
        other_facilities: 기타 시설 문자열 (보안 관련 항목 포함 가능)
    
    Returns:
        0-100점 사이의 점수 (20점 단위)
        - 20점: 1분위 (0개 보안시설)
        - 40점: 2분위 (1~2개 보안시설)
        - 60점: 3분위 (3~4개 보안시설) ← 평균 2.8개
        - 80점: 4분위 (5~6개 보안시설)
        - 100점: 5분위 (7개 이상 보안시설)
    """
    all_facilities = []
    
    # 보안시설 추가
    if security_facilities and security_facilities != '-':
        facilities = [f.strip() for f in security_facilities.split(',') if f.strip()]
        all_facilities.extend(facilities)
    
    # 기타 시설에서 보안 관련 항목 추가 (있다면)
    if other_facilities and other_facilities != '-':
        facilities = [f.strip() for f in other_facilities.split(',') if f.strip()]
        all_facilities.extend(facilities)
    
    # 중복 제거
    unique_facilities = list(set(all_facilities))
    count = len(unique_facilities)
    
    # 5분위수 분류 (평균 2.8개가 3분위 중앙에 위치)
    if count == 0:
        return 20  # 1분위
    elif count <= 2:
        return 40  # 2분위
    elif count <= 4:
        return 60  # 3분위 (평균)
    elif count <= 6:
        return 80  # 4분위
    else:  # 7개 이상
        return 100  # 5분위


def calculate_space_efficiency_score(area_info: str) -> int:
    """
    공간 효율성 점수 계산
    
    전국 평균 전용률(77.6%)을 기준으로 점수 산정:
    - 평균(77.6%) = 80점
    - 우수(85% 이상) = 100점
    - 양호(70-77%) = 60점
    - 보통(60-70%) = 40점
    - 낮음(60% 미만) = 20점
    
    Args:
        area_info: 전용/공급면적 문자열 (예: "40.14m2/59.96m2 (12.14평/18.14평)")
    
    Returns:
        0-100점 사이의 점수
        - 85% 이상: 100점 (우수 - 평균보다 약 10% 높음)
        - 77-84%: 80점 (평균 수준 - 전국 평균 77.6%)
        - 70-76%: 60점 (양호 - 소형 아파트 평균 74.5%)
        - 60-69%: 40점 (보통 - 최소 허용 수준)
        - 60% 미만: 20점 (낮음 - 공용면적 과다)
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
                
                # 전국 평균(77.6%) 기준 점수 산정
                if efficiency >= 85:
                    return 100  # 우수 (평균보다 10% 높음)
                elif efficiency >= 77:
                    return 80   # 평균 수준 (전국 평균 77.6%)
                elif efficiency >= 70:
                    return 60   # 양호 (소형 아파트 평균 74.5%)
                elif efficiency >= 60:
                    return 40   # 보통 (최소 허용 수준)
                else:
                    return 20   # 낮음 (공용면적 과다)
        
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
    매물의 레이더 차트 데이터 계산 (5분위수 + 최저주거기준)
    
    Args:
        land: Land 모델 인스턴스
    
    Returns:
        5가지 지표의 점수 딕셔너리
    """
    listing_info = land.listing_info or {}
    
    # 1. 건물연식
    approval_date = listing_info.get('사용승인일', '-')
    building_age = calculate_building_age_score(approval_date)
    
    # 2. 옵션 충실도 (최저주거기준 검증 + 5분위수)
    # 2-1. 최저주거기준 검증
    heating = listing_info.get('난방방식', '-')
    direction = listing_info.get('주실기준/방향', '-')
    other_facilities = listing_info.get('기타', '-')
    description = land.description or ''
    
    # 필수 조건 확인
    has_heating = heating and heating != '-'
    has_lighting = direction and direction != '-'
    
    ventilation_keywords = ['환기', '창문', '창', '발코니', '베란다']
    has_ventilation = any(keyword in description or keyword in other_facilities 
                          for keyword in ventilation_keywords)
    
    # 최저주거기준 미충족 시 0점
    if not (has_heating and has_lighting and has_ventilation):
        options = 0
    else:
        # 최저주거기준 충족 시 옵션 개수로 5분위수 계산
        living_facilities = listing_info.get('생활시설', '-')
        additional_options = land.additional_options or '-'
        options = calculate_options_score(living_facilities, other_facilities, additional_options)
    
    # 3. 보안 수준 (컬럼 기반 카운팅, 최소기준 없음)
    security_facilities = listing_info.get('보안시설', '-')
    security = calculate_security_score(security_facilities, other_facilities)
    
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
