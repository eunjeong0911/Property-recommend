
import os
import glob
import pandas as pd
import numpy as np

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(current_dir, "../../../"))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "GraphDB_data")

def load_park_areas():
    park_files = glob.glob(os.path.join(DATA_DIR, "park", "*.csv"))
    park_dfs = []
    for f in park_files:
        try:
            d = pd.read_csv(f, encoding='cp949')
        except:
            d = pd.read_csv(f, encoding='utf-8')
        park_dfs.append(d)
    
    if park_dfs:
        df = pd.concat(park_dfs, ignore_index=True)
        # Assuming '공원면적' column exists based on previous amenity_importer viewing
        # Clean up column: remove commas, convert to float
        if '공원면적' in df.columns:
            # Handle string formatted numbers if any
            df['area'] = pd.to_numeric(df['공원면적'].astype(str).str.replace(',', ''), errors='coerce')
            return df['area'].dropna()
    return pd.Series(dtype=float)

def main():
    print("공원 면적 데이터 분석 중...")
    areas = load_park_areas()
    
    if areas.empty:
        print("공원 데이터가 없거나 면적 정보를 읽을 수 없습니다.")
        return

    print(f"총 공원 수: {len(areas)}개")
    print(f"\n--- 공원 면적 통계 (㎡ 단위) ---")
    
    desc = areas.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9, 0.95])
    print(desc)
    
    print("\n--- 주요 기준별 제외 비율 시뮬레이션 ---")
    thresholds = [100, 300, 500, 1000, 1500, 2000, 3000, 5000, 10000]
    for t in thresholds:
        count = (areas >= t).sum()
        ratio = count / len(areas) * 100
        print(f"{t}㎡ 이상: {count}개 ({ratio:.1f}%) - 제외되는 공원: {len(areas)-count}개")

    print("\n💡 참고: 서울 여의도 공원 ≈ 230,000㎡, 일반적인 소공원/어린이공원 ≈ 1,500㎡ ~ 3,000㎡ 미만")
    print("   도시공원법상 어린이공원 최소 기준: 1,500㎡")
    print("   소공원 최소 기준: 165㎡ (너무 작음)")

if __name__ == "__main__":
    main()
