"""
[01] 타겟 엔지니어링 (타겟 변수 및 등급 생성)
이 모듈은 '베이지안 보정된 지역별 평균거래성사율'을 계산하고, 이를 바탕으로 타겟 등급을 생성합니다.
"""
import pandas as pd
import numpy as np

def success_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    [타겟 변수 생성 로직]
    1. 지역별 매물분포율 계산
    2. 지역별 거래성사율 계산
    3. 성사율에 분포율 가중치 적용 (Adjusted Prior)
    4. 베이지안 보정 (Final Rate)
    """
    print("\n[타겟 엔지니어링] 베이지안 보정 성사율(Target) 계산 중...")
    
    # 0. 전처리
    df["거래완료"] = df["거래완료"].fillna(0)
    df["총매물수"] = df["총매물수"].fillna(1)
    
    # 지역명(ldCodeNm) 추출
    if "ldCodeNm" not in df.columns:
        if "주소" in df.columns:
            df["ldCodeNm"] = df["주소"].str.split().str[1]
        else:
            df["ldCodeNm"] = "Unknown"

    # ---------------------------------------------------------
    # [Step 1] 지역별 매물 분포율 계산
    # ---------------------------------------------------------
    total_listings = df["총매물수"].sum()
    region_total_listings = df.groupby("ldCodeNm")["총매물수"].transform("sum")
    df["지역매물분포율"] = region_total_listings / total_listings

    # ---------------------------------------------------------
    # [Step 2] 지역별 매물 분포율 계산
    # ---------------------------------------------------------
    df["지역별_중개사수"] = df.groupby("ldCodeNm")["등록번호"].transform("count")
    
    # ---------------------------------------------------------
    # [Step 3] 지역별 거래성사율 계산
    # ---------------------------------------------------------
    region_total_success = df.groupby("ldCodeNm")["거래완료"].transform("sum")
    df["지역평균성사율"] = region_total_success / region_total_listings
    df["지역평균성사율"] = df["지역평균성사율"].fillna(0)
    
    # ---------------------------------------------------------
    # [Step 4] 성사율에 분포율 가중치 적용 (Adjusted Prior)
    # ---------------------------------------------------------
    global_mean = df["거래완료"].sum() / df["총매물수"].sum()
    
    # 보정된 기준값 = (지역평균 * 분포율) + (전체평균 * (1-분포율))
    df["보정된_기준값"] = (
        (df["지역평균성사율"] * df["지역매물분포율"]) + 
        (global_mean * (1 - df["지역매물분포율"]))
    )
    
    # ---------------------------------------------------------
    # [Step 5] 베이지안 보정 (최종 타겟 변수)
    # ---------------------------------------------------------
    # m: 임계값 (전체 중위 매물 수)
    m = df["총매물수"].median()
    print(f"   - 베이지안 임계값 (m): {m:.1f}")
    print(f"     (매물 수가 {m:.1f}개 미만인 경우, 지역/전체 평균값(Prior)의 영향을 더 많이 받습니다.)")
    
    # 베이지안 성사율 = (m*Prior + 거래완료) / (m + 총매물수)
    df["베이지안_성사율"] = (
        (m * df["보정된_기준값"] + df["거래완료"]) / 
        (m + df["총매물수"])
    )
    
    return df

def save_distribution_plot(df: pd.DataFrame):
    """
    베이지안 성사율 분포를 히스토그램으로 저장
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # 비GUI 백엔드 사용 (tkinter 스레드 에러 방지)
        import matplotlib.pyplot as plt
        import platform

        # 한글 폰트 설정
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
        plt.title('베이지안 성사율(Target) 분포')
        plt.xlabel('점수')
        plt.ylabel('빈도 (Frequency)')
        plt.grid(axis='y', alpha=0.5)
        
        save_path = "target_distribution.png"
        plt.savefig(save_path)
        print(f"\n[시각화] 타겟 분포 그래프가 저장되었습니다: {save_path}")
        plt.close()
    except Exception as e:
        print(f"[주의] 시각화 실패: {e}")

def main(df: pd.DataFrame):
    """
    메인 실행 함수
    """
    # 1. 타겟 변수(성사율) 계산
    df = success_rate(df)
    
    # 2. 분포 시각화 (파일 저장)
    save_distribution_plot(df)
    
    print("\n=== [검증] 데이터 샘플 (상위 5개) ===")
    cols = ["ldCodeNm", "총매물수", "거래완료", "보정된_기준값", "베이지안_성사율"]
    print(df[cols].head())
    
    return df

if __name__ == "__main__":
    from _00_load_data import load_processed_office_data
    
    print("=== 타겟 엔지니어링 모듈 실행 ===")
    
    # 1. 데이터 로드
    raw_df = load_processed_office_data()
    
    # 2. 메인 로직 실행
    df_result = main(raw_df)
