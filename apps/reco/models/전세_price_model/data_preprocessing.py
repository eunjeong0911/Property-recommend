"""
전세 데이터 로딩 및 전처리 모듈
"""
import pandas as pd
import numpy as np
import re


def load_data(file_path: str, encoding: str = "utf-8") -> pd.DataFrame:
    """
    CSV 파일을 로드합니다.

    Args:
        file_path: CSV 파일 경로
        encoding: 파일 인코딩 (기본값: utf-8)

    Returns:
        pd.DataFrame: 로드된 데이터프레임
    """
    df = pd.read_csv(file_path, encoding=encoding)
    return df


def filter_jeonse_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    전세 데이터만 필터링합니다.

    Args:
        df: 원본 데이터프레임

    Returns:
        pd.DataFrame: 전세 데이터만 포함된 데이터프레임
    """
    df_jeonse = df[df['거래_정보.거래방식'].str.contains('전세', na=False)].copy()
    return df_jeonse


def parse_korean_money(text):
    """
    한국 화폐 단위 문자열을 만원 단위 숫자로 변환합니다.
    예: "1억 2,000만원" -> 12000

    Args:
        text: 한국 화폐 단위 문자열

    Returns:
        int: 만원 단위로 변환된 숫자
    """
    if pd.isna(text):
        return 0

    text = text.replace(",", "").strip()
    text = re.sub(r"[^\d억만]", "", text)

    if "억" in text:
        parts = text.split("억")
        eok = int(parts[0]) if parts[0] else 0
        man = 0
        if len(parts) > 1 and "만" in parts[1]:
            man = int(parts[1].replace("만", ""))
        return eok * 10000 + man

    numbers = re.findall(r"\d+", text)
    if numbers:
        return int(numbers[0])

    return 0


def extract_area(value):
    """
    전용/공급면적 문자열에서 전용면적(m²)만 추출합니다.
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


def extract_management_fee(value):
    """
    관리비 문자열에서 만원 단위 숫자를 추출합니다.
    예: '관리비 5만원' -> 5

    Args:
        value: 관리비 문자열

    Returns:
        int: 관리비 (만원 단위)
    """
    if pd.isna(value):
        return 0
    match = re.search(r'(\d+)\s*만원', str(value))
    return int(match.group(1)) if match else 0


def extract_floor(value):
    """
    층 정보 문자열에서 해당 층수를 추출합니다.
    예: '3층/10층' -> 3

    Args:
        value: 층 정보 문자열

    Returns:
        int or None: 해당 층수
    """
    if pd.isna(value):
        return None
    parts = str(value).split('/')
    match = re.search(r'-?\d+', parts[0])
    return int(match.group(0)) if match else None


def extract_gu_dong(addr):
    """
    주소 문자열에서 구와 동 정보를 추출합니다.

    Args:
        addr: 주소 문자열

    Returns:
        tuple: (구, 동)
    """
    if pd.isna(addr):
        return (None, None)
    addr = str(addr).strip()
    gu_match = re.search(r'(\S+구)', addr)
    dong_match = re.search(r'(\S+?\d*(동|가))', addr)
    gu = gu_match.group(1) if gu_match else None
    dong = dong_match.group(1) if dong_match else None
    return (gu, dong)


def remove_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    IQR 방법을 사용하여 이상치를 제거합니다.

    Args:
        df: 데이터프레임
        column: 이상치를 제거할 컬럼명

    Returns:
        pd.DataFrame: 이상치가 제거된 데이터프레임
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)].copy()
    return df


def preprocess_data(file_path: str) -> pd.DataFrame:
    """
    전체 데이터 전처리 파이프라인을 실행합니다.

    Args:
        file_path: CSV 파일 경로

    Returns:
        pd.DataFrame: 전처리된 데이터프레임
    """
    # 1. 데이터 로드
    df = load_data(file_path)

    # 2. 전세 데이터 필터링
    df_jeonse = filter_jeonse_data(df)

    # 3. 전세금 추출
    df_jeonse["전세금"] = df_jeonse["거래_정보.거래방식"].apply(parse_korean_money)

    # 4. 전용면적 추출
    df_jeonse["전용면적_m2"] = df_jeonse["매물_정보.전용/공급면적"].apply(extract_area)
    df_jeonse["전용면적_평"] = df_jeonse["전용면적_m2"] / 3.3

    # 5. 평당 전세금 계산 (타겟 변수)
    # 전세금을 전용면적으로 나눈 평당 전세금
    df_jeonse["평당가"] = df_jeonse["전세금"] / df_jeonse["전용면적_평"].replace(0, np.nan)

    # 6. 결측치 제거
    df_jeonse = df_jeonse.dropna(subset=["전용면적_평", "평당가"])

    # 7. 음수 및 0 제거
    df_jeonse = df_jeonse[df_jeonse["평당가"] > 0]

    # 8. 이상치 제거 (IQR 방법)
    df_jeonse = remove_outliers_iqr(df_jeonse, "평당가")

    # 9. 관리비 추출
    df_jeonse["관리비"] = df_jeonse["거래_정보.관리비"].apply(extract_management_fee)

    # 10. 층 정보 추출
    df_jeonse["층"] = df_jeonse["매물_정보.해당층/전체층"].apply(extract_floor)

    # 11. 방/욕실 개수 추출
    room_info = df_jeonse["매물_정보.방/욕실개수"].str.extract(
        r'(?P<방수>\d+)개/(?P<욕실수>\d+)개'
    )
    df_jeonse["방수"] = room_info["방수"].astype(float)
    df_jeonse["욕실수"] = room_info["욕실수"].astype(float)

    # 12. 구/동 추출
    df_jeonse["구"], df_jeonse["동"] = zip(*df_jeonse["주소_정보.전체주소"].apply(extract_gu_dong))

    # 13. 결측치 제거
    df_jeonse = df_jeonse.dropna(subset=["구", "동", "층", "방수", "욕실수"])

    return df_jeonse

