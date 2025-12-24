import os
import json
import psycopg2
from psycopg2.extras import Json
from config import Config

class PostgresImporter:
    """
    PostgreSQL Land 테이블에 매물 데이터를 적재하는 Importer
    
    데이터 역할 분리:
    - PostgreSQL: 매물의 모든 상세 정보 저장 (주소, 가격, 옵션, 이미지, 설명 등)
    - Neo4j: 매물번호 + 좌표만 저장 (공간 기반 그래프 검색용)
    
    데이터 소스:
    - 경로: data/RDB/land/*.json
    - 파일: 00_통합_빌라주택.json, 00_통합_아파트.json, 00_통합_오피스텔.json, 00_통합_원투룸.json
    - 내용: 크롤링한 매물의 전체 정보
    
    ERD 기준 Land 테이블:
    - land_id (PK, SERIAL)
    - landbroker_id (FK, int) - 중개사 id
    - land_num (varchar(20), NOT NULL) - 매물번호
    - building_type (varchar(20), NOT NULL) - 건물형태 (원룸, 빌라, 다가구 등)
    - address (varchar(200)) - 주소
    - like_count (int) - 찜수
    - view_count (int) - 조회수
    - deal_type (varchar(50)) - 거래방식 (전세/월세/매매)
    - user_profiles_id (FK, int) - 사용자 프로필 id
    - url (text) - 매물 URL
    - images (jsonb) - 매물 이미지 목록
    - trade_info (jsonb) - 거래 정보 (가격, 면적 등)
    - listing_info (jsonb) - 매물 정보 (방 개수, 층수 등)
    - additional_options (text[]) - 추가 옵션
    - description (text) - 상세 설명
    - agent_info (jsonb) - 중개사 정보
    """
    
    # 파일명과 building_type 매핑 (RDB/land의 JSON 파일 사용)
    FILE_TYPE_MAPPING = {
        "00_통합_빌라주택.json": "빌라주택",
        "00_통합_아파트.json": "아파트",
        "00_통합_오피스텔.json": "오피스텔",
        "00_통합_원투룸.json": "원투룸"
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
        """Land 테이블 확인 (init.sql에서 생성됨)"""
        # init.sql에서 이미 생성되어 있으므로 확인만 수행
        check_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'land'
        );
        """
        self.cur.execute(check_query)
        exists = self.cur.fetchone()[0]
        
        if not exists:
            # land 테이블이 없으면 생성 (init.sql 스키마와 동일)
            create_table_query = """
            CREATE TABLE IF NOT EXISTS land (
                land_id SERIAL PRIMARY KEY,
                land_num VARCHAR(20) UNIQUE NOT NULL,
                landbroker_id INT,
                building_type VARCHAR(20) NOT NULL,
                address VARCHAR(200),
                deal_type VARCHAR(30),
                like_count INT DEFAULT 0,
                view_count INT DEFAULT 0,
                deposit INT DEFAULT 0,
                monthly_rent INT DEFAULT 0,
                jeonse_price INT DEFAULT 0,
                sale_price INT DEFAULT 0,
                url TEXT,
                images JSONB,
                trade_info JSONB,
                listing_info JSONB,
                additional_options TEXT[],
                description TEXT,
                agent_info JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cur.execute(create_table_query)
            self.conn.commit()
            print("✓ Land 테이블 생성 완료")
        else:
            print("✓ Land 테이블 확인 완료")

    def import_properties(self):
        """data/RDB/land 폴더의 JSON 파일들을 Land 테이블에 적재"""
        # 테이블 확인
        self._create_land_table()
        
        # Docker 환경에서는 /data/RDB/land, 로컬에서는 data/RDB/land 사용 (전처리 완료된 데이터)
        if os.path.exists("/data/RDB/land"):
            data_dir = "/data/RDB/land"
            print("Docker 환경 감지: /data/RDB/land 사용")
        else:
            # 로컬에서는 data/RDB/land 사용
            data_dir = os.path.join(Config.BASE_DIR, "data", "RDB", "land")
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

    def _parse_price_to_int(self, price_str):
        """한국어 가격 문자열을 만원 단위 정수로 변환
        예: '3,000만원' → 3000, '1억 2,500만원' → 12500, '5억' → 50000
        """
        if not price_str or price_str == '-' or price_str == '0원':
            return 0
        
        import re
        # 공백, 쉼표 제거
        s = str(price_str).replace(',', '').replace(' ', '').replace('\xa0', '')
        
        eok = 0  # 억
        man = 0  # 만
        
        # 억 단위 추출
        eok_match = re.search(r'(\d+)억', s)
        if eok_match:
            eok = int(eok_match.group(1))
        
        # 만원 단위 추출
        man_match = re.search(r'(\d+)만', s)
        if man_match:
            man = int(man_match.group(1))
        
        # 만원 단위로 반환 (억 = 10000만)
        return eok * 10000 + man

    def _insert_land(self, item, building_type):
        """Land 테이블에 매물 데이터 삽입 (ERD 기반 하이브리드 스키마)"""
        land_num = item.get("매물번호")
        if not land_num:
            return None

        # 기본 정보 추출
        address = item.get("주소_정보", {}).get("전체주소", "") if item.get("주소_정보") else None
        
        # 거래 정보 추출
        trade_info_raw = item.get("거래_정보", {})
        deal_type = self._extract_deal_type(trade_info_raw)
        
        # 가격 추출 (만원 단위 INT)
        deposit = self._parse_price_to_int(trade_info_raw.get("보증금"))
        monthly_rent = self._parse_price_to_int(trade_info_raw.get("월세"))
        jeonse_price = self._parse_price_to_int(trade_info_raw.get("보증금")) if deal_type == "전세" else 0
        sale_price = self._parse_price_to_int(trade_info_raw.get("매매가"))
        
        # 전세인 경우 보증금이 전세가
        if deal_type == "전세":
            jeonse_price = deposit
            deposit = 0
        
        # 이미지 목록 (별도 테이블에 저장)
        images_list = item.get("매물_이미지", [])
        
        # 기타 JSONB 필드
        url = item.get("매물_URL")
        trade_info = Json(trade_info_raw)
        listing_info = Json(item.get("매물_정보", {}))
        additional_options = item.get("추가_옵션", [])
        description = item.get("상세_설명")
        # agent_info는 저장하지 않음 - reimport_brokers.py에서 landbroker 테이블로 별도 처리

        # UPSERT 쿼리 (land 테이블 스키마 - images, agent_info 제거)
        query = """
            INSERT INTO land (
                land_num, building_type, address, deal_type,
                deposit, monthly_rent, jeonse_price, sale_price,
                url, trade_info, listing_info,
                additional_options, description
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
            ON CONFLICT (land_num) DO UPDATE SET
                building_type = EXCLUDED.building_type,
                address = EXCLUDED.address,
                deal_type = EXCLUDED.deal_type,
                deposit = EXCLUDED.deposit,
                monthly_rent = EXCLUDED.monthly_rent,
                jeonse_price = EXCLUDED.jeonse_price,
                sale_price = EXCLUDED.sale_price,
                url = EXCLUDED.url,
                trade_info = EXCLUDED.trade_info,
                listing_info = EXCLUDED.listing_info,
                additional_options = EXCLUDED.additional_options,
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP
            RETURNING land_id, (xmax = 0) AS inserted;
        """

        self.cur.execute(query, (
            land_num, building_type, address, deal_type,
            deposit, monthly_rent, jeonse_price, sale_price,
            url, trade_info, listing_info,
            additional_options, description
        ))
        
        result = self.cur.fetchone()
        land_id = result[0] if result else None
        is_inserted = result[1] if result else False
        
        # 이미지를 land_image 테이블에 저장
        if land_id and images_list:
            # 기존 이미지 삭제 (업데이트 시)
            self.cur.execute("DELETE FROM land_image WHERE land_id = %s", (land_id,))
            # 새 이미지 INSERT
            for img_url in images_list:
                if img_url:
                    self.cur.execute(
                        "INSERT INTO land_image (land_id, img_url) VALUES (%s, %s)",
                        (land_id, img_url)
                    )
        
        return "inserted" if is_inserted else "updated"

    def close(self):
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    importer = PostgresImporter()
    try:
        importer.import_properties()
    finally:
        importer.close()

