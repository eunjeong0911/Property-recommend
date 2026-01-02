"""
월세 매물 가격 분류 적용 스크립트 (Docker 환경용)
PostgreSQL land 테이블에서 월세 매물을 읽어 모델 적용 후 결과 테이블에 저장

Usage:
    python apply_price_classification.py
    python apply_price_classification.py --dry_run  # DB 저장 없이 테스트
"""
import argparse
import pickle
import os
import sys
import re
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ML 모듈 경로 추가
SCRIPT_DIR = Path(__file__).resolve().parent

# Docker 환경 감지
IS_DOCKER = os.path.exists("/app") or os.path.exists("/data")

if IS_DOCKER:
    # Docker 환경 (backend 컨테이너 또는 scripts 컨테이너)
    # backend 컨테이너: apps/reco가 /app/apps/reco에 마운트됨
    # scripts 컨테이너: apps/reco가 없을 수 있음
    DOCKER_ML_SRC = Path("/app/apps/reco/price_model/src")
    if DOCKER_ML_SRC.exists():
        ML_SRC = DOCKER_ML_SRC
    else:
        # fallback: 현재 스크립트 위치 기준
        ML_SRC = SCRIPT_DIR.parents[2] / "apps" / "reco" / "price_model" / "src"
else:
    # 로컬 환경
    PROJECT_ROOT = SCRIPT_DIR.parents[2]
    ML_SRC = PROJECT_ROOT / "apps" / "reco" / "price_model" / "src"

if str(ML_SRC) not in sys.path:
    sys.path.insert(0, str(ML_SRC))

try:
    from preprocessing.preprocessor import PriceDataPreprocessor
    from loaders.data_loader import DataLoader
    from core.config import (
        INTEREST_RATE_PATH,
        CLASS_LABELS,
        MODEL_PATH
    )
except ImportError:
    print("⚠ ML 모듈을 임포트할 수 없습니다. 경로를 확인하세요.")
    PriceDataPreprocessor = None
    DataLoader = None
    INTEREST_RATE_PATH = None
    CLASS_LABELS = {
        0: {"label": "UNDERPRICED", "label_kr": "저렴"},
        1: {"label": "FAIR", "label_kr": "적정"},
        2: {"label": "OVERPRICED", "label_kr": "비쌈"}
    }

# ========================================
# 환경별 경로 설정
# ========================================

if IS_DOCKER:
    # Docker 환경
    # 1. backend 컨테이너: /app/apps/reco/price_model/model
    # 2. scripts 컨테이너: /app/04_analysis/price_model (마운트된 폴더)
    DOCKER_MODEL_DIR = Path("/app/apps/reco/price_model/model")
    if DOCKER_MODEL_DIR.exists():
        MODEL_DIR = DOCKER_MODEL_DIR
    else:
        MODEL_DIR = SCRIPT_DIR
else:
    # 로컬 환경
    SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SCRIPT_DIR.parents[2]
    
    LOCAL_MODEL_DIR = SCRIPT_DIR
    ML_MODEL_DIR = PROJECT_ROOT / "apps" / "reco" / "price_model" / "model"
    
    if (LOCAL_MODEL_DIR / "price_model_lightgbm.pkl").exists():
        MODEL_DIR = LOCAL_MODEL_DIR
    else:
        MODEL_DIR = ML_MODEL_DIR

DEFAULT_MODEL_PATH = MODEL_DIR / "price_model_lightgbm.pkl"

# 클래스 레이블 (이미 임포트했으면 생략 가능하지만 안전을 위해 유지)
if not CLASS_LABELS:
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

# 테이블 설정
SOURCE_TABLE = "land"  # 매물 데이터 테이블
RESULTS_TABLE = "price_classification_results"  # 결과 저장 테이블


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
    
    def load_monthly_rent_from_land(self) -> pd.DataFrame:
        """land 테이블에서 월세 매물만 로드"""
        print(f"\n📊 {SOURCE_TABLE} 테이블에서 월세 매물 로드 중...")
        
        # 월세 매물만 조회 (area, floor 등은 listing_info JSONB에서 추출)
        query = f"""
        SELECT 
            land_id,
            land_num,
            url,
            address,
            building_type,
            deal_type,
            deposit,
            monthly_rent,
            listing_info,
            created_at
        FROM {SOURCE_TABLE}
        WHERE deal_type LIKE '%월세%'
           OR (monthly_rent IS NOT NULL AND monthly_rent > 0)
        """
        
        try:
            df = pd.read_sql(query, self.conn)
            print(f"✅ 월세 매물 {len(df)}건 로드 완료")
            return df
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def create_results_table(self):
        """결과 저장 테이블 생성 (기존 테이블 삭제 후 재생성)"""
        # 기존 테이블 삭제
        drop_sql = f"DROP TABLE IF EXISTS {RESULTS_TABLE} CASCADE;"
        self.cursor.execute(drop_sql)
        self.conn.commit()
        
        create_sql = f"""
        CREATE TABLE {RESULTS_TABLE} (
            id SERIAL PRIMARY KEY,
            land_id INTEGER,
            매물번호 VARCHAR(20),
            매물_url TEXT,
            address TEXT,
            자치구명 VARCHAR(50),
            법정동명 VARCHAR(100),
            건물용도 VARCHAR(50),
            보증금_만원 DECIMAL(12, 2),
            월세_만원 DECIMAL(12, 2),
            임대면적 DECIMAL(10, 2),
            층 INTEGER,
            건축년도 INTEGER,
            환산보증금_만원 DECIMAL(14, 2),
            환산보증금_평당가 DECIMAL(12, 2),
            예측_클래스 INTEGER,
            예측_레이블 VARCHAR(20),
            예측_레이블_한글 VARCHAR(20),
            저렴_확률 DECIMAL(5, 4),
            적정_확률 DECIMAL(5, 4),
            비쌈_확률 DECIMAL(5, 4),
            예측_일시 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(land_id)
        );
        
        -- 인덱스 생성
        CREATE INDEX IF NOT EXISTS idx_price_class_land_id ON {RESULTS_TABLE}(land_id);
        CREATE INDEX IF NOT EXISTS idx_price_class_num ON {RESULTS_TABLE}(매물번호);
        CREATE INDEX IF NOT EXISTS idx_price_class_label ON {RESULTS_TABLE}(예측_레이블_한글);
        CREATE INDEX IF NOT EXISTS idx_price_class_gu ON {RESULTS_TABLE}(자치구명);
        """
        
        try:
            self.cursor.execute(create_sql)
            self.conn.commit()
            print(f"✅ 테이블 생성 완료: {RESULTS_TABLE}")
        except Exception as e:
            print(f"❌ 테이블 생성 실패: {e}")
            self.conn.rollback()
            raise
    
    def save_results(self, df: pd.DataFrame):
        """분류 결과 저장 (UPSERT)"""
        from psycopg2.extras import execute_batch
        
        if df.empty:
            print("⚠ 저장할 데이터가 없습니다.")
            return
        
        insert_sql = f"""
        INSERT INTO {RESULTS_TABLE} (
            land_id, 매물_url, address, 자치구명, 법정동명, 건물용도,
            보증금_만원, 월세_만원, 임대면적, 층, 건축년도,
            환산보증금_만원, 환산보증금_평당가,
            예측_클래스, 예측_레이블, 예측_레이블_한글,
            저렴_확률, 적정_확률, 비쌈_확률, 매물번호
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (land_id) DO UPDATE SET
            예측_클래스 = EXCLUDED.예측_클래스,
            예측_레이블 = EXCLUDED.예측_레이블,
            예측_레이블_한글 = EXCLUDED.예측_레이블_한글,
            저렴_확률 = EXCLUDED.저렴_확률,
            적정_확률 = EXCLUDED.적정_확률,
            비쌈_확률 = EXCLUDED.비쌈_확률,
            환산보증금_만원 = EXCLUDED.환산보증금_만원,
            환산보증금_평당가 = EXCLUDED.환산보증금_평당가,
            매물번호 = EXCLUDED.매물번호,
            예측_일시 = CURRENT_TIMESTAMP;
        """
        
        records = []
        for _, row in df.iterrows():
            try:
                # PriceDataPreprocessor에서 생성한 컬럼명 사용
                record = (
                    int(row["land_id"]),
                    str(row.get("url", "")),
                    str(row.get("address", "")),
                    str(row.get("자치구명", "")),
                    str(row.get("법정동명", "")),
                    str(row.get("건물용도", "")),
                    float(row.get("보증금(만원)", 0) or 0),
                    float(row.get("임대료(만원)", 0) or 0),
                    float(row.get("임대면적", 0) or 0),
                    int(row.get("층", 0) or 0),
                    int(row.get("건축년도", 2000) or 2000),
                    float(row.get("환산보증금(만원)", 0) or 0),
                    float(row.get("환산보증금_평당가", 0) or 0),
                    int(row["예측_클래스"]),
                    row["예측_레이블"],
                    row["예측_레이블_한글"],
                    float(row["저렴_확률"]),
                    float(row["적정_확률"]),
                    float(row["비쌈_확률"]),
                    str(row.get("land_num", ""))
                )
                records.append(record)
            except Exception as e:
                print(f"⚠ 레코드 변환 실패 (land_id={row.get('land_id')}): {e}")
                continue
        
        if records:
            execute_batch(self.cursor, insert_sql, records, page_size=100)
            self.conn.commit()
            print(f"✅ {len(records)}개 레코드 저장 완료")


# ========================================
# 데이터 전처리기
# ========================================
class LandDataPreprocessor:
    """land 테이블 데이터 전처리"""
    
    # 서울시 자치구 리스트
    GU_LIST = [
        "강남구", "강동구", "강북구", "강서구", "관악구",
        "광진구", "구로구", "금천구", "노원구", "도봉구",
        "동대문구", "동작구", "마포구", "서대문구", "서초구",
        "성동구", "성북구", "송파구", "양천구", "영등포구",
        "용산구", "은평구", "종로구", "중구", "중랑구"
    ]
    
    def parse_address(self, address: str) -> dict:
        """주소에서 자치구명과 법정동명 추출"""
        if not address:
            return {"자치구명": "알수없음", "법정동명": "알수없음"}
        
        자치구명 = None
        법정동명 = None
        
        # 자치구 찾기
        for gu in self.GU_LIST:
            if gu in address:
                자치구명 = gu
                break
        
        # 법정동 찾기
        if 자치구명:
            parts = address.split(자치구명)
            if len(parts) > 1:
                after_gu = parts[1].strip()
                match = re.search(r'([^\s]+(?:동|로|가))', after_gu)
                if match:
                    법정동명 = match.group(1)
        
        return {
            "자치구명": 자치구명 or "알수없음",
            "법정동명": 법정동명 or "알수없음"
        }
    
    def parse_floor(self, floor_str) -> int:
        """층수 파싱"""
        if floor_str is None:
            return 5  # 기본값
        
        floor_str = str(floor_str)
        
        # 지하/반지하
        if "지하" in floor_str or "반지하" in floor_str or "B" in floor_str.upper():
            return -1
        
        # 문자형 층수
        floor_mapping = {"저층": 2, "중층": 5, "중고층": 8, "고층": 12}
        for key, value in floor_mapping.items():
            if key in floor_str:
                return value
        
        # 숫자 추출
        match = re.search(r'(\d+)', floor_str)
        if match:
            return int(match.group(1))
        
        return 5
    
    def parse_building_type(self, building_type: str) -> str:
        """건물용도 정규화"""
        if not building_type:
            return "연립다세대"
        
        building_type_lower = building_type.lower()
        
        if "아파트" in building_type_lower:
            return "아파트"
        if "오피스텔" in building_type_lower:
            return "오피스텔"
        
        return "연립다세대"
    
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """land 테이블 데이터 전처리"""
        print("\n[Step] 데이터 전처리 시작")
        
        result_df = df.copy()
        
        # land_id는 이미 있음
        # listing_info JSONB에서 면적, 층수, 건축년도 추출
        def extract_from_listing_info(row):
            info = row.get('listing_info')
            if isinstance(info, str):
                import json
                try:
                    info = json.loads(info)
                except:
                    info = {}
            elif not isinstance(info, dict):
                info = {}
            
            # 전용/공급면적에서 숫자 추출
            area_str = info.get('전용/공급면적', '')
            area = None
            if area_str:
                match = re.search(r'([\d.]+)', str(area_str))
                if match:
                    area = float(match.group(1))
            
            # 해당층/전체층에서 층수 추출
            floor_str = info.get('해당층/전체층', '')
            
            # 사용승인일에서 년도 추출
            year_str = info.get('사용승인일', '')
            year = None
            if year_str:
                match = re.search(r'(\d{4})', str(year_str))
                if match:
                    year = int(match.group(1))
            
            return pd.Series({'임대면적_raw': area, '층_raw': floor_str, '건축년도_raw': year})
        
        # listing_info 파싱
        extracted = result_df.apply(extract_from_listing_info, axis=1)
        result_df = pd.concat([result_df, extracted], axis=1)
        
        # 주소 파싱
        address_info = result_df["address"].apply(self.parse_address)
        result_df["자치구명"] = address_info.apply(lambda x: x["자치구명"])
        result_df["법정동명"] = address_info.apply(lambda x: x["법정동명"])
        
        # 가격 변환 확인 (DB에 만원 단위로 저장되어 있는지 확인)
        print("\n[DEBUG] DB에서 읽은 가격 샘플 (상위 5개):")
        print(result_df[["deposit", "monthly_rent"]].head())
        print(f"보증금 평균: {result_df['deposit'].mean():.2f}")
        print(f"월세 평균: {result_df['monthly_rent'].mean():.2f}")
        
        # 가격 변환 확인 (DB 값이 만원 단위인지 확인)
        avg_deposit = result_df["deposit"].mean()
        if avg_deposit > 100000:  # 원 단위로 저장됨
            print("→ DB 값이 원 단위로 저장되어 있음, 만원으로 변환")
            result_df["보증금(만원)"] = pd.to_numeric(result_df["deposit"], errors="coerce").fillna(0) / 10000
            result_df["임대료(만원)"] = pd.to_numeric(result_df["monthly_rent"], errors="coerce").fillna(0) / 10000
        else:  # 만원 단위로 저장됨
            print("→ DB 값이 만원 단위로 저장되어 있음")
            result_df["보증금(만원)"] = pd.to_numeric(result_df["deposit"], errors="coerce").fillna(0)
            result_df["임대료(만원)"] = pd.to_numeric(result_df["monthly_rent"], errors="coerce").fillna(0)
        
        # 면적 (listing_info에서 추출된 값 사용)
        result_df["임대면적"] = pd.to_numeric(result_df["임대면적_raw"], errors="coerce").fillna(0)
        
        # 층수 (listing_info에서 추출된 값 사용)
        result_df["층"] = result_df["층_raw"].apply(self.parse_floor)
        
        # 건축년도 (listing_info에서 추출된 값 사용)
        result_df["건축년도"] = pd.to_numeric(result_df["건축년도_raw"], errors="coerce").fillna(2010).astype(int)
        
        # 건물용도
        result_df["건물용도"] = result_df["building_type"].apply(self.parse_building_type)
        
        # 기준금리 (최신 데이터가 없으면 기본값 2.5 사용)
        result_df["기준금리"] = 2.5
        
        # 연월 생성
        now = datetime.now()
        result_df["연월"] = f"{now.year}-{now.month:02d}"
        result_df["계약연도"] = now.year
        result_df["계약월"] = now.month
        result_df["건축연차"] = result_df["계약연도"] - result_df["건축년도"]
        
        # 유효한 데이터만 필터링
        valid_mask = (
            (result_df["임대면적"] > 0) &
            (result_df["임대료(만원)"] > 0)
        )
        result_df = result_df[valid_mask].copy()
        
        print(f"✅ 전처리 완료: {len(result_df)}건 (유효 데이터)")
        
        return result_df


# ========================================
# 가격 분류 파이프라인
# ========================================
class PriceClassifier:
    """가격 분류 파이프라인"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model = None
        self.preprocessor = None
        self.interest_rate_df = None
    
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
            
        # 전처리기 생성
        self.preprocessor = PriceDataPreprocessor()
        
        # LabelEncoder 및 통계 복원
        if 'label_encoders' in saved_data:
            self.preprocessor.label_encoders = saved_data['label_encoders']
        if 'train_gu_quantiles' in saved_data:
            self.preprocessor.train_gu_quantiles = saved_data['train_gu_quantiles']
        
        print(f"✅ 모델 로드 완료: {saved_data.get('model_name', 'Unknown')}")

    def load_interest_rate(self):
        """금리 데이터 로드"""
        if not INTEREST_RATE_PATH or not INTEREST_RATE_PATH.exists():
            print(f"⚠ 금리 데이터 파일을 찾을 수 없습니다: {INTEREST_RATE_PATH}")
            return {"기준금리": 2.5}, "2025.10"
            
        print(f"\n📊 금리 데이터 로딩: {INTEREST_RATE_PATH}")
        self.interest_rate_df = pd.read_csv(INTEREST_RATE_PATH, encoding='utf-8-sig')
        
        columns = [col for col in self.interest_rate_df.columns if col != '구분']
        latest_month = columns[-1]
        print(f"✅ 최신 금리 데이터: {latest_month}")
        
        rate_dict = {}
        for _, row in self.interest_rate_df.iterrows():
            rate_name = row['구분']
            rate_value = row[latest_month]
            if pd.notna(rate_value):
                rate_dict[rate_name] = float(rate_value)
        
        return rate_dict, latest_month

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 전처리 (apply_model_to_json.py와 동일 로직)"""
        print("\n[Step] 데이터 전처리 시작")
        
        # 0. 학습 데이터 로드하여 분위수 재설정 (JSON 스크립트와 동일하게)
        if DataLoader and INTEREST_RATE_PATH:
            loader = DataLoader(base_dir=str(INTEREST_RATE_PATH.parent))
            train_df_raw, _ = loader.load_train_test()
            train_df_raw = self.preprocessor.create_target(train_df_raw)
        
        # 1. 금리 데이터 로드 및 적용
        if INTEREST_RATE_PATH and INTEREST_RATE_PATH.exists():
            macro = pd.read_csv(INTEREST_RATE_PATH, encoding="utf-8-sig")
            
            # wide -> long -> pivot
            macro_long = macro.melt(id_vars="구분", var_name="연월", value_name="값")
            macro_pivot = macro_long.pivot(index="연월", columns="구분", values="값").reset_index()
            
            # 최신 월 가져오기
            latest_month = macro_pivot["연월"].max()
            df["연월"] = latest_month
            
            # 조인
            df = df.merge(macro_pivot, on="연월", how="left")
            
            # 기준금리 및 적용이자율 설정
            rate_dict, _ = self.load_interest_rate()
            base_rate = rate_dict.get("기준금리", 2.5)
            df["기준금리"] = base_rate
            df["적용이자율"] = (df["기준금리"] + 2.0) / 100.0
        else:
            print("⚠ 금리 데이터가 없어 기본값을 사용합니다.")
            df["기준금리"] = 2.5
            df["적용이자율"] = (df["기준금리"] + 2.0) / 100.0
        
        # 2. 타깃 및 가격 컬럼 생성
        df = self.preprocessor.create_target(
            df,
            train_stats={"gu_quantiles": self.preprocessor.train_gu_quantiles}
        )
        
        # 3. 고급 피처 엔지니어링
        if DataLoader and INTEREST_RATE_PATH:
            _, df_fe = self.preprocessor.advanced_feature_engineering(train_df_raw, df)
        else:
            _, df_fe = self.preprocessor.advanced_feature_engineering(df.iloc[:0], df)
            
        return df_fe

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """모델 예측 수행 (apply_model_to_json.py와 동일 로직)"""
        print("\n🔮 예측 수행 중...")
        
        if df.empty:
            return df
        
        # 1) 피처 선택
        X = df[self.preprocessor.candidate_features].copy()
        
        # 2) Tree용 전처리 (Label Encoding)
        empty_df = pd.DataFrame(columns=X.columns)
        _, _, X_transformed = self.preprocessor.prepare_tree_features(
            empty_df, empty_df, X
        )
        
        # 3) 모델이 기대하는 피처 수에 맞춰 정렬
        X_arr = X_transformed.values
        n_model_features = getattr(self.model, "n_features_in_", X_arr.shape[1])
        
        if X_arr.shape[1] != n_model_features:
            diff = n_model_features - X_arr.shape[1]
            if diff > 0:
                pad = np.zeros((X_arr.shape[0], diff))
                X_arr = np.hstack([X_arr, pad])
            else:
                X_arr = X_arr[:, :n_model_features]
        
        # 4) 예측
        y_pred_proba = self.model.predict_proba(X_arr)
        y_pred = np.argmax(y_pred_proba, axis=1)
        
        # 애매한 확률은 적정(1)으로
        max_proba = np.max(y_pred_proba, axis=1)
        uncertain = max_proba < 0.6
        y_pred[uncertain] = 1
        
        # 5) 결과 컬럼 추가
        df['예측_클래스'] = y_pred
        df['예측_레이블'] = [CLASS_LABELS[c]['label'] for c in y_pred]
        df['예측_레이블_한글'] = [CLASS_LABELS[c]['label_kr'] for c in y_pred]
        df['저렴_확률'] = y_pred_proba[:, 0]
        df['적정_확률'] = y_pred_proba[:, 1]
        df['비쌈_확률'] = y_pred_proba[:, 2]
        
        # DB 저장을 위해 컬럼명 맞춤
        if "보증금(만원)" in df.columns:
            df["보증금_만원"] = df["보증금(만원)"]
        if "임대료(만원)" in df.columns:
            df["월세_만원"] = df["임대료(만원)"]
        if "환산보증금(만원)" in df.columns:
            df["환산보증금_만원"] = df["환산보증금(만원)"]
            
        print(f"✅ 예측 완료: {len(df)}개 매물")
        
        # 예측 결과 요약
        class_counts = df['예측_레이블_한글'].value_counts()
        print("\n📊 예측 결과 요약:")
        for label, count in class_counts.items():
            print(f"   - {label}: {count}개 ({count/len(df)*100:.1f}%)")
            
        return df
    
    def run(self, save_to_db: bool = True) -> pd.DataFrame:
        """전체 파이프라인 실행"""
        print("\n" + "=" * 60)
        print("🚀 월세 매물 가격 분류 시작")
        print("=" * 60)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 모델 로드
        self.load_model()
        
        # 2. DB에서 데이터 로드
        db = DatabaseManager()
        try:
            db.connect()
            df_raw = db.load_monthly_rent_from_land()
            
            if df_raw.empty:
                print("⚠ 처리할 월세 매물이 없습니다.")
                return df_raw
            
            # 3. 데이터 전처리
            preprocessor = LandDataPreprocessor()
            df_preprocessed = preprocessor.preprocess(df_raw)
            
            # apply_model_to_json.py와 동일한 prepare_data 호출
            df_processed = self.prepare_data(df_preprocessed)
            
            # 4. 예측
            df_result = self.predict(df_processed)
            
            # 5. DB 저장
            if save_to_db and not df_result.empty:
                print("\n💾 데이터베이스 저장 중...")
                db.create_results_table()
                db.save_results(df_result)
                
        except Exception as e:
            print(f"❌ 파이프라인 실행 중 오류: {e}")
            raise
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
        description="월세 매물 가격 분류 (land 테이블 → 결과 테이블)"
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
    args = parser.parse_args()
    
    # 경로 확인 및 출력
    print("\n" + "=" * 60)
    print("📁 설정")
    print("=" * 60)
    print(f"   - 환경: {'Docker' if IS_DOCKER else '로컬'}")
    print(f"   - 모델 경로: {args.model_path}")
    print(f"   - 소스 테이블: {SOURCE_TABLE}")
    print(f"   - 결과 테이블: {RESULTS_TABLE}")
    print(f"   - DB 저장: {'No (dry-run)' if args.dry_run else 'Yes'}")
    
    # 분류기 실행
    classifier = PriceClassifier(args.model_path)
    results_df = classifier.run(save_to_db=not args.dry_run)


if __name__ == "__main__":
    main()
