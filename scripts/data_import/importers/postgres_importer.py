import os
import json
import psycopg2
from psycopg2.extras import Json
from config import Config

class PostgresImporter:
    """
    PostgreSQL Land 테이블에 매물 데이터를 적재하는 Importer
    
    ERD 기준 Land 테이블:
    - land_id (PK, SERIAL)
    - landbroker_id (FK, int) - 중개사 id
    - land_num (varchar(10), NOT NULL) - 매물번호
    - building_type (varchar(10), NOT NULL) - 건물형태 (원룸, 빌라, 다가구 등)
    - address (varchar(50)) - 주소
    - like_count (int(10)) - 찜수
    - view_count (int(10)) - 조회수
    - deal_type (varchar(30)) - 거래방식 (전세/월세/매매)
    - user_profiles_id (FK, int) - 사용자 프로필 id
    """
    
    # 파일명과 building_type 매핑 (_parsed.json 파일 사용)
    FILE_TYPE_MAPPING = {
        "00_통합_빌라주택_parsed.json": "빌라주택",
        "00_통합_아파트_parsed.json": "아파트",
        "00_통합_오피스텔_parsed.json": "오피스텔",
        "00_통합_원투룸_parsed.json": "원투룸"
    }
    
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        
    def _create_land_table(self):
        """Land 테이블 생성 (없으면 생성)"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS land (
            land_id SERIAL PRIMARY KEY,
            landbroker_id INT,
            land_num VARCHAR(20) NOT NULL,
            building_type VARCHAR(20) NOT NULL,
            address VARCHAR(200),
            like_count INT DEFAULT 0,
            view_count INT DEFAULT 0,
            deal_type VARCHAR(50),
            user_profiles_id INT,
            url TEXT,
            images JSONB,
            trade_info JSONB,
            listing_info JSONB,
            additional_options TEXT[],
            description TEXT,
            agent_info JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(land_num)
        );
        
        CREATE INDEX IF NOT EXISTS idx_land_building_type ON land(building_type);
        CREATE INDEX IF NOT EXISTS idx_land_address ON land(address);
        CREATE INDEX IF NOT EXISTS idx_land_deal_type ON land(deal_type);
        """
        self.cur.execute(create_table_query)
        self.conn.commit()
        print("✓ Land 테이블 생성/확인 완료")

    def import_properties(self):
        """data/landData 폴더의 JSON 파일들을 Land 테이블에 적재"""
        # 테이블 생성
        self._create_land_table()
        
        # Docker 환경에서는 /data/landData, 로컬에서는 GraphDB_data/home_data
        if os.path.exists("/data/landData"):
            data_dir = "/data/landData"
            print("Docker 환경 감지: /data/landData 사용")
        else:
            # 로컬에서는 GraphDB_data/home_data 사용 (parsed 파일 있는 곳)
            data_dir = os.path.join(Config.BASE_DIR, "GraphDB_data", "home_data")
            print(f"로컬 환경 감지: {data_dir} 사용")
        
        if not os.path.exists(data_dir):
            print(f"✗ 데이터 디렉토리를 찾을 수 없습니다: {data_dir}")
            return

        # 처리할 JSON 파일 목록
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json') and f in self.FILE_TYPE_MAPPING]
        print(f"처리할 JSON 파일: {len(json_files)}개")
        
        total_inserted = 0
        total_updated = 0
        
        for json_file in json_files:
            file_path = os.path.join(data_dir, json_file)
            building_type = self.FILE_TYPE_MAPPING.get(json_file, "기타")
            
            print(f"\n[{building_type}] {json_file} 처리 중...")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                inserted = 0
                updated = 0
                
                for item in data:
                    result = self._insert_land(item, building_type)
                    if result == "inserted":
                        inserted += 1
                    elif result == "updated":
                        updated += 1
                
                self.conn.commit()
                print(f"  ✓ {building_type}: {inserted}건 삽입, {updated}건 업데이트")
                total_inserted += inserted
                total_updated += updated

            except Exception as e:
                self.conn.rollback()
                print(f"  ✗ 파일 처리 오류 ({json_file}): {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n총 결과: {total_inserted}건 삽입, {total_updated}건 업데이트")

    def _extract_deal_type(self, trade_info):
        """거래유형 추출 (parsed 파일에서는 거래유형 필드 직접 사용)"""
        # parsed 파일의 경우 거래유형 필드가 있음
        deal_type = trade_info.get("거래유형")
        if deal_type and deal_type != "-":
            return deal_type
        
        # fallback: 기존 거래방식 필드에서 추출
        deal_str = trade_info.get("거래방식", "")
        if "전세" in deal_str:
            return "전세"
        elif "월세" in deal_str:
            return "월세"
        elif "매매" in deal_str:
            return "매매"
        elif "단기임대" in deal_str:
            return "단기임대"
        return deal_str[:50] if deal_str else None

    def _insert_land(self, item, building_type):
        """Land 테이블에 매물 데이터 삽입"""
        land_num = item.get("매물번호")
        if not land_num:
            return None

        # 필드 추출
        address = item.get("주소_정보", {}).get("전체주소", "")[:200] if item.get("주소_정보") else None
        trade_info = item.get("거래_정보", {})
        deal_type = self._extract_deal_type(trade_info)
        
        url = item.get("매물_URL")
        images = Json(item.get("매물_이미지", []))
        trade_info_json = Json(trade_info)
        listing_info = Json(item.get("매물_정보", {}))
        additional_options = item.get("추가_옵션", [])
        description = item.get("상세_설명")
        agent_info = Json(item.get("중개사_정보", {}))

        # UPSERT 쿼리
        query = """
            INSERT INTO land (
                land_num, building_type, address, deal_type,
                url, images, trade_info, listing_info, 
                additional_options, description, agent_info
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (land_num) DO UPDATE SET
                building_type = EXCLUDED.building_type,
                address = EXCLUDED.address,
                deal_type = EXCLUDED.deal_type,
                url = EXCLUDED.url,
                images = EXCLUDED.images,
                trade_info = EXCLUDED.trade_info,
                listing_info = EXCLUDED.listing_info,
                additional_options = EXCLUDED.additional_options,
                description = EXCLUDED.description,
                agent_info = EXCLUDED.agent_info,
                updated_at = CURRENT_TIMESTAMP
            RETURNING (xmax = 0) AS inserted;
        """

        self.cur.execute(query, (
            land_num, building_type, address, deal_type,
            url, images, trade_info_json, listing_info,
            additional_options, description, agent_info
        ))
        
        result = self.cur.fetchone()
        return "inserted" if result and result[0] else "updated"

    def close(self):
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    importer = PostgresImporter()
    try:
        importer.import_properties()
    finally:
        importer.close()
