"""
전세 가격 예측 모델을 위한 특성 엔지니어링 모듈
"""
import pandas as pd
import numpy as np
import re
from sklearn.model_selection import KFold
from sklearn.preprocessing import LabelEncoder


def extract_total_floor(value):
    """
    층 정보 문자열에서 전체 층수를 추출합니다.
    예: '3층/10층' -> 10

    Args:
        value: 층 정보 문자열

    Returns:
        int or None: 전체 층수
    """
    if pd.isna(value):
        return None
    parts = str(value).split('/')
    if len(parts) > 1:
        match = re.search(r'\d+', parts[1])
        return int(match.group(0)) if match else None
    return None


def add_floor_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    층 관련 특성을 추가합니다.
    - 전체층수
    - 층_비율 (해당층 / 전체층)
    - 층_카테고리 (저층/중층/고층)

    Args:
        df: 데이터프레임

    Returns:
        pd.DataFrame: 층 관련 특성이 추가된 데이터프레임
    """
    # 전체 층수 추출
    df['전체층수'] = df["매물_정보.해당층/전체층"].apply(extract_total_floor)

    # 층수 비율 (해당층 / 전체층)
    df['층_비율'] = df['층'] / df['전체층수'].replace(0, np.nan)

    # 저층/중층/고층 구분
    df['층_카테고리'] = pd.cut(
        df['층_비율'],
        bins=[0, 0.3, 0.7, 1.0],
        labels=['저층', '중층', '고층']
    )

    return df


def add_area_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    면적 관련 특성을 추가합니다.
    - 평수_구간 (소형/중형/대형)
    - 평당_방수 (방수 / 전용면적_평)

    Args:
        df: 데이터프레임

    Returns:
        pd.DataFrame: 면적 관련 특성이 추가된 데이터프레임
    """
    # 평수 구간 (소형/중형/대형)
    df['평수_구간'] = pd.cut(
        df['전용면적_평'],
        bins=[0, 20, 30, 100],
        labels=['소형', '중형', '대형']
    )

    # 방수 대비 평수 (평당 방 개수)
    df['평당_방수'] = df['방수'] / df['전용면적_평'].replace(0, np.nan)

    return df


def add_management_fee_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    관리비 관련 특성을 추가합니다.
    - 평당_관리비 (관리비 / 전용면적_평)

    Args:
        df: 데이터프레임

    Returns:
        pd.DataFrame: 관리비 관련 특성이 추가된 데이터프레임
    """
    # 평당 관리비
    df['평당_관리비'] = df['관리비'] / df['전용면적_평'].replace(0, np.nan)

    return df


def target_encode_loo(df, col, target):
    """
    Leave-One-Out Target Encoding
    각 행에 대해 자기 자신을 제외한 카테고리 평균을 계산합니다.

    Args:
        df: 데이터프레임
        col: 인코딩할 카테고리 컬럼명
        target: 타겟 변수 컬럼명

    Returns:
        list: 인코딩된 값 리스트
    """
    global_mean = df[target].mean()
    agg = df.groupby(col)[target].agg(['sum', 'count'])

    encoded = []
    for idx, row in df.iterrows():
        cat = row[col]
        target_val = row[target]

        # 해당 카테고리의 합계에서 현재 값을 빼고, 개수도 -1
        cat_sum = agg.loc[cat, 'sum'] - target_val
        cat_count = agg.loc[cat, 'count'] - 1

        # 개수가 0이면 전체 평균 사용
        if cat_count == 0:
            encoded.append(global_mean)
        else:
            encoded.append(cat_sum / cat_count)

    return encoded


def target_encode_oof(df, col, target, n_splits=5, random_state=42):
    """
    Out-of-Fold Target Encoding
    K-Fold 교차 검증을 사용하여 타깃 누수를 완전히 방지합니다.

    Args:
        df: 데이터프레임
        col: 인코딩할 카테고리 컬럼명
        target: 타겟 변수 컬럼명
        n_splits: K-Fold 분할 수
        random_state: 랜덤 시드

    Returns:
        pd.Series: 인코딩된 값 시리즈
    """
    df = df.copy()
    df[f'{col}_target_enc_oof'] = 0.0

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    for fold, (train_idx, val_idx) in enumerate(kf.split(df)):
        # 각 폴드의 학습 데이터로만 평균 계산
        train_fold = df.iloc[train_idx]
        global_mean = train_fold[target].mean()

        # 카테고리별 평균 계산
        category_mean = train_fold.groupby(col)[target].mean()

        # 검증 데이터에 인코딩 적용
        for val_i in val_idx:
            cat = df.iloc[val_i][col]
            if cat in category_mean.index:
                df.iloc[val_i, df.columns.get_loc(f'{col}_target_enc_oof')] = category_mean[cat]
            else:
                df.iloc[val_i, df.columns.get_loc(f'{col}_target_enc_oof')] = global_mean

    return df[f'{col}_target_enc_oof']


def add_location_features(df: pd.DataFrame, use_oof: bool = False) -> pd.DataFrame:
    """
    위치 관련 특성을 추가합니다.
    - 구_빈도: 구별 데이터 빈도
    - 동_빈도: 동별 데이터 빈도
    - 구_target_enc: 구별 Target Encoding
    - 동_target_enc: 동별 Target Encoding

    Args:
        df: 데이터프레임
        use_oof: Out-of-Fold Target Encoding 사용 여부 (기본값: False, Leave-One-Out 사용)

    Returns:
        pd.DataFrame: 위치 관련 특성이 추가된 데이터프레임
    """
    # 구/동 빈도 인코딩
    gu_freq = df['구'].value_counts() / len(df)
    dong_freq = df['동'].value_counts() / len(df)
    df['구_빈도'] = df['구'].map(gu_freq)
    df['동_빈도'] = df['동'].map(dong_freq)

    # Target Encoding
    if use_oof:
        # Out-of-Fold Target Encoding (타깃 누수 완전 방지)
        df['구_target_enc'] = target_encode_oof(df, '구', '평당가', n_splits=5)
        df['동_target_enc'] = target_encode_oof(df, '동', '평당가', n_splits=5)
    else:
        # Leave-One-Out Target Encoding
        df['구_target_enc'] = target_encode_loo(df, '구', '평당가')
        df['동_target_enc'] = target_encode_loo(df, '동', '평당가')

    return df


def create_all_features(df: pd.DataFrame, use_oof_target_encoding: bool = False) -> pd.DataFrame:
    """
    모든 특성 엔지니어링을 순차적으로 수행합니다.

    Args:
        df: 전처리된 데이터프레임
        use_oof_target_encoding: Out-of-Fold Target Encoding 사용 여부

    Returns:
        pd.DataFrame: 모든 특성이 추가된 데이터프레임
    """
    # 1. 층 관련 특성
    df = add_floor_features(df)

    # 2. 면적 관련 특성
    df = add_area_features(df)

    # 3. 관리비 관련 특성
    df = add_management_fee_features(df)

    # 4. 위치 관련 특성
    df = add_location_features(df, use_oof=use_oof_target_encoding)

    return df


def prepare_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    머신러닝 모델 학습을 위한 최종 특성 데이터프레임을 생성합니다.

    Args:
        df: 특성 엔지니어링이 완료된 데이터프레임

    Returns:
        pd.DataFrame: 모델 학습용 특성 데이터프레임
    """
    # 사용할 특성 목록
    feature_cols = [
        "평당가",  # 타겟 변수
        "전용면적_평",
        "전용면적_m2",
        "관리비",
        "층",
        "방수",
        "욕실수",
        "전체층수",
        "층_비율",
        "평당_방수",
        "평당_관리비",
        "구_빈도",
        "동_빈도",
        "구_target_enc",
        "동_target_enc"
    ]

    # 결측치 제거
    df = df.dropna(subset=feature_cols)

    # ML용 DataFrame 생성
    df_ml = df[feature_cols].copy()

    return df_ml

