import pandas as pd
import json
from pathlib import Path
from collections import Counter

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).resolve().parents[5]
DATA_PATH = PROJECT_ROOT / 'data' / 'processed_office_data.csv'
LAND_DATA_PATH = PROJECT_ROOT / 'data' / 'landData'

# JSON 파일 목록
JSON_FILES = [
    '00_통합_아파트.json',
    '00_통합_빌라주택.json',
    '00_통합_오피스텔.json',
    '00_통합_원투룸.json'
]

def load_broker_data():
    """processed_office_data.csv 파일 로드"""
    print(f"Loading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows")
    return df

def count_listings_from_json():
    """JSON 파일들에서 등록번호+중개사명별 등록매물 수 카운트"""
    broker_counter = Counter()
    
    for json_file in JSON_FILES:
        json_path = LAND_DATA_PATH / json_file
        print(f"Processing: {json_path}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 각 매물에서 등록번호 + 중개사명 추출
            for item in data:
                broker_info = item.get('중개사_정보', {})
                if broker_info and isinstance(broker_info, dict):
                    broker_name = broker_info.get('중개사명')
                    registration_no = broker_info.get('등록번호')
                    
                    # 등록번호와 중개사명이 모두 있는 경우만 카운트
                    if broker_name and registration_no:
                        # 등록번호 + 중개사명을 키로 사용
                        key = f"{registration_no}_{broker_name}"
                        broker_counter[key] += 1
            
            print(f"  - Found {len([item for item in data if item.get('중개사_정보', {}).get('중개사명') and item.get('중개사_정보', {}).get('등록번호')])} listings with broker info")
        
        except Exception as e:
            print(f"  - Error processing {json_file}: {e}")
    
    print(f"\nTotal unique brokers (등록번호+중개사명) found: {len(broker_counter)}")
    print(f"Total listings counted: {sum(broker_counter.values())}")
    
    return broker_counter

def fill_na_values(df, broker_counter):
    """거래완료와 등록매물의 NA 값 채우기"""
    # 거래완료와 등록매물이 모두 NA인 행 찾기
    both_na_mask = df['거래완료'].isna() & df['등록매물'].isna()
    print(f"\nRows with both 거래완료 and 등록매물 as NA: {both_na_mask.sum()}")
    
    # 거래완료는 0으로 채우기
    df.loc[both_na_mask, '거래완료'] = '0건'
    
    # 등록매물은 JSON에서 카운트한 값으로 채우기 (등록번호 + 중개사명으로 매칭)
    filled_count = 0
    for idx in df[both_na_mask].index:
        registration_no = df.loc[idx, '등록번호']
        broker_name = df.loc[idx, '중개사명']
        
        # 등록번호 + 중개사명으로 키 생성
        key = f"{registration_no}_{broker_name}"
        
        if key in broker_counter:
            count = broker_counter[key]
            df.loc[idx, '등록매물'] = f'{count}건'
            filled_count += 1
        else:
            # JSON에 없는 경우 0건으로 설정
            df.loc[idx, '등록매물'] = '0건'
    
    print(f"Filled 등록매물 from JSON count: {filled_count}")
    print(f"Filled 등록매물 with 0건 (not found in JSON): {both_na_mask.sum() - filled_count}")
    
    return df

def save_data(df):
    """처리된 데이터 저장"""
    output_path = DATA_PATH
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\nSaved processed data to: {output_path}")

def main():
    print("=" * 60)
    print("Starting NA filling process")
    print("=" * 60)
    
    # 1. 데이터 로드
    df = load_broker_data()
    
    # 2. JSON 파일에서 중개사별 등록매물 수 카운트
    broker_counter = count_listings_from_json()
    
    # 3. NA 값 채우기
    df = fill_na_values(df, broker_counter)
    
    # 4. 결과 저장
    save_data(df)
    
    print("\n" + "=" * 60)
    print("Process completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
