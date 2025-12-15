"""
02_create_features.py
중개사 신뢰도 모델 - Feature 생성 (12개 버전)
"""

import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# 1) 타겟 데이터 로드
# ============================================================
def load_target_data(filepath: str = "data/ML/office_target.csv") -> pd.DataFrame:
    file = Path(filepath)
    if not file.exists():
        raise FileNotFoundError(f"[ERROR] 파일이 존재하지 않음: {filepath}")

    print(f"📂 [1단계] 타겟 데이터 로드: {filepath}")
    df = pd.read_csv(file, encoding="utf-8-sig")
    print(f"   - 행 수: {len(df):,}")
    print(f"   - 열 수: {len(df.columns)}")

    return df


# ============================================================
# 2) Feature 생성 (12개)
# ============================================================
def create_features(df: pd.DataFrame):

    print("\n🔧 [2단계] Feature 생성 시작 (12개)")

    # ------------------------------------------------------------
    # 숫자형 변환
    # ------------------------------------------------------------
    df["거래완료_숫자"] = pd.to_numeric(df["거래완료_숫자"], errors="coerce").fillna(0)
    df["등록매물_숫자"] = pd.to_numeric(df["등록매물_숫자"], errors="coerce").fillna(0)
    df["공인중개사수"] = pd.to_numeric(df["공인중개사수"], errors="coerce").fillna(0)
    df["중개보조원수"] = pd.to_numeric(df["중개보조원수"], errors="coerce").fillna(0)
    df["일반직원수"] = pd.to_numeric(df["일반직원수"], errors="coerce").fillna(0)

    # ------------------------------------------------------------
    # 12개 Feature 생성
    # ------------------------------------------------------------
    
    # 1-3. 거래 지표
    df["거래완료_safe"] = df["거래완료_숫자"]
    df["등록매물_safe"] = df["등록매물_숫자"]
    df["총거래활동량"] = df["거래완료_safe"] + df["등록매물_safe"]
    
    # 4-6. 인력 지표
    df["총_직원수"] = df["공인중개사수"] + df["중개보조원수"] + df["일반직원수"]
    df["총_직원수_safe"] = df["총_직원수"].replace(0, 1)
    df["공인중개사_비율"] = df["공인중개사수"] / df["총_직원수_safe"]
    
    # 7-10. 운영 경험
    df["등록일"] = pd.to_datetime(df["등록일"], errors="coerce")
    today = pd.Timestamp.now()
    df["운영기간_일"] = (today - df["등록일"]).dt.days.clip(lower=0)
    df["운영기간_년"] = (df["운영기간_일"] / 365.25).fillna(0)
    
    df["운영경험_지수"] = np.exp(df["운영기간_년"] / 10)
    df["숙련도_지수"] = df["운영기간_년"] * df["공인중개사_비율"]
    df["운영_안정성"] = (df["운영기간_년"] >= 3).astype(int)
    
    # 11-12. 조직 구조
    df["대형사무소"] = (df["총_직원수"] >= 3).astype(int)
    df["직책_다양성"] = (
        (df["공인중개사수"] > 0).astype(int) +
        (df["중개보조원수"] > 0).astype(int) +
        (df.get("대표수", pd.Series([1] * len(df))) > 0).astype(int) +
        (df.get("일반직원수", pd.Series([0] * len(df))) > 0).astype(int)
    )
    
    # ------------------------------------------------------------
    # Feature 선택 (12개)
    # ------------------------------------------------------------
    selected_features = [
        # 거래 지표 (3개)
        "거래완료_safe",
        "등록매물_safe",
        "총거래활동량",
        
        # 인력 지표 (3개)
        "총_직원수",
        "공인중개사수",
        "공인중개사_비율",
        
        # 운영 경험 (4개)
        "운영기간_년",
        "운영경험_지수",
        "숙련도_지수",
        "운영_안정성",
        
        # 조직 구조 (2개)
        "대형사무소",
        "직책_다양성"
    ]
    
    # Feature 추출
    X = df[selected_features].copy()
    
    # 모든 컬럼을 숫자형으로 강제 변환
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    
    # Inf, -Inf, NaN 처리
    X = X.replace([np.inf, -np.inf], 0).fillna(0)
    
    # 타겟
    y = df["신뢰도등급"]
    
    print(f"✅ Feature 생성 완료:")
    print(f"   - Feature 수: {len(X.columns)}개")
    print(f"   - 데이터 수: {len(X)}개")
    print(f"   - X shape: {X.shape}")
    print(f"   - 결측치: {X.isna().sum().sum()}")
    
    print(f"\n📋 12개 Feature (데이터 누수 없음):")
    for i, feature in enumerate(X.columns, 1):
        print(f"   {i:2d}. {feature}")
    
    return df, X, y, list(X.columns)


# ============================================================
# 3) Feature 저장
# ============================================================
def save_features(df, filepath="data/ML/office_features.csv"):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"\n💾 [3단계] Feature 저장 완료 → {filepath}")


# ============================================================
# main
# ============================================================
def main():
    print("=" * 70)
    print(" " * 20 + "Feature 생성 (12개)")
    print("=" * 70)

    df = load_target_data()
    df, X, y, feature_cols = create_features(df)
    save_features(df)

    print("\n" + "=" * 70)
    print(" " * 25 + "완료!")
    print("=" * 70 + "\n")

    return df, X, y, feature_cols


if __name__ == "__main__":
    df, X, y, feature_cols = main()
