"""
데이터베이스 관리 모듈
PostgreSQL 연결 및 결과 저장
"""
import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Dict
import pandas as pd
from .config import DB_CONFIG, RESULTS_TABLE, CLASS_LABELS


class DatabaseManager:
    """PostgreSQL 데이터베이스 관리 클래스"""
    
    def __init__(self, db_config: Dict = None):
        """
        Args:
            db_config: 데이터베이스 연결 설정 (None이면 config.py의 설정 사용)
        """
        self.db_config = db_config or DB_CONFIG
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print(f"✅ 데이터베이스 연결 성공: {self.db_config['database']}")
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✅ 데이터베이스 연결 종료")
    
    def create_table(self):
        """결과 저장 테이블 생성"""
        create_table_sql = f"""
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
        
        try:
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            print(f"✅ 테이블 생성/확인 완료: {RESULTS_TABLE}")
        except Exception as e:
            print(f"❌ 테이블 생성 실패: {e}")
            self.conn.rollback()
            raise
    
    def save_results(self, results_df: pd.DataFrame):
        """
        분류 결과를 데이터베이스에 저장
        
        Args:
            results_df: 예측 결과가 포함된 DataFrame
        """
        if results_df.empty:
            print("⚠️  저장할 데이터가 없습니다.")
            return
        
        # INSERT ... ON CONFLICT UPDATE 쿼리 (upsert)
        insert_sql = f"""
        INSERT INTO {RESULTS_TABLE} (
            매물번호, 매물_URL, 전체주소, 자치구명, 법정동명, 건물용도,
            보증금_만원, 월세_만원, 임대면적, 층, 건축년도,
            예측_클래스, 예측_레이블, 예측_레이블_한글,
            저렴_확률, 적정_확률, 비쌈_확률
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (매물번호) 
        DO UPDATE SET
            매물_URL = EXCLUDED.매물_URL,
            전체주소 = EXCLUDED.전체주소,
            자치구명 = EXCLUDED.자치구명,
            법정동명 = EXCLUDED.법정동명,
            건물용도 = EXCLUDED.건물용도,
            보증금_만원 = EXCLUDED.보증금_만원,
            월세_만원 = EXCLUDED.월세_만원,
            임대면적 = EXCLUDED.임대면적,
            층 = EXCLUDED.층,
            건축년도 = EXCLUDED.건축년도,
            예측_클래스 = EXCLUDED.예측_클래스,
            예측_레이블 = EXCLUDED.예측_레이블,
            예측_레이블_한글 = EXCLUDED.예측_레이블_한글,
            저렴_확률 = EXCLUDED.저렴_확률,
            적정_확률 = EXCLUDED.적정_확률,
            비쌈_확률 = EXCLUDED.비쌈_확률,
            예측_일시 = CURRENT_TIMESTAMP;
        """
        
        # 데이터 준비
        records = []
        for _, row in results_df.iterrows():
            record = (
                row["매물번호"],
                row["매물_URL"],
                row["전체주소"],
                row["자치구명"],
                row["법정동명"],
                row["건물용도"],
                float(row["보증금(만원)"]),
                float(row["임대료(만원)"]),
                float(row["임대면적"]),
                int(row["층"]),
                int(row["건축년도"]),
                int(row["예측_클래스"]),
                row["예측_레이블"],
                row["예측_레이블_한글"],
                float(row["저렴_확률"]),
                float(row["적정_확률"]),
                float(row["비쌈_확률"]),
            )
            records.append(record)
        
        try:
            # Batch insert
            execute_batch(self.cursor, insert_sql, records, page_size=100)
            self.conn.commit()
            print(f"✅ {len(records)}개 레코드 저장 완료")
        except Exception as e:
            print(f"❌ 데이터 저장 실패: {e}")
            self.conn.rollback()
            raise
    
    def get_statistics(self) -> Dict:
        """
        저장된 결과의 통계 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        try:
            # 전체 레코드 수
            self.cursor.execute(f"SELECT COUNT(*) FROM {RESULTS_TABLE};")
            total_count = self.cursor.fetchone()[0]
            
            # 클래스별 분포
            self.cursor.execute(f"""
                SELECT 예측_레이블_한글, COUNT(*) 
                FROM {RESULTS_TABLE} 
                GROUP BY 예측_레이블_한글
                ORDER BY 예측_레이블_한글;
            """)
            class_distribution = dict(self.cursor.fetchall())
            
            # 자치구별 분포
            self.cursor.execute(f"""
                SELECT 자치구명, COUNT(*) 
                FROM {RESULTS_TABLE} 
                GROUP BY 자치구명
                ORDER BY COUNT(*) DESC
                LIMIT 10;
            """)
            gu_distribution = dict(self.cursor.fetchall())
            
            return {
                "total_count": total_count,
                "class_distribution": class_distribution,
                "top_10_gu": gu_distribution
            }
        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")
            return {}
