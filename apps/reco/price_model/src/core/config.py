"""
설정 관리 모듈
환경 변수 및 경로 설정
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parents[5]
DATA_ROOT = PROJECT_ROOT / "data"

# 데이터베이스 설정
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "realestate"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

# 테이블 이름
RESULTS_TABLE = "price_classification_results"

# 파일 경로
JSON_DATA_DIR = DATA_ROOT / "RDB" / "land"
MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "price_model_lightgbm.pkl"
INTEREST_RATE_PATH = (DATA_ROOT / "actual_transaction_price" / "(총합)시장금리_및_대출금리(24.8~25.10).csv")


# 클래스 레이블
CLASS_LABELS = {
    0: {"label": "UNDERPRICED", "label_kr": "저렴"},
    1: {"label": "FAIR", "label_kr": "적정"},
    2: {"label": "OVERPRICED", "label_kr": "비쌈"}
}
