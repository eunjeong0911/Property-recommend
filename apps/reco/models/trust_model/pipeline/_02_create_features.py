"""
02_create_features.py
중개사 신뢰도 모델 - Feature 생성
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
# 2) Feature (12개)
# ============================================================
def create_features(df: pd.DataFrame):

    print("\n🔧 [2단계] Feature ")

    # ------------------------------------------------------------
    # 숫자형 변환
    # ------------------------------------------------------------
    df["거래완료_숫자"] = pd.to_numeric(df["거래완료_숫자"], errors="coerce")
    df["등록매물_숫자"] = pd.to_numeric(df["등록매물_숫자"], errors="coerce")
    df["공인중개사수"] = pd.to_numeric(df["공인중개사수"], errors="coerce")
    df["중개보조원수"] = pd.to_numeric(df["중개보조원수"], errors="coerce")
    df["총_직원수"] = pd.to_numeric(df["총_직원수"], errors="coerce")

    # ------------------------------------------------------------
    # 12개 Feature 생성
    # ------------------------------------------------------------
    
    # 1-3. 거래 지표 (로그 변환 + 스케일링 조정)
    df["거래완료_safe"] = df["거래완료_숫자"]
    df["등록매물_safe"] = df["등록매물_숫자"]
    df["총거래활동량"] = df["거래완료_safe"] + df["등록매물_safe"]
    
    # 로그 변환 + 제곱근 + 세제곱근 + 극초강 스케일링으로 중요도 완전 억제
    df["거래완료_log"] = np.power(np.sqrt(np.log1p(df["거래완료_safe"])), 1/3) * 0.001  # 0.1% 스케일링 (완전 억제)
    df["등록매물_log"] = np.power(np.sqrt(np.log1p(df["등록매물_safe"])), 1/3) * 0.001   # 0.1% 스케일링 (완전 억제)
    df["총거래활동량_log"] = np.power(np.sqrt(np.log1p(df["총거래활동량"])), 1/3) * 0.0005  # 0.05% 스케일링 (초완전 억제)
    
    # 4-6. 인력 지표
    df["총_직원수"] = df["총_직원수"]
    df["공인중개사_비율"] = df["공인중개사수"] / df["총_직원수"]
    
    # 7-10. 운영 경험
    df["등록일"] = pd.to_datetime(df["등록일"], errors="coerce")
    today = pd.Timestamp.now()
    df["운영기간_일"] = (today - df["등록일"]).dt.days.clip(lower=0)
    df["운영기간_년"] = (df["운영기간_일"] / 365.25).fillna(0)
    
    df["운영경험_지수"] = np.exp(df["운영기간_년"] / 10)
    df["숙련도_지수"] = df["운영기간_년"] * df["공인중개사_비율"]  # 원본 비율 사용
    df["운영_안정성"] = (df["운영기간_년"] >= 3).astype(int)
    
    # 11-12. 조직 구조 (가중치 강화)
    df["대형사무소"] = (df["총_직원수"] >= 2).astype(int)
    df["직책_다양성"] = (
        (df["공인중개사수"] > 0).astype(int) +
        (df["중개보조원수"] > 0).astype(int) +
        (df.get("대표수", pd.Series([1] * len(df))) > 0).astype(int) +
        (df.get("일반직원수", pd.Series([0] * len(df))) > 0).astype(int)
    )
    
    # 조직 구조 가중치 강화 (3배)
    df["대형사무소"] = df["대형사무소"] * 3.0
    df["직책_다양성"] = df["직책_다양성"] * 3.0
    
    # 13-16. 대표자 구분 (원-핫 인코딩)
    # 모든 데이터에 대표자구분명이 있다고 가정
    
    # 각 대표자 유형별 이진 Feature 생성
    df["대표_공인중개사"] = (df["대표자구분명"] == "공인중개사").astype(int)
    df["대표_법인"] = (df["대표자구분명"] == "법인").astype(int)
    df["대표_중개인"] = (df["대표자구분명"] == "중개인").astype(int)
    df["대표_중개보조원"] = (df["대표자구분명"] == "중개보조원").astype(int)
    
    # ============================================================
    # 가중치 조정 (모든 피처 계산 완료 후)
    # ============================================================
    print("\n⚖️ 가중치 조정 적용 중...")
    
    # 인력 지표 가중치 강화 (2배)
    df["총_직원수"] = df["총_직원수"] * 2.0
    df["공인중개사수"] = df["공인중개사수"] * 2.0
    df["공인중개사_비율"] = df["공인중개사_비율"] * 2.0
    print("   📈 인력 지표 (3개): 2배 강화")
    
    # 운영 경험 가중치 강화 (2.5배)
    df["운영기간_년"] = df["운영기간_년"] * 2.5
    df["운영경험_지수"] = df["운영경험_지수"] * 2.5
    df["숙련도_지수"] = df["숙련도_지수"] * 2.5
    df["운영_안정성"] = df["운영_안정성"] * 2.5
    print("   📈 운영 경험 (4개): 2.5배 강화")
    
    # 조직 구조 가중치 강화 (3배)
    df["대형사무소"] = df["대형사무소"] * 3.0
    df["직책_다양성"] = df["직책_다양성"] * 3.0
    print("   📈 조직 구조 (2개): 3배 강화")
    
    # 대표자 구분 가중치 강화 (2배)
    df["대표_공인중개사"] = df["대표_공인중개사"] * 2.0
    df["대표_법인"] = df["대표_법인"] * 2.0
    df["대표_중개인"] = df["대표_중개인"] * 2.0
    df["대표_중개보조원"] = df["대표_중개보조원"] * 2.0
    print("   📈 대표자 구분 (4개): 2배 강화")
    
    print("   📉 거래 지표 (3개): 로그+제곱근+세제곱근+극초강억제 (0.05-0.1%)")
    print("   ✅ 가중치 조정 완료")
    
    # ------------------------------------------------------------
    # Feature 선택 (16개) - 거래 지표 강력 억제
    # ------------------------------------------------------------
    selected_features = [
        # 거래 지표 (3개) - 로그 변환 + 스케일링으로 중요도 억제
        "거래완료_log",
        "등록매물_log", 
        "총거래활동량_log",
        
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
        "직책_다양성",
        
        # 대표자 구분 (4개) - 모든 카테고리 포함 (다중공선성 테스트)
        "대표_공인중개사",
        "대표_법인",
        "대표_중개인",
        "대표_중개보조원"
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
    
    print(f"\n📋 {len(X.columns)}개 Feature (거래 억제 + 다른 피처 강화 + 대표_공인중개사 포함):")
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
    print(" " * 20 + "Feature 생성 (15개)")
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
