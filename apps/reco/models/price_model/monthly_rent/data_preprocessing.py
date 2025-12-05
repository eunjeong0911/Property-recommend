"""
데이터 로딩 및 전처리 모듈
"""
import json
from pathlib import Path
from typing import Iterable, List, Union

import pandas as pd

PathInput = Union[str, Path]
FileInput = Union[PathInput, Iterable[PathInput]]


def _normalize_file_inputs(file_path: FileInput) -> List[Path]:
    """파일 경로 입력을 Path 리스트로 정규화합니다."""
    if isinstance(file_path, (str, Path)):
        return [Path(file_path)]

    if isinstance(file_path, Iterable):
        paths: List[Path] = []
        for item in file_path:
            if isinstance(item, (str, Path)):
                paths.append(Path(item))
            else:
                raise TypeError("file_path의 항목은 문자열 또는 Path 여야 합니다.")

        if not paths:
            raise ValueError("최소 한 개 이상의 데이터 파일 경로가 필요합니다.")
        return paths

    raise TypeError("file_path는 문자열/Path 또는 그들의 Iterable 이어야 합니다.")


def load_data(file_path: FileInput, encoding: str = "utf-8") -> pd.DataFrame:
    """
    CSV 또는 JSON 파일(복수 가능)을 로드합니다.

    Args:
        file_path: 단일 경로 혹은 경로 리스트
        encoding: 파일 인코딩 (기본값: utf-8)

    Returns:
        pd.DataFrame: 로드된 데이터프레임
    """
    paths = _normalize_file_inputs(file_path)
    frames: List[pd.DataFrame] = []

    for path in paths:
        resolved = Path(path)
        if not resolved.exists():
            raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {resolved}")

        suffix = resolved.suffix.lower()
        if suffix == ".json":
            with resolved.open("r", encoding=encoding) as f:
                raw = json.load(f)
            df = pd.json_normalize(raw, sep='.')
        else:
            df = pd.read_csv(resolved, encoding=encoding)

        frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def filter_walse_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    월세 데이터만 필터링합니다.

    Args:
        df: 원본 데이터프레임

    Returns:
        pd.DataFrame: 월세 데이터만 포함된 데이터프레임
    """
    df_walse = df[df['거래_정보.거래방식'].str.contains('월세', na=False)].copy()
    return df_walse


def drop_unnecessary_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    불필요한 컬럼을 제거합니다.

    Args:
        df: 데이터프레임

    Returns:
        pd.DataFrame: 필요한 컬럼만 남긴 데이터프레임
    """
    columns_to_drop = [
        "매물번호", "평면도_URL", "매물_이미지", "매물_URL",
        "주변_학교", "거래_정보.융자금", "거래_정보.입주가능일",
        "매물_정보.전입신고 여부", "매물_정보.현관유형",
        "매물_정보.총세대수", "매물_정보.총주차대수",
        "매물_정보.난방방식", "매물_정보.냉방시설", "매물_정보.보안시설",
        "중개사_정보.중개사명", "중개사_정보.대표자", "중개사_정보.전화번호",
        "중개사_정보.주소", "중개사_정보.등록번호", "중개사_정보.거래완료",
        "중개사_정보.등록매물", "매물_정보.건물명", "매물_정보.동",
        "매물_정보.계약기간", "매물_정보.연/대지면적", "매물_정보.용적률/건쳬율",
        "매물_정보.준공인가일", "중개사_정보.담당자", "매물_정보.사용검사일",
        " 매물_정보.건축/전용면적", "매물_정보.용적률/건폐율", "매물_정보.지상/지하총층",
        "매물_정보.오피스텔명", "매물_정보.아파트명", "매물_정보.사용승인일"
    ]

    df = df.drop(columns=columns_to_drop, errors="ignore")
    return df


def remove_invalid_room_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    방/욕실 개수가 유효하지 않은 데이터를 제거합니다.
    - 방수 == 0
    - 욕실수 >= 3
    - 파싱 실패한 데이터

    Args:
        df: 데이터프레임

    Returns:
        pd.DataFrame: 유효한 방/욕실 데이터만 포함된 데이터프레임
    """
    # 방/욕실개수에서 숫자 추출
    tmp = df["매물_정보.방/욕실개수"].str.extract(
        r'(?P<방수>\d+)개/(?P<욕실수>\d+)개'
    )

    # 숫자로 변환
    tmp = tmp.astype(float)

    # 제거할 조건 정의
    cond_bad = (
        (tmp["방수"] == 0) |
        (tmp["욕실수"] >= 3) |
        tmp.isna().any(axis=1)
    )

    # 필터링
    df = df[~cond_bad].copy()

    return df


def remove_null_dong(df: pd.DataFrame) -> pd.DataFrame:
    """
    '동' 정보가 없는 데이터를 제거합니다.

    Args:
        df: 데이터프레임

    Returns:
        pd.DataFrame: '동' 정보가 있는 데이터만 포함된 데이터프레임
    """
    df = df[df['동'].notna()].copy()
    return df


def preprocess_data(file_path: FileInput) -> pd.DataFrame:
    """
    전체 데이터 전처리 파이프라인을 실행합니다.

    Args:
        file_path: CSV 파일 경로

    Returns:
        pd.DataFrame: 전처리된 데이터프레임
    """
    # 1. 데이터 로드
    df = load_data(file_path)

    # 2. 월세 데이터 필터링
    df_walse = filter_walse_data(df)

    # 3. 불필요한 컬럼 제거
    df_walse = drop_unnecessary_columns(df_walse)

    return df_walse
