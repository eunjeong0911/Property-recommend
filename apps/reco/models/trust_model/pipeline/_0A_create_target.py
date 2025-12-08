import pandas as pd
import numpy as np

def create_binary_target(df):
    """
    이진 분류 문제를 위한 타겟 생성: 중개사 등급 분류
    
    Target:
      - trust_target: 2등급 (A=고수, B=신입)
      - trust_binary: 0/1 (신입/고수)
    기준:
      - A: 거래성사율 90% 이상 (고수)
      - B: 나머지 (신입)
    """
    print("\n📊 [2단계] 이진 분류 타겟 생성 (2등급)")

    df = df.copy()

    # 날짜 변환
    df["registDe"] = pd.to_datetime(df["registDe"])
    df["estbsEndDe"] = pd.to_datetime(df["estbsEndDe"], errors="coerce")
    today = pd.Timestamp.today()

    # 기본 지표 계산
    df["영업일수"] = (today - df["registDe"]).dt.days.clip(lower=1)
    df["보증보험유효"] = (df["estbsEndDe"] >= today).astype(int)

    # 거래 성사율 계산 (중간 단계, 0~100 %)
    df["거래성사율"] = df["거래완료"] / (df["총매물수"] + 1e-6) * 100

    # 🔑 절대 기준: 거래성사율 90% 이상 = 고수(A)
    high_threshold = 90.0

    # trust_target: A = 거래성사율 90% 이상, B = 나머지
    df["trust_target"] = np.where(df["거래성사율"] >= high_threshold, "A", "B")

    # trust_binary: A=1(고수), B=0(신입)
    df["trust_binary"] = (df["거래성사율"] >= high_threshold).astype(int)

    print("   ✅ 분류 타겟 생성 완료")
    print("   - 타겟1: trust_target (A/B)")
    print("   - 타겟2: trust_binary (0/1)")
    print(f"   - 기준: 거래성사율 {high_threshold:.2f}% 이상 = A / 1")

    print("\n   등급 분포:")
    print(df["trust_target"].value_counts().sort_index())

    print("\n   이진 타겟 분포:")
    print(df["trust_binary"].value_counts().rename(index={0: "0 (신입/B)", 1: "1 (고수/A)"}))

    print("\n   거래성사율 통계:")
    print(f"   - 평균: {df['거래성사율'].mean():.2f}%")
    print(f"   - 범위: {df['거래성사율'].min():.2f}% ~ {df['거래성사율'].max():.2f}%")

    for grade in ["A", "B"]:
        grade_data = df[df["trust_target"] == grade]["거래성사율"]
        if len(grade_data) > 0:
            print(f"   - {grade}등급: {grade_data.min():.1f}% ~ {grade_data.max():.1f}% (n={len(grade_data)})")

    print("\n   ✅ Feature에서 거래완료 정보 제외 필요")

    return df


if __name__ == "__main__":
    df = pd.read_csv("data/raw/seoul_broker_final.csv")
    df = create_binary_target(df)