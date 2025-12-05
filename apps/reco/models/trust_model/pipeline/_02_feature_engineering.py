import numpy as np
import pandas as pd

def add_features(df):
    """
    피처 엔지니어링: 거래 성사율 예측을 위한 다양한 피처 생성 (개선 버전)
    
    총 15개 피처:
    - 매물 정보 (1개): 등록매물
    - 시간 정보 (6개): 영업일수, 영업년수, 등록일_년, 등록일_월, 계절, 보증보험_남은일수
    - 지역 정보 (4개): 지역중개사수, 지역내_등록매물_순위, 지역_평균영업년수, 지역_매물밀도
    - 안전성 (1개): 보증보험유효
    - 파생 피처 (3개): 매물_규모_지수, 지역_경쟁_강도, 영업년수_매물_상호작용
    
    ❌ 제거된 피처 (Data Leakage 방지):
    - 거래완료 (Target 계산에 직접 사용)
    - 총매물수 = 등록매물 + 거래완료
    - 거래완료 기반 모든 파생 피처
    """
    print("\n🔧 [3단계] 피처 엔지니어링 (개선 버전 - 15개 피처)")
    
    df = df.copy()

    # 시간 기반 피처 (6개)
    df["등록일_년"] = df["registDe"].dt.year
    df["등록일_월"] = df["registDe"].dt.month
    
    # 계절 (1~12월 → 봄/여름/가을/겨울)
    df["계절"] = df["등록일_월"].map({
        12: 0, 1: 0, 2: 0,  # 겨울
        3: 1, 4: 1, 5: 1,   # 봄
        6: 2, 7: 2, 8: 2,   # 여름
        9: 3, 10: 3, 11: 3  # 가을
    })
    
    # 보증보험 남은 일수
    today = pd.Timestamp.today()
    df["보증보험_남은일수"] = (df["estbsEndDe"] - today).dt.days.clip(lower=0)
    
    print("   ✅ 시간 피처 6개 (영업일수, 영업년수, 등록일_년, 등록일_월, 계절, 보증보험_남은일수)")

    # 지역 기반 피처 (4개)
    region_counts = df.groupby("ldCodeNm").size()
    df["지역중개사수"] = df["ldCodeNm"].map(region_counts)
    
    # 지역 내 등록매물 순위 (백분위)
    df["지역내_등록매물_순위"] = df.groupby("ldCodeNm")["등록매물"].rank(pct=True)
    
    # 지역 평균 영업년수
    region_avg_years = df.groupby("ldCodeNm")["영업년수"].mean()
    df["지역_평균영업년수"] = df["ldCodeNm"].map(region_avg_years)
    
    # 지역 매물 밀도 (지역 내 총 매물 / 중개사 수)
    region_total_listings = df.groupby("ldCodeNm")["등록매물"].sum()
    df["지역_매물밀도"] = df["ldCodeNm"].map(region_total_listings) / (df["지역중개사수"] + 1e-6)
    
    print("   ✅ 지역 피처 4개 (지역중개사수, 지역내_등록매물_순위, 지역_평균영업년수, 지역_매물밀도)")

    # 파생 피처 (3개)
    df["매물_규모_지수"] = np.log1p(df["등록매물"])
    df["지역_경쟁_강도"] = df["등록매물"] / (df["지역중개사수"] + 1e-6)
    
    # Feature 상호작용: 영업년수 × 매물 규모
    df["영업년수_매물_상호작용"] = df["영업년수"] * df["매물_규모_지수"]
    
    print("   ✅ 파생 피처 3개 (매물_규모_지수, 지역_경쟁_강도, 영업년수_매물_상호작용)")

    print(f"\n   📊 총 15개 피처 준비 완료 (10개 → 15개)")
    print(f"   ✅ 거래완료 정보 제외 (Target과 독립적)")

    return df

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/seoul_broker_clean.csv")
    df = add_features(df)
