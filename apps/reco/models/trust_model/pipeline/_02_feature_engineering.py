# _02_feature_engineering.py
import numpy as np

def add_features(df):
    print("\n🔧 [3단계] 피처 엔지니어링")
    
    df = df.copy()

    # 기본 피처
    df["등록비율"] = df["등록매물"] / (df["총매물수"] + 1e-6)
    df["규모지수"] = np.log1p(df["총매물수"])

    # 지역 기반 피처
    df["지역내순위"] = df.groupby("ldCodeNm")["거래완료"].rank(ascending=False, method='min')
    df["지역내백분위"] = df.groupby("ldCodeNm")["거래완료"].rank(pct=True)
    
    region_counts = df.groupby("ldCodeNm").size()
    df["지역중개사수"] = df["ldCodeNm"].map(region_counts)
    
    region_mean_deal = df.groupby("ldCodeNm")["거래완료"].mean()
    df["지역평균대비거래비율"] = df["거래완료"] / df["ldCodeNm"].map(region_mean_deal)

    print(f"   ✅ 6개 피처 생성 완료 (기본 2개 + 지역 4개)")

    return df

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/seoul_broker_clean.csv")
    df = add_features(df)
