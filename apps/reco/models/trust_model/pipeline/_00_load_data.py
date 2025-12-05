import pandas as pd
import os

def load_data(input_path=None):
    """
    원본 데이터셋 load 
    """
    print("\n📂 [1단계] 데이터 로드")
    
    # 경로 자동 탐색
    if input_path is None:
        # 현재 파일 위치에서 프로젝트 루트 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", ".."))
        input_path = os.path.join(project_root, "data", "seoul_broker_clean.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"❌ 데이터 파일을 찾을 수 없습니다: {input_path}")
    
    df = pd.read_csv(input_path)
    print(f"   ✅ {df.shape[0]}개 중개사 데이터 로드 완료")
    print(f"   📁 경로: {input_path}")
    return df

if __name__ == "__main__":
    df = load_data()
