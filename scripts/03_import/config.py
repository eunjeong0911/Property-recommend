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
    
    # Kakao API 설정 (선택사항)
    # 참고: 현재 import 스크립트는 Geocoding을 사용하지 않습니다.
    # 모든 좌표 데이터는 CSV/JSON 파일에 미리 포함되어 있습니다.
    # 이 키는 향후 새로운 데이터 추가 시에만 필요합니다.
    KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
    
    # 경로 설정 (Docker 환경 자동 감지)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    if os.path.exists("/app/data/GraphDB_data"):
        DATA_DIR = "/app/data/GraphDB_data"
        print("Docker 환경 감지: /app/data/GraphDB_data 사용")
    else:
        DATA_DIR = os.path.join(BASE_DIR, "data", "GraphDB_data")
        print(f"로컬 환경 감지: {DATA_DIR} 사용")
    
    @classmethod
    def validate_kakao_api_key(cls):
        """
        Kakao API 키 검증 (선택사항)
        
        참고: 현재 import 프로세스에서는 필요하지 않습니다.
        모든 좌표는 데이터 파일에 미리 포함되어 있습니다.
        새로운 주소의 좌표를 얻어야 할 때만 필요합니다.
        """
        if not cls.KAKAO_API_KEY:
            print("\n⚠ 참고: KAKAO_API_KEY가 설정되지 않았습니다")
            print("  현재 import에는 영향 없습니다 (좌표는 이미 데이터에 포함됨)")
            print("  새로운 주소 geocoding이 필요한 경우에만 .env에 추가하세요")
            print("  Kakao Developers (https://developers.kakao.com)에서 API 키 발급 가능\n")
            return False
        return True
