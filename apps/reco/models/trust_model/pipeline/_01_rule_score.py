# _01_rule_score.py
import pandas as pd

def apply_rule_score(df):
    print("\n📊 [2단계] 룰 기반 스코어링")

    df = df.copy()

    # 날짜 변환
    df["registDe"] = pd.to_datetime(df["registDe"])
    df["estbsEndDe"] = pd.to_datetime(df["estbsEndDe"], errors="coerce")

    today = pd.Timestamp.today()

    # 영업일수 계산
    if "영업일수" not in df.columns:
        df["영업일수"] = (today - df["registDe"]).dt.days.clip(lower=1)

    # 일평균 거래
    df["일평균거래"] = df["거래완료"] / (df["영업일수"] + 1e-6)

    # 보증보험유효 여부
    df["보증보험유효"] = (df["estbsEndDe"] >= today).astype(int)

    # 지역 평균 성사율 계산
    df["거래성사율"] = df["거래완료"] / (df["총매물수"] + 1e-6)
    region_mean = df.groupby("ldCodeNm")["거래성사율"].mean()
    df["지역권평균성사율"] = df["ldCodeNm"].map(region_mean)

    # Rule Score 계산
    df["rule_score"] = (
        df["거래성사율"] * 40 +
        df["일평균거래"] * 30 +
        df["보증보험유효"] * 20 +
        df["지역권평균성사율"] * 10
    )

    # Rule 등급 (Quantile 기반)
    df["grade"] = pd.qcut(
        df["rule_score"], 
        q=5, 
        labels=["D", "C", "B", "A", "S"],
        duplicates='drop'
    )

    print(f"   ✅ Rule Score 생성 (평균: {df['rule_score'].mean():.1f})")
    print(f"   ✅ 등급 분류 완료 (각 등급 20%씩)")

    return df

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/seoul_broker_clean.csv")
    df = apply_rule_score(df)
