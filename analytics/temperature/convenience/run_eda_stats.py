
import os
import json
import glob
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

# 경로 설정
# 현재 파일 위치: analytics/temperature/convenience
# 프로젝트 루트: ../../../
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(current_dir, "../../../"))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "GraphDB_data")

def load_properties(limit=5000):
    """매물 샘플 데이터 로드 (좌표 포함)"""
    geo_file = os.path.join(DATA_DIR, "land", "00_통합_원투룸.json")
    if not os.path.exists(geo_file):
        print(f"매물 파일을 찾을 수 없습니다: {geo_file}")
        return pd.DataFrame()
        
    with open(geo_file, 'r', encoding='utf-8') as f:
        geo_data = json.load(f)
        
    df = pd.DataFrame(geo_data)
    # 좌표 정보 추출
    df['lat'] = df['좌표_정보'].apply(lambda x: x.get('위도') if x else None)
    df['lon'] = df['좌표_정보'].apply(lambda x: x.get('경도') if x else None)
    df = df.dropna(subset=['lat', 'lon'])
    
    if limit:
        df = df.sample(n=min(limit, len(df)), random_state=42)
    return df[['매물번호', 'lat', 'lon']]

def load_facilities():
    """편의시설 데이터 로드"""
    facilities = {}
    
    # 1. 대형마트 (Mart)
    mart_path = os.path.join(DATA_DIR, "store_data", "서울시 대규모점포 인허가 정보.csv")
    try:
        df = pd.read_csv(mart_path, encoding='cp949')
    except:
        try:
            df = pd.read_csv(mart_path, encoding='euc-kr')
        except:
            df = pd.read_csv(mart_path, encoding='utf-8')
            
    cats = ['대형마트', '백화점', '쇼핑센터', '복합쇼핑몰', '구분없음']
    df = df[df['업태구분명'].isin(cats)]
    df = df.dropna(subset=['위도', '경도'])
    facilities['mart'] = df[['위도', '경도']].rename(columns={'위도': 'lat', '경도': 'lon'})

    # 2. 소상공인 상가 정보 (Store)
    store_path = os.path.join(DATA_DIR, "store_data", "소상공인시장진흥공단_상가(상권)정보_서울_cleaned.csv")
    try:
        df_store = pd.read_csv(store_path, encoding='utf-8')
    except:
        df_store = pd.read_csv(store_path, encoding='cp949')
        
    # 세탁소
    laundry = df_store[df_store['상권업종소분류명'] == '세탁소'].dropna(subset=['위도', '경도'])
    facilities['laundry'] = laundry[['위도', '경도']].rename(columns={'위도': 'lat', '경도': 'lon'})
    
    # 편의점
    conv = df_store[df_store['상권업종소분류명'] == '편의점'].dropna(subset=['위도', '경도'])
    facilities['convenience'] = conv[['위도', '경도']].rename(columns={'위도': 'lat', '경도': 'lon'})
    
    # 3. 공원 (Park)
    park_files = glob.glob(os.path.join(DATA_DIR, "park", "*.csv"))
    park_dfs = []
    for f in park_files:
        try:
            d = pd.read_csv(f, encoding='cp949')
        except:
            d = pd.read_csv(f, encoding='utf-8')
        park_dfs.append(d)
    
    if park_dfs:
        df_park = pd.concat(park_dfs, ignore_index=True)
        df_park = df_park.dropna(subset=['위도', '경도'])
        facilities['park'] = df_park[['위도', '경도']].rename(columns={'위도': 'lat', '경도': 'lon'})
        
    return facilities

def get_nearest_distance(sources_df, targets_df):
    """최단 거리 계산 (미터 단위 근사치)"""
    if targets_df.empty: return np.full(len(sources_df), np.inf)
    
    # 서울 지역 평면 투영 근사치 (위도 37.5도 기준)
    def to_xy(df):
        x = df['lon'].values * 88000  # 경도 1도 ≈ 88km
        y = df['lat'].values * 111000 # 위도 1도 ≈ 111km
        return np.column_stack([x, y])
    
    source_xy = to_xy(sources_df)
    target_xy = to_xy(targets_df)
    
    tree = cKDTree(target_xy)
    dists, _ = tree.query(source_xy, k=1)
    return dists

def main():
    print("데이터 로딩 중...")
    props = load_properties(limit=5000)
    print(f"매물 샘플 로드됨: {len(props)}개")
    
    facs = load_facilities()
    for k, v in facs.items():
        print(f"시설 데이터 '{k}': {len(v)}개")
        
    print("\n[거리 분석 결과 및 점수 기준 제안]")
    metrics = {
        'convenience': '편의점',
        'laundry': '세탁소',
        'mart': '대형마트/백화점',
        'park': '공원'
    }
    
    for m, label in metrics.items():
        if m not in facs: continue
        dists = get_nearest_distance(props, facs[m])
        
        print(f"\n--- {label} ({m.upper()}) 거리 분포 (미터 단위) ---")
        p = np.percentile(dists, [10, 25, 50, 75, 90, 95])
        print(f"  하위 10% (매우 가까움): {p[0]:.1f}m 이내")
        print(f"  하위 25%: {p[1]:.1f}m 이내")
        print(f"  중위 50%: {p[2]:.1f}m (평균적)")
        print(f"  하위 75%: {p[3]:.1f}m")
        print(f"  하위 90% (먼 편): {p[4]:.1f}m")
        print(f"  하위 95%: {p[5]:.1f}m")
        
        # 간단한 제안 로직
        print(f"  💡 제안: {p[1]:.0f}m 이내 만점, {p[4]:.0f}m 이상 0점 고려")

if __name__ == "__main__":
    main()
