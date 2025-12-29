
import os
import json
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(current_dir, "../../../"))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "GraphDB_data")

def load_properties(limit=5000):
    geo_file = os.path.join(DATA_DIR, "land", "00_통합_원투룸.json")
    if not os.path.exists(geo_file):
        print("매물 파일을 찾을 수 없습니다.")
        return pd.DataFrame()
        
    with open(geo_file, 'r', encoding='utf-8') as f:
        geo_data = json.load(f)
        
    df = pd.DataFrame(geo_data)
    df['lat'] = df['좌표_정보'].apply(lambda x: x.get('위도') if x else None)
    df['lon'] = df['좌표_정보'].apply(lambda x: x.get('경도') if x else None)
    df = df.dropna(subset=['lat', 'lon'])
    
    if limit:
        df = df.sample(n=min(limit, len(df)), random_state=42)
    return df[['매물번호', 'lat', 'lon']]

def load_transport():
    transport = {}
    
    # Subway
    subway_path = os.path.join(DATA_DIR, "subway_station", "지하철_노선도.csv")
    try:
        df = pd.read_csv(subway_path, encoding='utf-8', on_bad_lines='skip')
    except:
        df = pd.read_csv(subway_path, encoding='cp949', on_bad_lines='skip')
    
    df = df.dropna(subset=['역위도', '역경도'])
    transport['subway'] = df[['역위도', '역경도']].rename(columns={'역위도': 'lat', '역경도': 'lon'})
    
    # Bus
    bus_path = os.path.join(DATA_DIR, "bus_station", "bus_data_fixed.csv")
    try:
        df_bus = pd.read_csv(bus_path, encoding='utf-8')
    except:
        df_bus = pd.read_csv(bus_path, encoding='cp949')
        
    df_bus = df_bus[df_bus['도시명'].str.contains("서울특별시", na=False)]
    df_bus = df_bus.dropna(subset=['위도', '경도'])
    transport['bus'] = df_bus[['위도', '경도']].rename(columns={'위도': 'lat', '경도': 'lon'})
    
    return transport

def get_nearest_distance(sources_df, targets_df):
    if targets_df.empty: return np.full(len(sources_df), np.inf)
    
    def to_xy(df):
        x = df['lon'].values * 88000
        y = df['lat'].values * 111000
        return np.column_stack([x, y])
    
    source_xy = to_xy(sources_df)
    target_xy = to_xy(targets_df)
    tree = cKDTree(target_xy)
    dists, _ = tree.query(source_xy, k=1)
    return dists

def count_within_radius(sources_df, targets_df, radius_m):
    """지정 반경 내 개수 계산"""
    if targets_df.empty: return np.zeros(len(sources_df))
    
    def to_xy(df):
        x = df['lon'].values * 88000
        y = df['lat'].values * 111000
        return np.column_stack([x, y])
        
    source_xy = to_xy(sources_df)
    target_xy = to_xy(targets_df)
    tree = cKDTree(target_xy)
    
    return np.array([len(l) for l in tree.query_ball_point(source_xy, r=radius_m)])

def main():
    print("교통 데이터 분석 중...")
    props = load_properties(limit=5000)
    trans = load_transport()
    
    print(f"매물: {len(props)}개, 지하철역: {len(trans['subway'])}개, 버스정류장: {len(trans['bus'])}개")
    
    # 1. 지하철: 최단 거리 분석
    dists_subway = get_nearest_distance(props, trans['subway'])
    print("\n[지하철 역세권 분석 (거리)]")
    p_sub = np.percentile(dists_subway, [10, 25, 50, 75, 90, 95])
    print(f"  하위 10% (초역세권): {p_sub[0]:.1f}m 이내")
    print(f"  하위 25%: {p_sub[1]:.1f}m 이내")
    print(f"  중위 50%: {p_sub[2]:.1f}m")
    print(f"  하위 75%: {p_sub[3]:.1f}m")
    print(f"  하위 90% (비역세권): {p_sub[4]:.1f}m")
    
    # 2. 버스: 300m 반경 내 정류장 개수 분포
    counts_bus_300 = count_within_radius(props, trans['bus'], 300)
    print("\n[버스 정류장 접근성 (300m 내 개수)]")
    p_bus = np.percentile(counts_bus_300, [10, 25, 50, 75, 90])
    print(f"  상위 10%: {p_bus[4]:.1f}개 이상 (매우 많음)")
    print(f"  상위 25%: {p_bus[3]:.1f}개 이상")
    print(f"  중위 50%: {p_bus[2]:.1f}개 (평균)")
    print(f"  하위 25%: {p_bus[1]:.1f}개 이하")
    print(f"  하위 10%: {p_bus[0]:.1f}개 이하 (거의 없음)")
    
    # 3. 버스: 500m 반경 내 정류장 개수 분포
    counts_bus_500 = count_within_radius(props, trans['bus'], 500)
    print("\n[버스 정류장 접근성 (500m 내 개수)]")
    p_bus5 = np.percentile(counts_bus_500, [10, 25, 50, 75, 90])
    print(f"  중위 50%: {p_bus5[2]:.1f}개")

if __name__ == "__main__":
    main()
