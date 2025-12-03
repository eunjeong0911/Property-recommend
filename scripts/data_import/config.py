import os
import sys
from dotenv import load_dotenv

load_dotenv()


class Config:
    """데이터 import 설정 및 환경 변수 관리"""
    
    # 필수 환경 변수 목록
    REQUIRED_ENV_VARS = [
        "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD",
        "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB",
        "POSTGRES_USER", "POSTGRES_PASSWORD"
    ]
    
    @classmethod
    def validate_env_vars(cls):
        """
        필수 환경 변수 검증
        누락된 변수가 있으면 명확한 오류 메시지와 함께 종료
        """
        missing = []
        for var in cls.REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            print("\n" + "=" * 60)
            print("✗ 오류: 필수 환경 변수가 누락되었습니다")
            print("=" * 60)
            for var in missing:
                print(f"  - {var}")
            print("\n해결 방법:")
            print("  1. .env 파일이 존재하는지 확인하세요")
            print("  2. .env.example을 참조하여 누락된 변수를 추가하세요")
            print("  3. Docker 환경에서는 docker-compose.yml의 environment 섹션을 확인하세요")
            print("=" * 60 + "\n")
            sys.exit(1)
    
    # Neo4j 설정
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")
    
    # PostgreSQL 설정
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    # Kakao API 설정
    KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
    
    # 경로 설정 (Docker 환경 자동 감지)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Docker 환경에서는 /GraphDB_data, 로컬에서는 상대 경로
    if os.path.exists("/GraphDB_data"):
        DATA_DIR = "/GraphDB_data"
        print("Docker 환경 감지: /GraphDB_data 사용")
    else:
        DATA_DIR = os.path.join(BASE_DIR, "GraphDB_data")
        print(f"로컬 환경 감지: {DATA_DIR} 사용")
    
    @classmethod
    def validate_kakao_api_key(cls):
        """Kakao API 키 검증 (지오코딩 사용 시 필요)"""
        if not cls.KAKAO_API_KEY:
            print("\n⚠ 경고: KAKAO_API_KEY가 설정되지 않았습니다")
            print("  지오코딩 기능이 작동하지 않습니다")
            print("  .env 파일에 KAKAO_API_KEY를 추가하세요")
            print("  Kakao Developers (https://developers.kakao.com)에서 API 키를 발급받을 수 있습니다\n")
            return False
        return True
