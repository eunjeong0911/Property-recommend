import pandas as pd
import numpy as np

def create_regression_target(df):
    """
    다중 분류 문제를 위한 타겟 생성: 중개사 등급 분류
    
    Target: 3등급 (A, B, C)
    - 기준: 거래성사율 분위수
    - A: 상위 33% (우수)
    - B: 중위 33% (보통)
    - C: 하위 33% (미흡)
    """
    print("\n📊 [2단계] 다중 분류 타겟 생성 (3등급)")

    df = df.copy()

    # 날짜 변환
    df["registDe"] = pd.to_datetime(df["registDe"])
    df["estbsEndDe"] = pd.to_datetime(df["estbsEndDe"], errors="coerce")
    today = pd.Timestamp.today()

    # 기본 지표 계산
    df["영업일수"] = (today - df["registDe"]).dt.days.clip(lower=1)
    df["보증보험유효"] = (df["estbsEndDe"] >= today).astype(int)

    # 거래 성사율 계산 (중간 단계)
    df["거래성사율"] = df["거래완료"] / (df["총매물수"] + 1e-6) * 100

    # 타겟: 3등급 분류 (분위수 기반)
    # 각 등급이 균등하게 분포 (33%씩)
    df["trust_target"] = pd.qcut(
        df["거래성사율"],
        q=3,
        labels=["C", "B", "A"],
        duplicates='drop'
    )

    print(f"   ✅ 분류 타겟 생성 완료")
    print(f"   - 타겟: trust_target (3등급 분류)")
    print(f"   - 기준: 거래성사율 분위수")
    print(f"   - A: 상위 33% (우수)")
    print(f"   - B: 중위 33% (보통)")
    print(f"   - C: 하위 33% (미흡)")
    print(f"\n   등급 분포:")
    print(df["trust_target"].value_counts().sort_index())
    print(f"\n   거래성사율 통계:")
    print(f"   - 평균: {df['거래성사율'].mean():.2f}%")
    print(f"   - 범위: {df['거래성사율'].min():.2f}% ~ {df['거래성사율'].max():.2f}%")
    
    # 각 등급의 성사율 범위 출력
    for grade in ["A", "B", "C"]:
        grade_data = df[df["trust_target"] == grade]["거래성사율"]
        if len(grade_data) > 0:
            print(f"   - {grade}등급: {grade_data.min():.1f}% ~ {grade_data.max():.1f}%")
    
    print(f"\n   ✅ Feature에서 거래완료 정보 제외 필요")

    return df


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/raw/seoul_broker_final.csv") # data 경로 변경 및 파일명 변경 clean ->  merged
    df = create_regression_target(df)
