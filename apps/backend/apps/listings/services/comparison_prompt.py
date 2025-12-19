"""
매물 비교 LLM 프롬프트 템플릿
"""

COMPARISON_SYSTEM_PROMPT = """당신은 한국 부동산 시장 전문가입니다.

**핵심 원칙**:
1. 사실만 전달 - 주관적 표현 절대 금지
2. 논리적 일관성 필수 - 모순되는 문장 절대 금지
3. 중복 정보 제거 - 같은 내용을 반복하지 않음

**평당 환산보증금 계산**:
- 적용이자율 = (기준금리 2.5% + 2.0%) / 100 = 0.045
- 환산보증금 = 보증금 + (임대료 × 12) / 적용이자율
- 평당 환산보증금 = 환산보증금 / (전용면적 / 3.3)

**논리적 일관성 규칙**:
- 한 매물이 "가능"이면서 동시에 "불가"일 수 없음
- 각 매물의 특성은 제공된 데이터만 사용
- 비교 시 테이블 형식으로만 나열
"""

COMPARISON_USER_PROMPT_TEMPLATE = """
다음 {count}개 매물을 종합 비교 분석하세요.

**절대 규칙**:
1. 제공된 데이터의 사실만 비교
2. 논리적으로 모순되는 문장 절대 금지
3. 테이블 데이터는 정확히 그대로 표기

**평당 환산보증금 공식** (기준금리 2.5%):
- 적용이자율 = 4.5% (기준금리 2.5% + 2.0%)
- 환산보증금 = 보증금 + (월세 × 12 ÷ 0.045)
- 평당 환산보증금 = 환산보증금 ÷ (전용면적 ÷ 3.3)

**매물 데이터**:
{properties_data}

**출력 형식**:

## 종합 비교
[5문장으로 핵심 차이점만 깔끔하게 요약해서 사용자가 쉽게 이해할 수 있도록 시각적으로 작성하고, 중요한 키워드는 굵게 색상으로 표시하거나 표 형태로 정리]

---
## 조건별 추천

각 조건에 맞는 매물 1개만 추천 (중복 추천 가능):
- **가성비**: 매물X (이유: 가격 비교한 결과)
- **넓은 공간**: 매물Y (이유: 전용면적 비교한 결과)
- **신뢰도**: 매물Z (이유: X등급)

---
**참고**: 객관적 데이터 기반 비교입니다. 최종 선택은 개인 상황을 고려하세요.
"""


def format_property_for_comparison(property_data: dict, index: int) -> str:
    """
    매물 데이터를 LLM 프롬프트용 텍스트로 포맷팅
    """
    import re
    
    # property_number가 있으면 사용, 없으면 index 사용
    prop_number = property_data.get('property_number', index)
    
    # 가격 정보
    deposit = property_data.get('deposit', 0) or 0
    monthly_rent = property_data.get('monthly_rent', 0) or 0
    jeonse_price = property_data.get('jeonse_price', 0) or 0
    
    # 면적 정보 (문자열에서 숫자 추출)
    area_exclusive_str = property_data.get('area_exclusive', '-')
    
    # 전용면적에서 숫자 추출 (예: "25.48㎡/35.28㎡" -> 25.48)
    area_exclusive_value = 0
    if area_exclusive_str and area_exclusive_str != '-':
        match = re.search(r'([\d.]+)', str(area_exclusive_str))
        if match:
            area_exclusive_value = float(match.group(1))
    
    # 평으로 변환 (1평 = 3.3㎡)
    area_pyeong = area_exclusive_value / 3.3 if area_exclusive_value > 0 else 0
    
    # 기타 정보
    floor = property_data.get('floor', '-')
    room_count = property_data.get('room_count', '-')
    direction = property_data.get('direction', '-')
    parking = property_data.get('parking', '-')
    heating = property_data.get('heating_method', '-')
    
    # 실거래가 판단 정보
    ml_prediction = property_data.get('price_prediction', {})
    ml_label = ml_prediction.get('prediction_label_korean', '-')
    
    # 중개사 신뢰도
    broker = property_data.get('broker', {})
    trust_score = broker.get('trust_score', '-')
    trust_grade = broker.get('trust_grade', '-')
    
    # 거래 유형에 따른 가격 및 평당 환산보증금 계산
    deal_type = property_data.get('deal_type', '월세')
    
    # 적용이자율 = (기준금리 2.5% + 2.0%) / 100 = 0.045
    APPLIED_INTEREST_RATE = 0.045
    
    converted_deposit = 0      # 환산보증금
    price_per_pyeong = 0       # 평당 환산보증금
    
    if deal_type == '전세':
        price_info = f"전세 {jeonse_price:,}만원"
        converted_deposit = jeonse_price
        if area_pyeong > 0:
            price_per_pyeong = jeonse_price / area_pyeong
    elif deal_type == '매매':
        sale_price = property_data.get('sale_price', 0) or 0
        price_info = f"매매 {sale_price:,}만원"
        converted_deposit = sale_price
        if area_pyeong > 0:
            price_per_pyeong = sale_price / area_pyeong
    else:  # 월세/단기임대
        price_info = f"보증금 {deposit:,}만원 / 월세 {monthly_rent:,}만원"
        # 환산보증금 = 보증금 + (월세 × 12 / 적용이자율)
        if monthly_rent > 0:
            converted_deposit = deposit + (monthly_rent * 12 / APPLIED_INTEREST_RATE)
        else:
            converted_deposit = deposit
        if area_pyeong > 0:
            price_per_pyeong = converted_deposit / area_pyeong
    
    # 포맷
    price_per_pyeong_str = f"{int(price_per_pyeong):,}만원/평" if price_per_pyeong > 0 else "-"
    area_pyeong_str = f"{area_pyeong:.1f}평" if area_pyeong > 0 else "-"
    
    formatted = f"""
매물{prop_number}:
- 주소: {property_data.get('address', '-')}
- 거래유형: {deal_type}
- 가격: {price_info}
- 전용면적: {area_exclusive_str} ({area_pyeong_str})
- 평당 환산보증금: {price_per_pyeong_str}
- 건물유형: {property_data.get('building_type', '-')}
- 층수: {floor}
- 방/욕실: {room_count}
- 방향: {direction}
- 주차: {parking}
- 난방: {heating}
- 실거래가 판단: {ml_label}
- 중개사 신뢰도: {trust_score}등급 ({trust_grade})
"""
    
    return formatted.strip()


def create_comparison_prompt(properties: list) -> dict:
    """
    매물 리스트를 받아 LLM 프롬프트 생성
    """
    if not properties or len(properties) < 2:
        raise ValueError("최소 2개의 매물이 필요합니다.")
    
    if len(properties) > 3:
        raise ValueError("최대 3개의 매물만 비교할 수 있습니다.")
    
    # 각 매물 포맷팅
    properties_text = "\n\n".join([
        format_property_for_comparison(prop, i + 1)
        for i, prop in enumerate(properties)
    ])
    
    # 프롬프트 생성
    user_prompt = COMPARISON_USER_PROMPT_TEMPLATE.format(
        count=len(properties),
        properties_data=properties_text
    )
    
    return {
        "system": COMPARISON_SYSTEM_PROMPT,
        "user": user_prompt
    }
