import pandas as pd
import numpy as np

def create_regression_target(df):
    """
    회귀 문제를 위한 타겟 생성
    
    규칙 기반 라벨 대신, 실제 데이터를 조합한 신뢰도 점수 생성
    """
    print("\n📊 [2단계] 회귀 타겟 생성 (실제 데이터 기반)")

    df = df.copy()

    # 날짜 변환
    df["registDe"] = pd.to_datetime(df["registDe"])
    df["estbsEndDe"] = pd.to_datetime(df["estbsEndDe"], errors="coerce")
    today = pd.Timestamp.today()

    # 기본 지표 계산
    df["영업일수"] = (today - df["registDe"]).dt.days.clip(lower=1)
    df["일평균거래"] = df["거래완료"] / (df["영업일수"] + 1e-6)
    df["보증보험유효"] = (df["estbsEndDe"] >= today).astype(int)
    df["거래성사율"] = df["거래완료"] / (df["총매물수"] + 1e-6)
    
    # 지역 평균
    region_mean = df.groupby("ldCodeNm")["거래완료"].mean()
    df["지역권평균거래"] = df["ldCodeNm"].map(region_mean)

    # 타겟: 종합 신뢰도 점수 (연속형)
    # 여러 실제 지표를 조합하여 생성
    df["trust_target"] = (
        df["거래완료"] * 0.4 +                    # 실제 거래 실적 40%
        df["거래성사율"] * 100 * 0.3 +            # 성사율 30%
        df["일평균거래"] * 50 * 0.2 +             # 활동성 20%
        df["보증보험유효"] * 10 * 0.1             # 안전성 10%
    )

    print(f"   ✅ 회귀 타겟 생성 완료")
    print(f"   - 타겟: trust_target (연속형 점수)")
    print(f"   - 평균: {df['trust_target'].mean():.2f}")
    print(f"   - 범위: {df['trust_target'].min():.2f} ~ {df['trust_target'].max():.2f}")
    print(f"   - 표준편차: {df['trust_target'].std():.2f}")

    return df


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/seoul_broker_clean.csv")
    df = create_regression_target(df)
