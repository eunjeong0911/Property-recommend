import pandas as pd
from pathlib import Path

def load_data(input_path=None):
    """
    원본 데이터셋 load 
    """
    print("\n📂 [1단계] 데이터 로드")
    
    # 경로 자동 탐색
    if input_path is None:
        # 현재 파일 기준으로 data 폴더 찾기
        current_file = Path(__file__)
        data_dir = current_file.parent.parent.parent.parent.parent.parent / "data"
        input_path = data_dir / "seoul_broker_clean.csv"
    else:
        input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"❌ 데이터 파일을 찾을 수 없습니다: {input_path}")
    
    df = pd.read_csv(input_path)
    print(f"   ✅ {df.shape[0]}개 중개사 데이터 로드 완료")
    print(f"   📁 경로: {input_path}")
    return df

if __name__ == "__main__":
    df = load_data()
