"""
[02] 피처 엔지니어링 모듈 (Binary Classification)
- 모델 학습용 피처(X) 생성
- 누수(Leakage) 없는 피처만 사용
"""
import pandas as pd
import numpy as np



def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """피처 생성"""
    print("\n[피처 엔지니어링] 파생 변수 생성 중...")
    
    # 전처리
    df["총매물수"] = df["총매물수"].fillna(1)
    
    for col in ["총_직원수", "공인중개사수", "중개보조원수", "대표수"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    df["총_직원수"] = df["총_직원수"].replace(0, 1)
    
    # 기본 비율
    df["공인중개사비율"] = df["공인중개사수"] / df["총_직원수"]
    df["중개보조원비율"] = df["중개보조원수"] / df["총_직원수"]
    
    # 운영 기간
    if "등록일" in df.columns:
        df["등록일"] = pd.to_datetime(df["등록일"], errors="coerce")
        today = pd.Timestamp.now()
        df["운영일수"] = (today - df["등록일"]).dt.days.clip(lower=0)
        df["운영연수"] = df["운영일수"] / 365.25
        df["운영로그"] = np.log1p(df["운영일수"])
        df["연차구간"] = pd.cut(df["운영연수"], bins=[-1, 1, 3, 5, 100], labels=[0, 1, 2, 3]).astype(int)
    else:
        for c in ["운영일수", "운영연수", "운영로그", "연차구간"]:
            df[c] = 0
    
    # 규모/전문성
    df["대형"] = (df["총_직원수"] >= 5).astype(int)
    df["중형"] = ((df["총_직원수"] >= 3) & (df["총_직원수"] < 5)).astype(int)
    df["소형"] = (df["총_직원수"] <= 2).astype(int)
    df["복수자격"] = (df["공인중개사수"] >= 2).astype(int)
    df["전원자격"] = ((df["공인중개사수"] > 0) & (df["중개보조원수"] == 0)).astype(int)
    
    # 파생 피처 (누수 없음)
    df["전문인력밀도"] = df["공인중개사수"] / df["총_직원수"]
    df["경력전문성"] = df["운영연수"] * df["공인중개사비율"]
    df["규모연차"] = np.log1p(df["총_직원수"]) * df["운영연수"]
    df["경력규모"] = df["운영연수"] * df["총_직원수"]
    df["보조자격비"] = df["중개보조원수"] / df["공인중개사수"].replace(0, 1)
    df["보조자격비"] = df["보조자격비"].fillna(0).replace([np.inf, -np.inf], 0)
    df["비자격비"] = (df["총_직원수"] - df["공인중개사수"]) / df["총_직원수"]
    df["비자격비"] = df["비자격비"].fillna(0).clip(lower=0)
    
    return df


def select_features(df: pd.DataFrame):
    """피처 선택 (누수 방지)"""
    print("[피처 엔지니어링] 피처 선택 중...")
    
    feature_map = {
        "총_직원수": "직원수",
        "공인중개사수": "공인중개사",
        "중개보조원수": "중개보조원",
        "공인중개사비율": "공인중개사비율",
        "중개보조원비율": "중개보조원비율",
        "복수자격": "복수자격",
        "전원자격": "전원자격",
        "대형": "대형",
        "중형": "중형",
        "소형": "소형",
        "운영연수": "운영연수",
        "운영로그": "운영로그",
        "연차구간": "연차구간",
        "전문인력밀도": "전문밀도",
        "경력전문성": "경력전문",
        "규모연차": "규모연차",
        "경력규모": "경력규모",
        "보조자격비": "보조비",
        "비자격비": "비자격비",
    }
    
    available_cols = [col for col in feature_map.keys() if col in df.columns]
    X = df[available_cols].copy().rename(columns=feature_map)
    X = X.select_dtypes(include=[np.number])
    X = X.fillna(0).replace([np.inf, -np.inf], 0)
    
    return X, list(X.columns)


def main(df: pd.DataFrame):
    """피처 엔지니어링 메인"""
    df_enriched = create_features(df)
    X, feature_names = select_features(df_enriched)
    
    print(f"\n✅ 피처 생성 완료: {X.shape}")
    print(f"✅ 피처 목록: {feature_names}")
    
    return df_enriched, X, feature_names


if __name__ == "__main__":
    from _00_load_data import load_processed_office_data
    
    print("=== 피처 엔지니어링 테스트 (Binary) ===")
    raw_df = load_processed_office_data()
    df_result, X_result, feats = main(raw_df)
    print("\n[샘플 데이터]")
    print(X_result.head())
