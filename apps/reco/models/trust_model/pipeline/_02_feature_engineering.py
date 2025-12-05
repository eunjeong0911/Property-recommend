import numpy as np

def add_features(df):
    """
    피처 엔지니어링: 기본 + 지역 + 고급 파생 피처 생성
    
    총 16개 피처:
    - 기본 피처 (2개)
    - 지역 피처 (3개)
    - 고급 파생 피처 (6개)
    - 원본 피처 (5개)
    """
    print("\n🔧 [3단계] 피처 엔지니어링")
    
    df = df.copy()

    # 기본 피처 (2개)
    df["등록비율"] = df["등록매물"] / (df["총매물수"] + 1e-6)
    df["규모지수"] = np.log1p(df["총매물수"])
    print("   ✅ 기본 피처 2개 생성")

    # 지역 기반 피처 (3개)
    df["지역내백분위"] = df.groupby("ldCodeNm")["거래완료"].rank(pct=True)
    
    region_counts = df.groupby("ldCodeNm").size()
    df["지역중개사수"] = df["ldCodeNm"].map(region_counts)
    print("   ✅ 지역 피처 2개 생성")

    # 고급 파생 피처 (6개) - 성능 향상의 핵심
    df["거래효율성"] = df["거래완료"] / (df["등록매물"] + 1e-6)
    df["매물활용도"] = df["거래완료"] / (df["총매물수"] + 1e-6)
    df["지역경쟁력"] = df["거래완료"] / (df["지역중개사수"] + 1e-6)
    df["상대적성과"] = df["거래완료"] / (df["지역권평균거래"] + 1e-6)
    df["log_거래완료"] = np.log1p(df["거래완료"])
    df["log_총매물수"] = np.log1p(df["총매물수"])
    print("   ✅ 고급 파생 피처 6개 생성")

    print(f"   📊 총 16개 피처 준비 완료")

    return df

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/seoul_broker_clean.csv")
    df = add_features(df)
