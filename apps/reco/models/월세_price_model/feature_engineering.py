"""
특성 엔지니어링 모듈
모든 특성 변환 및 추출 함수들을 포함합니다.
"""
import re
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer


# ==================== 금액 관련 ====================

def parse_korean_money(text):
    """
    숫자 + 만원/억 단위 문자열을 숫자로 변환하는 함수

    Args:
        text: 한국 화폐 단위 문자열 (예: "2,500만원", "3억")

    Returns:
        int: 만원 단위로 변환된 숫자
    """
    if pd.isna(text):
        return 0

    text = text.replace(",", "").strip()

    # 앞뒤의 불필요한 단어 제거 (예: "월세 2500만원")
    text = re.sub(r"[^\d억만]", "", text)

    # 억 단위 포함
    if "억" in text:
        parts = text.split("억")
        eok = int(parts[0]) if parts[0] else 0

        man = 0
        if len(parts) > 1 and "만" in parts[1]:
            man = int(parts[1].replace("만", ""))

        return eok * 10000 + man  # 만원 단위로 반환

    # 억 없음 → 그냥 만원 단위 숫자
    numbers = re.findall(r"\d+", text)
    if numbers:
        return int(numbers[0])

    return 0


def split_deposit_rent(x):
    """
    "보증금/월세" 문자열을 분리하여 각각의 금액을 반환합니다.

    Args:
        x: "보증금/월세" 형식의 문자열

    Returns:
        pd.Series: [보증금, 월세]
    """
    x = x.replace(" ", "")
    deposit, rent = x.split("/")
    deposit = parse_korean_money(deposit)
    rent = parse_korean_money(rent)
    return pd.Series([deposit, rent])


def calculate_converted_deposit(df: pd.DataFrame) -> pd.DataFrame:
    """
    보증금과 월세를 기반으로 환산보증금을 계산합니다.

    Args:
        df: 데이터프레임 (거래_정보.거래방식 컬럼 필요)

    Returns:
        pd.DataFrame: 보증금, 월세, 월세_전환보증금, 환산보증금 컬럼이 추가된 데이터프레임
    """
    # 보증금/월세 분리
    df[["보증금", "월세"]] = df["거래_정보.거래방식"].apply(split_deposit_rent)

    # 월세 전환 보증금 계산
    df["월세_전환보증금"] = df["월세"] * 12 / 0.06

    # 최종 환산보증금 계산
    df["환산보증금"] = df["보증금"] + df["월세_전환보증금"]

    return df


def extract_management_fee(value):
    """
    관리비 문자열에서 '00만원' 형태 중 가장 앞에 나오는 숫자만 추출.

    Args:
        value: 관리비 문자열

    Returns:
        int or None: 관리비 (만원 단위)
    """
    if pd.isna(value):
        return None

    s = str(value).strip()

    # 맨 앞쪽 "숫자 + 만원" 패턴 첫번째 매칭만 추출
    match = re.search(r'(\d+)\s*만원', s)

    if match:
        return int(match.group(1))

    return None


def add_management_fee(df: pd.DataFrame) -> pd.DataFrame:
    """
    관리비 정보를 추출하여 추가합니다.

    Args:
        df: 데이터프레임 (거래_정보.관리비 컬럼 필요)

    Returns:
        pd.DataFrame: 관리비 컬럼이 추가된 데이터프레임
    """
    df["관리비"] = df["거래_정보.관리비"].apply(extract_management_fee)
    df["관리비"] = df["관리비"].fillna(0)
    return df


# ==================== 면적 관련 ====================

def extract_area(value):
    """
    전용/공급면적에서 전용면적(㎡)만 추출.
    예: '30m2/38.68m2' -> 30.0

    Args:
        value: 면적 문자열

    Returns:
        float or None: 전용면적 (㎡)
    """
    if pd.isna(value):
        return None
    try:
        text = str(value).replace(" ", "").strip()
        area_str = text.split('/')[0].replace("m2", "")
        return float(area_str)
    except:
        return None


def convert_to_pyeong_from_raw(value):
    """
    '30m2/38.68m2' 같은 문자열을 입력받아 바로 평으로 변환.

    Args:
        value: 면적 문자열

    Returns:
        float or None: 전용면적 (평)
    """
    area_m2 = extract_area(value)
    if area_m2 is None:
        return None
    return round(area_m2 / 3.3, 2)


def add_area_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    전용면적 정보를 추출하여 추가합니다.

    Args:
        df: 데이터프레임 (매물_정보.전용/공급면적 컬럼 필요)

    Returns:
        pd.DataFrame: 전용면적_m2, 전용면적_평 컬럼이 추가된 데이터프레임
    """
    col_area = "매물_정보.전용/공급면적"
    df["전용면적_m2"] = df[col_area].apply(extract_area)
    df["전용면적_평"] = df[col_area].apply(convert_to_pyeong_from_raw)
    return df


# ==================== 건물 정보 관련 ====================

def building_usage_score(value):
    """
    매물_정보.건축물용도 → 점수 변환
    1점: 공동주택, 단독주택
    0점: 나머지(근린, 미등기, 업무, 숙박, 교육, '그', NaN 포함)

    Args:
        value: 건축물용도 문자열

    Returns:
        int: 점수 (0 또는 1)
    """
    if pd.isna(value):
        return 0

    s = str(value)

    # 주거용
    if '공동주택' in s or '단독주택' in s:
        return 1

    # 나머지 즉시 0점
    return 0


def building_type_score(value):
    """
    매물_정보.건물형태 → 점수 변환
    규칙 순서:
        0점: nan, 미등기, 상가
        1점: '전체', '주택'
        2점: 원룸
        3점: 빌라, 연립
        4점: 다가구

    Args:
        value: 건물형태 문자열

    Returns:
        int: 점수 (0-4)
    """
    if pd.isna(value):
        return 0

    s = str(value).strip()

    # 0점 규칙 (최우선)
    if '미등기' in s:
        return 0
    if '상가' in s:  # 해충과 쥐 등 문제로 상가주택은 0점 처리
        return 0

    # 1점 규칙
    if '전체' in s:   # 단독 (건물 전체), 다가구 (건물 전체)
        return 1
    if '주택' in s:   # 빌라/주택, 상가주택(단 상가 규칙이 먼저 걸림)
        return 1

    # 2점 규칙
    if '원룸' in s:
        return 2

    # 3점 규칙
    if '빌라' in s or '연립' in s:
        return 3

    # 4점 규칙
    if '다가구' in s:
        return 4

    # 정의되지 않은 기타 값은 기본 0 처리
    return 0


def add_building_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    건축물용도와 건물형태 정보를 점수로 변환하여 추가합니다.

    Args:
        df: 데이터프레임

    Returns:
        pd.DataFrame: 건축물용도, 건물형태 컬럼이 추가된 데이터프레임
    """
    df["건축물용도"] = df["매물_정보.건축물용도"].apply(building_usage_score)
    df["건물형태"] = df["매물_정보.건물형태"].apply(building_type_score)
    return df


# ==================== 층 정보 관련 ====================

def extract_floor_info(value):
    """
    '해당층/전체층' 문자열에서
    (해당층_숫자, 전체층_숫자, 층_타입, 층_점수)를 반환.

    층_타입: '지하', '저층', '중층', '고층', '옥탑', '알수없음'
    층_점수: 지하 < 저층 < 옥탑 < 중층 < 고층

    Args:
        value: 해당층/전체층 문자열

    Returns:
        tuple: (해당층, 전체층, 층_타입, 층_점수)
    """
    if pd.isna(value):
        return (None, None, None, None)

    s = str(value).strip()
    parts = s.split('/')

    floor_raw = parts[0].strip()              # '3층(옥탑)', '중층', 'B1층' 등
    total_raw = parts[1].strip() if len(parts) > 1 else None  # '10층', '17층' 등

    # -----------------------------
    # 1) 지하 여부 체크 ('지', 'B')
    # -----------------------------
    # 반지층, 반지하, 지하, B1층 등
    if any(tok in floor_raw for tok in ['지하', '반지하', '반지층', 'B', 'b']):
        floor_num = -1
        floor_type = '지하'
        total_floors = None
        if total_raw:
            m_tot = re.search(r'\d+', total_raw)
            if m_tot:
                total_floors = int(m_tot.group(0))
        floor_score = -1  # 지하는 항상 마이너스
        return (floor_num, total_floors, floor_type, floor_score)

    # -----------------------------
    # 2) 옥탑 여부
    # -----------------------------
    is_rooftop = ('옥' in floor_raw)  # '옥탑', '옥상', '2층(옥탑)' 등

    # -----------------------------
    # 3) 숫자 층 추출
    # -----------------------------
    floor_num = None
    m_floor = re.search(r'-?\d+', floor_raw)
    if m_floor:
        floor_num = int(m_floor.group(0))

    total_floors = None
    if total_raw:
        m_tot = re.search(r'\d+', total_raw)
        if m_tot:
            total_floors = int(m_tot.group(0))

    # -----------------------------
    # 4) 기본 층 타입 텍스트 기반
    # -----------------------------
    floor_type = '중층'  # 기본값

    if '저층' in floor_raw:
        floor_type = '저층'
    elif '고층' in floor_raw:
        floor_type = '고층'
    elif '중층' in floor_raw:
        floor_type = '중층'

    # -----------------------------
    # 5) 전체층/해당층 숫자 기준 규칙 반영
    #    - 전체층 ≤ 3 → 저층
    #    - 해당층 ≤ 2 → 저층
    #    - 그 외는 비율로 저/중/고층 나누기
    # -----------------------------
    if total_floors is not None and total_floors <= 3:
        floor_type = '저층'
    elif floor_num is not None and floor_num <= 2:
        floor_type = '저층'
    elif total_floors is not None and floor_num is not None:
        # 전체층 기준 구간 나누기 (낮은 30% = 저층, 높은 30% = 고층)
        low_th = max(1, round(total_floors * 0.3))
        high_th = max(2, round(total_floors * 0.7))

        if floor_num <= low_th:
            floor_type = '저층'
        elif floor_num >= high_th:
            floor_type = '고층'
        else:
            floor_type = '중층'

    # -----------------------------
    # 6) 옥탑이면 타입 덮어쓰기
    # -----------------------------
    if is_rooftop:
        floor_type = '옥탑'

    # -----------------------------
    # 7) 점수 매핑
    # -----------------------------
    if floor_type == '지하':
        floor_score = -1
    elif floor_type == '저층':
        floor_score = 0
    elif floor_type == '옥탑':
        floor_score = 1   # 저층(0)과 중층/고층 사이 점수
    elif floor_type == '중층':
        floor_score = 1.5
    elif floor_type == '고층':
        floor_score = 2   # 가장 우선순위 높은 층
    else:
        floor_score = None

    return (floor_num, total_floors, floor_type, floor_score)


def add_floor_feature(df: pd.DataFrame) -> pd.DataFrame:
    """
    층 정보를 추출하여 추가합니다.

    Args:
        df: 데이터프레임 (매물_정보.해당층/전체층 컬럼 필요)

    Returns:
        pd.DataFrame: 층 컬럼이 추가된 데이터프레임
    """
    df["층"] = df["매물_정보.해당층/전체층"].apply(extract_floor_info).apply(lambda x: x[0])
    return df


# ==================== 방 정보 관련 ====================

def parse_room_toilet(value):
    """
    방/욕실 개수 문자열을 파싱합니다.
    예: '2개/1개' → (2, 1)

    Args:
        value: 방/욕실개수 문자열

    Returns:
        tuple: (방수, 욕실수)
    """
    if pd.isna(value):
        return (None, None)
    try:
        room_str, toilet_str = str(value).split('/')
        room = int(re.sub(r'\D', '', room_str))      # 숫자만 추출
        toilet = int(re.sub(r'\D', '', toilet_str))
        return room, toilet
    except Exception:
        return (None, None)


def add_room_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    방수와 욕실수 정보를 추출하여 추가합니다.

    Args:
        df: 데이터프레임 (매물_정보.방/욕실개수 컬럼 필요)

    Returns:
        pd.DataFrame: 방수, 욕실수 컬럼이 추가된 데이터프레임
    """
    df[["방수", "욕실수"]] = df["매물_정보.방/욕실개수"] \
        .apply(parse_room_toilet) \
        .tolist()
    return df


def room_living_score(value):
    """
    매물_정보.방거실형태 → 점수 변환

    Args:
        value: 방거실형태 문자열

    Returns:
        int: 점수 (1-4)
    """
    if pd.isna(value):
        return 3  # nan은 기본 3점

    s = str(value).strip()

    if s == "분리형":
        return 4
    elif s == "분리형, 복층":
        return 2
    elif s == "오픈형":
        return 3
    elif s == "오픈형, 복층":
        return 1
    else:
        # 정의되지 않은 기타 값 대비 안전장치 정의가 없는경우 대부분 일반 오픈형
        return 3


def add_room_living_feature(df: pd.DataFrame) -> pd.DataFrame:
    """
    방거실형태 정보를 점수로 변환하여 추가합니다.

    Args:
        df: 데이터프레임 (매물_정보.방거실형태 컬럼 필요)

    Returns:
        pd.DataFrame: 방형태 컬럼이 추가된 데이터프레임
    """
    df["방형태"] = df["매물_정보.방거실형태"].apply(room_living_score)
    return df


# ==================== 방향 관련 ====================

def direction_score(value):
    """
    방향 문자열(예: '안방/남동향')을 점수로 변환.
    규칙:
        - '북' 포함 → 0점
        - '남' 포함 → 4점
        - '동' 또는 '서' 포함 → 2점
        - nan → 2점

    Args:
        value: 방향 문자열

    Returns:
        int: 점수 (0, 2, 4)
    """
    if pd.isna(value):
        return 2   # 결측 기본값

    s = str(value)

    # 규칙 순서 중요: "남" 처리 후 "동/서"로 넘어가야 함
    if '북' in s:
        return 0

    if '남' in s:
        return 4

    if '동' in s or '서' in s:
        return 2

    # 기타 예외 처리
    return 2


def add_direction_feature(df: pd.DataFrame) -> pd.DataFrame:
    """
    방향 정보를 점수로 변환하여 추가합니다.

    Args:
        df: 데이터프레임 (매물_정보.주실기준/방향 컬럼 필요)

    Returns:
        pd.DataFrame: 방향 컬럼이 추가된 데이터프레임
    """
    df["방향"] = df["매물_정보.주실기준/방향"].apply(direction_score)
    return df


# ==================== 주차 관련 ====================

def convert_parking(value):
    """
    '가능' → 1
    '불가' → 0
    그 외 값 또는 NaN → 0 처리

    Args:
        value: 주차 가능 여부 문자열

    Returns:
        int: 0 또는 1
    """
    if pd.isna(value):
        return 0

    value = str(value).strip()

    if value == "가능":
        return 1
    elif value == "불가":
        return 0
    else:
        return 0


def add_parking_feature(df: pd.DataFrame) -> pd.DataFrame:
    """
    주차 정보를 변환하여 추가합니다.

    Args:
        df: 데이터프레임 (매물_정보.주차 컬럼 필요)

    Returns:
        pd.DataFrame: 주차 컬럼이 추가된 데이터프레임
    """
    df["주차"] = df["매물_정보.주차"].apply(convert_parking)
    return df


# ==================== 위반건축물 관련 ====================

def convert_violation(value):
    """
    위반건축물 여부를 점수로 변환:
    - '위반건축물 아님' → 1
    - '위반건축물' → -1
    - 그 외/NaN → 0

    Args:
        value: 위반건축물 여부 문자열

    Returns:
        int: -1, 0, 1
    """
    if pd.isna(value):
        return 0

    s = str(value).strip()

    if s == "위반건축물 아님":
        return 1
    elif s == "위반건축물":
        return -1
    else:
        return 0


def add_violation_feature(df: pd.DataFrame) -> pd.DataFrame:
    """
    위반건축물 정보를 점수로 변환하여 추가합니다.

    Args:
        df: 데이터프레임 (매물_정보.위반건축물 여부 컬럼 필요)

    Returns:
        pd.DataFrame: 위반 컬럼이 추가된 데이터프레임
    """
    df["위반"] = df["매물_정보.위반건축물 여부"].apply(convert_violation)
    return df


# ==================== 주소 관련 ====================

def extract_gu_dong(addr):
    """
    주소에서 구와 행정동 추출
    - 구: '구'로 끝나는 단어
    - 동: '동' 또는 '가'로 끝나는 행정동 (숫자 포함)
        예)
        - 상도1동   → 상도1동
        - 충무로4가 → 충무로4가
        - 충정로2가 → 충정로2가
        - 필동3가   → 필동3가

    Args:
        addr: 주소 문자열

    Returns:
        tuple: (구, 동)
    """
    if pd.isna(addr):
        return (None, None)

    addr = str(addr).strip()

    # 1) 구 추출
    gu_match = re.search(r'(\S+구)', addr)
    gu = gu_match.group(1) if gu_match else None

    # 2) 동 추출: '동' 또는 '가' 로 끝나는 단어 전체 매칭
    #   숫자가 포함된 형태까지 포함: (\S+?\d*(동|가))
    dong_match = re.search(r'(\S+?\d*(동|가))', addr)

    dong = dong_match.group(1) if dong_match else None

    return (gu, dong)


def add_location_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    주소에서 구와 동 정보를 추출하여 추가합니다.

    Args:
        df: 데이터프레임 (주소_정보.전체주소 컬럼 필요)

    Returns:
        pd.DataFrame: 구, 동 컬럼이 추가된 데이터프레임
    """
    df["구"], df["동"] = zip(*df["주소_정보.전체주소"].apply(extract_gu_dong))
    return df


# ==================== 옵션 및 키워드 관련 ====================

def parse_desc_keywords(x):
    """
    상세 설명 문자열에서 특정 키워드를 리스트 형태로 추출

    Args:
        x: 상세설명 문자열

    Returns:
        list: 키워드 리스트
    """
    # NaN 처리
    if pd.isna(x):
        return []

    text = str(x)

    keywords = ["역", "신축", "리모델링"]
    found = []

    for kw in keywords:
        if kw in text:
            found.append(kw)

    return found


def parse_life_options(x):
    """
    생활시설 문자열을 옵션 리스트로 변환

    Args:
        x: 생활시설 문자열 (쉼표로 구분)

    Returns:
        list: 옵션 리스트
    """
    if pd.isna(x):
        return []
    return [item.strip() for item in str(x).split(',') if item.strip() != '']


def clean_unified_options(option_list):
    """
    리스트 안에 '옵션1|옵션2|옵션3' 형태가 있으면
    이를 '옵션1', '옵션2', '옵션3' 으로 분리한 뒤
    전체 옵션 리스트로 재조합하고 중복 제거

    Args:
        option_list: 옵션 리스트

    Returns:
        list: 정리된 옵션 리스트
    """
    cleaned = []

    if not isinstance(option_list, list):
        return []

    for item in option_list:
        if isinstance(item, str):
            # '|' 로 분리
            parts = item.split('|')
            for p in parts:
                p = p.strip()
                if p:
                    cleaned.append(p)
        else:
            # 혹시 문자열 외 타입이면 무시
            continue

    # 중복 제거 후 정렬(선택)
    return sorted(set(cleaned))


def merge_lists(row):
    """
    여러 옵션 컬럼을 하나로 합칩니다.

    Args:
        row: 데이터프레임의 행

    Returns:
        list: 통합된 옵션 리스트
    """
    combined = []
    for col in ["기타시설", "추가옵션", "생활시설", "상세키워드"]:
        items = row[col]
        if isinstance(items, list):
            combined.extend(items)
    return list(set(combined))   # 중복 제거


def add_option_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    모든 옵션 및 키워드 정보를 추출하고 통합합니다.

    Args:
        df: 데이터프레임

    Returns:
        pd.DataFrame: 옵션 관련 컬럼들이 추가된 데이터프레임
    """
    # 상세 키워드 추출
    df["상세키워드"] = df["상세_설명"].apply(parse_desc_keywords)

    # 생활시설 파싱
    df["생활시설"] = df["매물_정보.생활시설"].apply(parse_life_options)

    # 추가옵션 파싱
    df["추가옵션"] = df["추가_옵션"].apply(parse_life_options)

    # 기타시설 파싱 ('-'는 빈 리스트로 변환)
    df["기타시설"] = df["매물_정보.기타시설"].apply(
        lambda x: [] if x == "-" else parse_life_options(x)
    )

    # 통합옵션 생성
    df["통합옵션"] = df.apply(merge_lists, axis=1)

    # 통합옵션 정리 (| 구분자 분리)
    df["통합옵션"] = df["통합옵션"].apply(clean_unified_options)

    return df


# ==================== 최종 특성 생성 ====================

def create_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    모든 특성 엔지니어링을 순차적으로 수행합니다.

    Args:
        df: 전처리된 데이터프레임

    Returns:
        pd.DataFrame: 모든 특성이 추가된 데이터프레임
    """
    # 1. 금액 관련
    df = calculate_converted_deposit(df)
    df = add_management_fee(df)

    # 2. 면적 관련
    df = add_area_features(df)

    # 3. 건물 정보
    df = add_building_features(df)
    df = add_floor_feature(df)

    # 4. 방 정보
    df = add_room_features(df)
    df = add_room_living_feature(df)

    # 5. 기타 정보
    df = add_direction_feature(df)
    df = add_parking_feature(df)
    df = add_violation_feature(df)

    # 6. 위치 정보
    df = add_location_features(df)

    # 7. 옵션 및 키워드
    df = add_option_features(df)

    return df


def prepare_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    머신러닝 모델 학습을 위한 최종 특성 데이터프레임을 생성합니다.

    Args:
        df: 특성 엔지니어링이 완료된 데이터프레임

    Returns:
        pd.DataFrame: 모델 학습용 특성 데이터프레임
    """
    feature_cols = [
        "환산보증금",
        "전용면적_평",
        "전용면적_m2",
        "관리비",
        "건축물용도",
        "건물형태",
        "층",
        "방수",
        "욕실수",
        "방형태",
        "방향",
        "구",
        "동",
        "통합옵션",
    ]

    df_ml = df[feature_cols].copy()

    # MultiLabelBinarizer로 통합옵션 인코딩
    mlb = MultiLabelBinarizer()
    encoded = mlb.fit_transform(df_ml["통합옵션"])

    new_cols = [f"통합옵션_{opt}" for opt in mlb.classes_]
    df_opt = pd.DataFrame(encoded, columns=new_cols, index=df_ml.index)

    # 통합옵션 컬럼 제거하고 인코딩 결과 붙이기
    df_ml = pd.concat([df_ml.drop(columns=["통합옵션"]), df_opt], axis=1)

    # LabelEncoder로 구, 동 인코딩
    label_cols = ["구", "동"]
    for col in label_cols:
        le = LabelEncoder()
        df_ml[col] = le.fit_transform(df_ml[col].astype(str))

    return df_ml
