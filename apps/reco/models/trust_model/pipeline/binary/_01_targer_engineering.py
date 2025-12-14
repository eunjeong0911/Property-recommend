"""
[01] 타겟 엔지니어링 - 이진 분류 (Binary Classification)
- 2등급: 상위(1), 하위(0)
- 중위수(50%) 기준으로 분할
"""
import pandas as pd
import numpy as np

def success_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    베이지안 보정 성사율 계산 및 이진 등급 부여
    """
    print("\n[타겟 엔지니어링] 베이지안 보정 성사율(Target) 계산 중...")
    
    # 0. 전처리
    df["거래완료"] = df["거래완료"].fillna(0)
    df["총매물수"] = df["총매물수"].fillna(1)
    
    # 지역명 추출
    if "ldCodeNm" not in df.columns:
        if "주소" in df.columns:
            df["ldCodeNm"] = df["주소"].str.split().str[1]
        else:
            df["ldCodeNm"] = "Unknown"

    # [Step 1] 지역별 매물 분포율
    total_listings = df["총매물수"].sum()
    region_total_listings = df.groupby("ldCodeNm")["총매물수"].transform("sum")
    df["지역매물분포율"] = region_total_listings / total_listings

    # [Step 2] 지역별 거래성사율
    region_total_success = df.groupby("ldCodeNm")["거래완료"].transform("sum")
    df["지역평균성사율"] = region_total_success / region_total_listings
    df["지역평균성사율"] = df["지역평균성사율"].fillna(0)
    
    # [Step 3] 가중치 적용
    global_mean = df["거래완료"].sum() / df["총매물수"].sum()
    df["보정된_기준값"] = (
        (df["지역평균성사율"] * df["지역매물분포율"]) + 
        (global_mean * (1 - df["지역매물분포율"]))
    )
    
    # [Step 4] 베이지안 보정
    m = df["총매물수"].median()
    print(f"   - 베이지안 임계값 (m): {m:.1f}")
    
    df["베이지안_성사율"] = (
        (m * df["보정된_기준값"] + df["거래완료"]) / 
        (m + df["총매물수"])
    )
    
    # [Step 5] 이진 등급 부여 (중위수 기준 - 50/50)
    median = df["베이지안_성사율"].quantile(0.50)
    
    def assign_grade(score):
        if score >= median:
            return 1  # 상위 (High)
        else:
            return 0  # 하위 (Low)
    
    df["신뢰등급"] = df["베이지안_성사율"].apply(assign_grade)
    
    print(f"\n   - 등급 기준 (중위수): {median:.4f}")
    print(f"   - 상위(1): >= {median:.4f}")
    print(f"   - 하위(0): < {median:.4f}")
    print(f"   - 등급 분포: {df['신뢰등급'].value_counts().sort_index().to_dict()}")
    
    return df

def save_distribution_plot(df: pd.DataFrame):
    """베이지안 성사율 분포 저장"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import platform

        system_name = platform.system()
        if system_name == 'Windows':
            plt.rc('font', family='Malgun Gothic')
        elif system_name == 'Darwin': 
            plt.rc('font', family='AppleGothic')
        else: 
            plt.rc('font', family='NanumGothic')

        plt.rcParams['axes.unicode_minus'] = False
        
        plt.figure(figsize=(10, 6))
        plt.hist(df["베이지안_성사율"], bins=30, color='skyblue', edgecolor='black', alpha=0.7)
        plt.axvline(df["베이지안_성사율"].median(), color='red', linestyle='--', label='Median (분류 기준)')
        plt.title('베이지안 성사율(Target) 분포 - 이진 분류')
        plt.xlabel('점수')
        plt.ylabel('빈도')
        plt.legend()
        plt.grid(axis='y', alpha=0.5)
        
        save_path = "target_distribution_binary.png"
        plt.savefig(save_path)
        print(f"\n[시각화] 저장: {save_path}")
        plt.close()
    except Exception as e:
        print(f"[주의] 시각화 실패: {e}")

def main(df: pd.DataFrame):
    """메인 실행 함수"""
    df = success_rate(df)
    save_distribution_plot(df)
    
    print("\n=== [검증] 데이터 샘플 (상위 5개) ===")
    cols = ["ldCodeNm", "총매물수", "거래완료", "베이지안_성사율", "신뢰등급"]
    print(df[cols].head())
    
    return df

if __name__ == "__main__":
    from _00_load_data import load_processed_office_data
    
    print("=== 타겟 엔지니어링 (Binary) 실행 ===")
    raw_df = load_processed_office_data()
    df_result = main(raw_df)
