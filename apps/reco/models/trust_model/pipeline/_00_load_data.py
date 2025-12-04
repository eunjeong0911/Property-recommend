import pandas as pd

def load_data(input_path="data/seoul_broker_clean.csv"):
    """
    원본 데이터셋 load 
    """
    print("\n📂 [1단계] 데이터 로드")
    df = pd.read_csv(input_path)
    print(f"   ✅ {df.shape[0]}개 중개사 데이터 로드 완료")
    return df

if __name__ == "__main__":
    df = load_data()
