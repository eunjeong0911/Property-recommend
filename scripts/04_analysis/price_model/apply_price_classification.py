"""
월세 매물 가격 분류 적용 스크립트 (Docker 환경용)
저장된 모델을 사용하여 매물 데이터에 가격 분류를 적용하고 DB에 저장

Usage:
    docker compose --profile scripts run --rm scripts
"""
import argparse
import pickle
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ========================================
# 환경별 경로 설정
# ========================================

# Docker 환경 감지
IS_DOCKER = os.path.exists("/app") or os.path.exists("/data")

if IS_DOCKER:
    # Docker 환경 (scripts 컨테이너)
    # apps/reco가 /app/apps/reco에 마운트됨
    SCRIPT_DIR = Path("/app/04_analysis/price_model")
    MODEL_DIR = Path("/app/04_analysis/price_model")
    DATA_DIR = Path("/data")
    JSON_DATA_DIR = DATA_DIR / "RDB" / "land"
    INTEREST_RATE_PATH = DATA_DIR / "actual_transaction_price" / "(총합)시장금리_및_대출금리(24.8~25.10).csv"
else:
    # 로컬 환경
    SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SCRIPT_DIR.parents[2]  # SKN18-FINAL-1TEAM
    MODEL_DIR = PROJECT_ROOT / "apps" / "reco" / "price_model" / "model"
    DATA_DIR = PROJECT_ROOT / "data"
    JSON_DATA_DIR = DATA_DIR / "RDB" / "land"
    INTEREST_RATE_PATH = DATA_DIR / "actual_transaction_price" / "(총합)시장금리_및_대출금리(24.8~25.10).csv"

    # ML 소스 경로 추가
    ML_SRC_PATH = PROJECT_ROOT / "apps" / "reco" / "price_model" / "src"
    if str(ML_SRC_PATH) not in sys.path:
        sys.path.insert(0, str(ML_SRC_PATH))

DEFAULT_MODEL_PATH = MODEL_DIR / "price_model_lightgbm.pkl"

# 클래스 레이블
CLASS_LABELS = {
    0: {"label": "UNDERPRICED", "label_kr": "저렴"},
    1: {"label": "FAIR", "label_kr": "적정"},
    2: {"label": "OVERPRICED", "label_kr": "비쌈"}
}

# 데이터베이스 설정
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "realestate"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

RESULTS_TABLE = "price_classification_results"


# ========================================
# JSON 데이터 파서
# ========================================
class JSONDataParser:
    """JSON 매물 데이터 파서"""
    
    def load_and_parse(self, json_dir: str) -> pd.DataFrame:
        """JSON 파일들을 로드하고 DataFrame으로 변환"""
        import json
        
        json_path = Path(json_dir)
        all_data = []
        
        for json_file in json_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
            except Exception as e:
                print(f"⚠ {json_file.name} 로드 실패: {e}")
        
        if not all_data:
            print("⚠ JSON 파일을 찾을 수 없습니다.")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        print(f"✅ {len(df)}개 매물 로드 완료")
        
        return df


# ========================================
# 데이터베이스 관리자
# ========================================
class DatabaseManager:
    """PostgreSQL 데이터베이스 관리"""
    
    def __init__(self, db_config: dict = None):
        self.db_config = db_config or DB_CONFIG
        self.conn = None
        self.cursor = None
    
    def connect(self):
        import psycopg2
        self.conn = psycopg2.connect(**self.db_config)
        self.cursor = self.conn.cursor()
        print(f"✅ DB 연결 성공: {self.db_config['database']}")
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✅ DB 연결 종료")
    
    def create_table(self):
        """결과 저장 테이블 생성"""
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {RESULTS_TABLE} (
            id SERIAL PRIMARY KEY,
            매물번호 VARCHAR(50),
            매물_URL TEXT,
            전체주소 TEXT,
            자치구명 VARCHAR(50),
            법정동명 VARCHAR(100),
            건물용도 VARCHAR(50),
            보증금_만원 DECIMAL(12, 2),
            월세_만원 DECIMAL(12, 2),
            임대면적 DECIMAL(10, 2),
            층 INTEGER,
            건축년도 INTEGER,
            예측_클래스 INTEGER,
            예측_레이블 VARCHAR(20),
            예측_레이블_한글 VARCHAR(20),
            저렴_확률 DECIMAL(5, 4),
            적정_확률 DECIMAL(5, 4),
            비쌈_확률 DECIMAL(5, 4),
            예측_일시 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(매물번호)
        );
        """
        self.cursor.execute(create_sql)
        self.conn.commit()
        print(f"✅ 테이블 생성/확인 완료: {RESULTS_TABLE}")
    
    def save_results(self, df: pd.DataFrame):
        """분류 결과 저장 (UPSERT)"""
        from psycopg2.extras import execute_batch
        
        if df.empty:
            print("⚠ 저장할 데이터가 없습니다.")
            return
        
        insert_sql = f"""
        INSERT INTO {RESULTS_TABLE} (
            매물번호, 매물_URL, 전체주소, 자치구명, 법정동명, 건물용도,
            보증금_만원, 월세_만원, 임대면적, 층, 건축년도,
            예측_클래스, 예측_레이블, 예측_레이블_한글,
            저렴_확률, 적정_확률, 비쌈_확률
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (매물번호) DO UPDATE SET
            예측_클래스 = EXCLUDED.예측_클래스,
            예측_레이블 = EXCLUDED.예측_레이블,
            예측_레이블_한글 = EXCLUDED.예측_레이블_한글,
            저렴_확률 = EXCLUDED.저렴_확률,
            적정_확률 = EXCLUDED.적정_확률,
            비쌈_확률 = EXCLUDED.비쌈_확률,
            예측_일시 = CURRENT_TIMESTAMP;
        """
        
        records = []
        for _, row in df.iterrows():
            try:
                record = (
                    str(row.get("매물번호", "")),
                    str(row.get("매물_URL", "")),
                    str(row.get("전체주소", "")),
                    str(row.get("자치구명", "")),
                    str(row.get("법정동명", "")),
                    str(row.get("건물용도", "")),
                    float(row.get("보증금(만원)", 0) or 0),
                    float(row.get("임대료(만원)", 0) or 0),
                    float(row.get("임대면적", 0) or 0),
                    int(row.get("층", 0) or 0),
                    int(row.get("건축년도", 2000) or 2000),
                    int(row["예측_클래스"]),
                    row["예측_레이블"],
                    row["예측_레이블_한글"],
                    float(row["저렴_확률"]),
                    float(row["적정_확률"]),
                    float(row["비쌈_확률"]),
                )
                records.append(record)
            except Exception as e:
                print(f"⚠ 레코드 변환 실패: {e}")
                continue
        
        if records:
            execute_batch(self.cursor, insert_sql, records, page_size=100)
            self.conn.commit()
            print(f"✅ {len(records)}개 레코드 저장 완료")


# ========================================
# 가격 분류 파이프라인
# ========================================
class PriceClassifier:
    """가격 분류 파이프라인"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model = None
        self.preprocessor = None
    
    def load_model(self):
        """저장된 모델 로드"""
        print(f"\n🚚 모델 로딩: {self.model_path}")
        
        with open(self.model_path, 'rb') as f:
            saved_data = pickle.load(f)
        
        if 'model' in saved_data:
            self.model = saved_data['model']
        elif 'best_model' in saved_data:
            self.model = saved_data['best_model']
        else:
            raise KeyError("저장된 파일에 'model' 키가 없습니다.")
        
        print(f"✅ 모델 로드 완료: {saved_data.get('model_name', 'Unknown')}")
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 전처리"""
        print("\n[Step] 데이터 전처리 시작")
        
        # 기본 전처리
        df = df.copy()
        
        # 필수 컬럼 확인 및 기본값 설정
        required_cols = ["자치구명", "법정동명", "층", "임대면적", "보증금(만원)", "임대료(만원)", "건축년도", "건물용도"]
        for col in required_cols:
            if col not in df.columns:
                print(f"⚠ 필수 컬럼 누락: {col}")
                df[col] = 0 if col in ["층", "임대면적", "보증금(만원)", "임대료(만원)", "건축년도"] else "Unknown"
        
        # 숫자형 변환
        for col in ["층", "임대면적", "보증금(만원)", "임대료(만원)", "건축년도"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # 기준금리 설정 (최신값)
        df["기준금리"] = 2.5
        df["적용이자율"] = (df["기준금리"] + 2.0) / 100.0
        
        # 환산보증금 계산
        df["환산보증금(만원)"] = df["보증금(만원)"] + (df["임대료(만원)"] * 12) / df["적용이자율"]
        df["전용평수"] = df["임대면적"] / 3.3
        df["환산보증금_평당가"] = df["환산보증금(만원)"] / df["전용평수"].replace(0, np.nan)
        
        # 현재 날짜 기준 연월 생성
        now = datetime.now()
        df["연월"] = f"{now.year}-{now.month:02d}"
        df["계약연도"] = now.year
        df["계약월"] = now.month
        df["건축연차"] = df["계약연도"] - df["건축년도"]
        
        print(f"✅ 전처리 완료: {len(df)}건")
        
        return df
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """모델 예측 수행"""
        print("\n🔮 예측 수행 중...")
        
        if df.empty:
            return df
        
        # 간단한 피처 생성 (모델에서 사용하는 피처와 맞춤)
        feature_cols = ["임대면적", "층", "건축년도", "보증금(만원)", "임대료(만원)", "환산보증금_평당가", "건축연차"]
        available_cols = [c for c in feature_cols if c in df.columns]
        
        X = df[available_cols].fillna(0).values
        
        # 모델의 n_features와 맞춤
        n_model_features = getattr(self.model, "n_features_in_", X.shape[1])
        
        if X.shape[1] < n_model_features:
            pad = np.zeros((X.shape[0], n_model_features - X.shape[1]))
            X = np.hstack([X, pad])
        elif X.shape[1] > n_model_features:
            X = X[:, :n_model_features]
        
        # 예측
        try:
            y_pred_proba = self.model.predict_proba(X)
            y_pred = np.argmax(y_pred_proba, axis=1)
            
            # 불확실한 예측은 "적정"으로
            max_proba = np.max(y_pred_proba, axis=1)
            uncertain = max_proba < 0.6
            y_pred[uncertain] = 1
            
            df['예측_클래스'] = y_pred
            df['예측_레이블'] = [CLASS_LABELS[c]['label'] for c in y_pred]
            df['예측_레이블_한글'] = [CLASS_LABELS[c]['label_kr'] for c in y_pred]
            df['저렴_확률'] = y_pred_proba[:, 0]
            df['적정_확률'] = y_pred_proba[:, 1]
            df['비쌈_확률'] = y_pred_proba[:, 2]
            
            print(f"✅ 예측 완료: {len(df)}개 매물")
            
            # 예측 결과 요약
            class_counts = df['예측_레이블_한글'].value_counts()
            print("\n📊 예측 결과 요약:")
            for label, count in class_counts.items():
                print(f"   - {label}: {count}개 ({count/len(df)*100:.1f}%)")
                
        except Exception as e:
            print(f"❌ 예측 오류: {e}")
            # 기본값 설정
            df['예측_클래스'] = 1
            df['예측_레이블'] = "FAIR"
            df['예측_레이블_한글'] = "적정"
            df['저렴_확률'] = 0.33
            df['적정_확률'] = 0.34
            df['비쌈_확률'] = 0.33
        
        return df
    
    def run(self, json_dir: str, save_to_db: bool = True) -> pd.DataFrame:
        """전체 파이프라인 실행"""
        print("\n" + "=" * 60)
        print("🚀 월세 매물 가격 분류 시작")
        print("=" * 60)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 모델 로드
        self.load_model()
        
        # 2. JSON 데이터 로드
        parser = JSONDataParser()
        df = parser.load_and_parse(json_dir)
        
        if df.empty:
            print("⚠ 처리할 데이터가 없습니다.")
            return df
        
        # 3. 데이터 전처리
        df_processed = self.prepare_data(df)
        
        # 4. 예측
        df_result = self.predict(df_processed)
        
        # 5. DB 저장
        if save_to_db:
            print("\n💾 데이터베이스 저장 중...")
            db = DatabaseManager()
            try:
                db.connect()
                db.create_table()
                db.save_results(df_result)
            except Exception as e:
                print(f"❌ DB 저장 중 오류: {e}")
            finally:
                db.close()
        
        print("\n" + "=" * 60)
        print("✅ 모든 작업 완료!")
        print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")
        
        return df_result


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="월세 매물 가격 분류 (저렴/적정/비쌈)"
    )
    parser.add_argument(
        "--json_dir",
        type=str,
        default=str(JSON_DATA_DIR),
        help="JSON 파일 디렉토리"
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default=str(DEFAULT_MODEL_PATH),
        help="저장된 모델 경로"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="DB 저장 없이 예측만 수행"
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default=None,
        help="결과를 CSV로 저장할 경로"
    )
    
    args = parser.parse_args()
    
    # 경로 확인 및 출력
    print("\n" + "=" * 60)
    print("📁 경로 설정")
    print("=" * 60)
    print(f"   - 환경: {'Docker' if IS_DOCKER else '로컬'}")
    print(f"   - JSON 디렉토리: {args.json_dir}")
    print(f"   - 모델 경로: {args.model_path}")
    print(f"   - DB 저장: {'No (dry-run)' if args.dry_run else 'Yes'}")
    
    # 분류기 실행
    classifier = PriceClassifier(args.model_path)
    results_df = classifier.run(
        json_dir=args.json_dir,
        save_to_db=not args.dry_run
    )
    
    # CSV 저장 (옵션)
    if args.output_csv and not results_df.empty:
        output_path = Path(args.output_csv)
        results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"📄 결과 CSV 저장: {output_path}")


if __name__ == "__main__":
    main()
