"""
가격 파싱 및 포맷팅 유틸리티 모듈

사전 컴파일된 정규식 패턴을 사용하여 성능을 최적화합니다.
Requirements: 4.1, 7.1, 7.2, 7.3
"""
import re
from typing import Optional, Tuple

# 사전 컴파일된 정규식 패턴 (모듈 로드 시 한 번만 컴파일)
PRICE_PATTERNS = {
    'jeonse': re.compile(r'전세\s+(\d+억\s*\d*,?\d*만원|\d+,?\d*만원|\d+억)'),
    'wolse': re.compile(r'월세\s+(\d+억\s*\d*,?\d*만원|\d+,?\d*만원|\d+억)/(\d+,?\d*만원)'),
    'maemae': re.compile(r'매매\s+(\d+억\s*\d*,?\d*만원|\d+,?\d*만원|\d+억)'),
    'danggi': re.compile(r'(\d+,?\d*만원)/(\d+,?\d*만원)'),
    'eok': re.compile(r'(\d+)억'),
    'manwon': re.compile(r'(\d+)만원'),
    'area_pyeong': re.compile(r'\(([^)]+평)'),
    'area_supply': re.compile(r'/([^(]+)\('),
    'area_exclusive': re.compile(r'(\d+\.?\d*m2)'),
    'floor_total': re.compile(r'/(\d+)층'),
}


def parse_korean_price(price_str: Optional[str]) -> int:
    """
    한국어 가격 문자열을 숫자(원)로 변환합니다.
    
    Args:
        price_str: 가격 문자열 (예: '1억 2,500만원', '5,000만원', '3억')
    
    Returns:
        int: 원 단위 금액 (예: 125000000, 50000000, 300000000)
    
    Examples:
        >>> parse_korean_price('1억 2,500만원')
        125000000
        >>> parse_korean_price('5,000만원')
        50000000
        >>> parse_korean_price('3억')
        300000000
    """
    if not price_str or price_str == '-':
        return 0
    
    try:
        # 쉼표와 공백 제거
        price_str = price_str.replace(',', '').replace(' ', '')
        
        # 억 단위 추출
        eok_match = PRICE_PATTERNS['eok'].search(price_str)
        eok = int(eok_match.group(1)) * 100000000 if eok_match else 0
        
        # 만원 단위 추출
        man_match = PRICE_PATTERNS['manwon'].search(price_str)
        man = int(man_match.group(1)) * 10000 if man_match else 0
        
        return eok + man
    except (ValueError, AttributeError):
        return 0


def format_price_in_manwon(amount: int) -> str:
    """
    금액(원)을 한국어 만원 단위로 포맷팅합니다.
    
    Args:
        amount: 원 단위 금액
    
    Returns:
        str: 포맷팅된 가격 문자열 (예: '1억 2,500만원', '5,000만원')
    
    Examples:
        >>> format_price_in_manwon(125000000)
        '1억 2,500만원'
        >>> format_price_in_manwon(50000000)
        '5,000만원'
        >>> format_price_in_manwon(300000000)
        '3억'
    """
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


def extract_deposit_from_deal_text(deal_text: str, deal_type: str = '') -> int:
    """
    거래방식 문자열에서 보증금을 추출합니다.
    
    Args:
        deal_text: 거래방식 문자열 (예: '전세 1억 2,500만원', '월세 2,500만원/104만원')
        deal_type: 거래유형 (예: '전세', '월세', '매매', '단기임대')
    
    Returns:
        int: 보증금 (원 단위)
    """
    if not deal_text:
        return 0
    
    # 전세
    if '전세' in deal_text:
        match = PRICE_PATTERNS['jeonse'].search(deal_text)
        if match:
            return parse_korean_price(match.group(1))
    
    # 월세
    elif '월세' in deal_text:
        match = PRICE_PATTERNS['wolse'].search(deal_text)
        if match:
            return parse_korean_price(match.group(1))
    
    # 매매
    elif '매매' in deal_text:
        match = PRICE_PATTERNS['maemae'].search(deal_text)
        if match:
            return parse_korean_price(match.group(1))
    
    # 단기임대
    if '단기임대' in deal_type:
        match = PRICE_PATTERNS['danggi'].search(deal_type)
        if match:
            return parse_korean_price(match.group(1))
    
    return 0


def extract_monthly_rent_from_deal_text(deal_text: str, deal_type: str = '') -> int:
    """
    거래방식 문자열에서 월세를 추출합니다.
    
    Args:
        deal_text: 거래방식 문자열 (예: '월세 2,500만원/104만원')
        deal_type: 거래유형 (예: '월세', '단기임대')
    
    Returns:
        int: 월세 (원 단위)
    """
    if not deal_text:
        return 0
    
    # 월세
    if '월세' in deal_text:
        match = PRICE_PATTERNS['wolse'].search(deal_text)
        if match:
            return parse_korean_price(match.group(2))
    
    # 단기임대
    if '단기임대' in deal_type:
        match = PRICE_PATTERNS['danggi'].search(deal_type)
        if match:
            return parse_korean_price(match.group(2))
    
    return 0


def get_price_display(land) -> str:
    """
    매물 객체에서 가격 표시 문자열을 생성합니다.
    
    Args:
        land: Land 모델 인스턴스 (deal_type, deposit, monthly_rent, jeonse_price, sale_price 속성 필요)
    
    Returns:
        str: 가격 표시 문자열 (예: '매매 1억 2,500만원', '월세 2,500만원 / 104만원')
    """
    deal_type = land.deal_type or ''
    
    # 단기임대는 deal_type에 이미 가격이 포함되어 있음
    if '단기임대' in deal_type:
        return deal_type
    
    # 데이터베이스 컬럼에서 직접 가격 가져오기 (만원 단위)
    deposit = getattr(land, 'deposit', 0) or 0
    monthly_rent = getattr(land, 'monthly_rent', 0) or 0
    jeonse_price = getattr(land, 'jeonse_price', 0) or 0
    sale_price = getattr(land, 'sale_price', 0) or 0
    
    # 매매
    if deal_type == '매매':
        if sale_price > 0:
            return f"매매 {format_price_in_manwon(sale_price * 10000)}"
        return '매매 (가격 미정)'
    
    # 전세
    if deal_type == '전세':
        if jeonse_price > 0:
            return f"전세 {format_price_in_manwon(jeonse_price * 10000)}"
        return '전세 (가격 미정)'
    
    # 월세
    if deal_type == '월세':
        if deposit > 0 or monthly_rent > 0:
            deposit_str = format_price_in_manwon(deposit * 10000)
            monthly_str = format_price_in_manwon(monthly_rent * 10000)
            return f"월세 {deposit_str} / {monthly_str}"
        return '월세 (가격 미정)'
    
    # 기타 - trade_info에서 시도
    trade_info = land.trade_info or {}
    deal_text = trade_info.get('거래방식', '') if isinstance(trade_info, dict) else ''
    if deal_text:
        return deal_text
    
    return '가격 정보 없음'


def extract_area_pyeong(area_str: str) -> str:
    """
    면적 문자열에서 평수를 추출합니다.
    
    Args:
        area_str: 면적 문자열 (예: '30m2/38.68m2 (9.07평/11.7평)')
    
    Returns:
        str: 평수 문자열 (예: '9.07평')
    """
    if not area_str or area_str == '-':
        return ''
    
    match = PRICE_PATTERNS['area_pyeong'].search(area_str)
    if match:
        return match.group(1)
    return ''


def extract_area_supply(area_str: str) -> str:
    """
    면적 문자열에서 공급면적을 추출합니다.
    
    Args:
        area_str: 면적 문자열 (예: '30m2/38.68m2 (9.07평/11.7평)')
    
    Returns:
        str: 공급면적 문자열 (예: '38.68m2')
    """
    if not area_str or area_str == '-':
        return area_str
    
    match = PRICE_PATTERNS['area_supply'].search(area_str)
    if match:
        return match.group(1).strip()
    return area_str


def extract_area_exclusive(area_str: str) -> str:
    """
    면적 문자열에서 전용면적을 추출합니다.
    
    Args:
        area_str: 면적 문자열 (예: '30m2/38.68m2 (9.07평/11.7평)')
    
    Returns:
        str: 전용면적 문자열 (예: '30m2')
    """
    if not area_str or area_str == '-':
        return area_str
    
    match = PRICE_PATTERNS['area_exclusive'].search(area_str)
    if match:
        return match.group(1)
    return area_str


def extract_total_floors(floor_str: str) -> Optional[int]:
    """
    층수 문자열에서 전체 층수를 추출합니다.
    
    Args:
        floor_str: 층수 문자열 (예: '3층/15층')
    
    Returns:
        Optional[int]: 전체 층수 또는 None
    """
    if not floor_str or floor_str == '-':
        return None
    
    match = PRICE_PATTERNS['floor_total'].search(floor_str)
    if match:
        return int(match.group(1))
    return None
