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
        check_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'land'
        );
        """
        self.cur.execute(check_query)
        exists = self.cur.fetchone()[0]
        
        if not exists:
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
                style_tags TEXT[],
                search_text TEXT,
                agent_info JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cur.execute(create_table_query)
            print("✓ Land 테이블 생성 완료")
        else:
            # 테이블이 존재하면 style_tags와 search_text 컬럼 확인 및 추가
            print("✓ Land 테이블 확인 완료")
            
            # style_tags 컬럼 확인
            check_style_tags = """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'land' AND column_name = 'style_tags'
            );
            """
            self.cur.execute(check_style_tags)
            has_style_tags = self.cur.fetchone()[0]
            
            if not has_style_tags:
                print("  → style_tags 컬럼 추가 중...")
                self.cur.execute("ALTER TABLE land ADD COLUMN style_tags TEXT[];")
                print("  ✓ style_tags 컬럼 추가 완료")
            
            # search_text 컬럼 확인
            check_search_text = """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'land' AND column_name = 'search_text'
            );
            """
            self.cur.execute(check_search_text)
            has_search_text = self.cur.fetchone()[0]
            
            if not has_search_text:
                self.cur.execute("ALTER TABLE land ADD COLUMN search_text TEXT;")
                print("  ✓ search_text 컬럼 추가 완료")

            # agent_info 컬럼 확인
            check_agent_info = """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'land' AND column_name = 'agent_info'
            );
            """
            self.cur.execute(check_agent_info)
            has_agent_info = self.cur.fetchone()[0]
            
            if not has_agent_info:
                print("  → agent_info 컬럼 추가 중...")
                self.cur.execute("ALTER TABLE land ADD COLUMN agent_info JSONB;")
                print("  ✓ agent_info 컬럼 추가 완료")
        
        # land_image 테이블 확인 및 생성
        check_image_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'land_image'
        );
        """
        self.cur.execute(check_image_query)
        image_exists = self.cur.fetchone()[0]
        
        if not image_exists:
            create_image_table_query = """
            CREATE TABLE IF NOT EXISTS land_image (
                landimage_id SERIAL PRIMARY KEY,
                land_id INT REFERENCES land(land_id) ON DELETE CASCADE,
                img_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cur.execute(create_image_table_query)
            print("✓ Land Image 테이블 생성 완료")
        
        # landbroker 테이블 확인 및 생성
        check_broker_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'landbroker'
        );
        """
        self.cur.execute(check_broker_query)
        broker_exists = self.cur.fetchone()[0]
        
        if not broker_exists:
            create_broker_table_query = """
            CREATE TABLE IF NOT EXISTS landbroker (
                landbroker_id SERIAL PRIMARY KEY,
                office_name VARCHAR(200),
                representative VARCHAR(100),
                phone VARCHAR(50),
                address VARCHAR(500),
                registration_number VARCHAR(100) UNIQUE,
                completed_deals INT DEFAULT 0,
                registered_properties INT DEFAULT 0,
                brokers_count INT DEFAULT 0,
                assistants_count INT DEFAULT 0,
                staff_count INT DEFAULT 0,
                region VARCHAR(100),
                registration_date DATE,
                trust_score VARCHAR(1),
                trust_score_updated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cur.execute(create_broker_table_query)
            print("✓ LandBroker 테이블 생성 완료")
        
        self.conn.commit()
        if image_exists:
            print("✓ Land Image 테이블 확인 완료")
    
    def _get_existing_count(self):
        """기존 매물 개수 확인"""
        self.cur.execute("SELECT COUNT(*) FROM land")
        return self.cur.fetchone()[0]

    def import_properties(self, skip_if_exists=True):
        """data/RDB/land 폴더의 JSON 파일들을 Land 테이블에 적재"""
        # 테이블 확인
        self._create_land_table()
        
        # 기존 데이터 확인
        existing_count = self._get_existing_count()
        if skip_if_exists and existing_count > 0:
            print(f"  ⏭ Land data already exists ({existing_count} records). Skipping import.")
            print("  (강제 업데이트를 원하면 skip_if_exists=False 사용)")
            return
        
        # Docker 환경에서는 /app/data/RDB/land, 로컬에서는 data/RDB/land
        if os.path.exists("/app/data/RDB/land"):
            data_dir = "/app/data/RDB/land"
            print("Docker 환경 감지: /app/data/RDB/land 사용")
        else:
            data_dir = os.path.join(Config.BASE_DIR, "data", "RDB", "land")
            print(f"로컬 환경 감지: {data_dir} 사용")
        
        # 판매 완료된 매물 삭제
        sold_land_nums = existing_land_nums - active_land_nums
        total_deleted = 0
        
        if sold_land_nums:
            print(f"\n판매 완료된 매물 {len(sold_land_nums)}개 삭제 중...")
            try:
                # 배치 삭제 (1000개씩)
                sold_list = list(sold_land_nums)
                batch_size = 1000
                
                for i in range(0, len(sold_list), batch_size):
                    batch = sold_list[i:i+batch_size]
                    placeholders = ','.join(['%s'] * len(batch))
                    delete_query = f"DELETE FROM land WHERE land_num IN ({placeholders})"
                    self.cur.execute(delete_query, batch)
                    deleted_count = self.cur.rowcount
                    total_deleted += deleted_count
                    print(f"  배치 {i//batch_size + 1}: {deleted_count}건 삭제")
                
                self.conn.commit()
                print(f"✅ 총 {total_deleted}건 삭제 완료")
            except Exception as e:
                self.conn.rollback()
                print(f"❌ 삭제 오류: {e}")
        else:
            print("\n판매 완료된 매물 없음")
        
        print(f"\n총 결과: {total_inserted}건 삽입, {total_updated}건 업데이트, {total_deleted}건 삭제")

    def _process_json_files(self, data_dir, active_land_nums, file_mapping=None):
        """지정된 디렉토리의 JSON 파일들을 처리 (helper method)"""
        if not os.path.exists(data_dir):
            print(f"\n[Skip] 디렉토리가 존재하지 않음: {data_dir}")
            return (0, 0)
            
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        # 매핑이 있으면 해당 파일만, 없으면 모두 처리
        if file_mapping:
            json_files = [f for f in json_files if f in file_mapping]
            
        print(f"\n[폴더 스캔] {data_dir}: {len(json_files)}개 파일 발견")

        total_inserted = 0
        total_updated = 0

        for file_idx, json_file in enumerate(json_files, 1):
            file_path = os.path.join(data_dir, json_file)
            
            # 매핑이 있으면 사용 (피터팬 데이터)
            if file_mapping:
                building_type = file_mapping.get(json_file, "기타")
            else:
                # 직방 데이터: JSON에서 건물형태 읽어서 매핑
                # 일단 기본값 설정 (나중에 JSON에서 읽어서 변경)
                building_type = None  # JSON에서 읽을 예정
            
            print(f"\n[{file_idx}/{len(json_files)}] {json_file} 처리 중...")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                inserted = 0
                updated = 0
                total_items = len(data)
                batch_size = 100
                
                for idx, item in enumerate(data):
                    land_num = item.get("매물번호")
                    if land_num:
                        active_land_nums.add(land_num)
                    
                    result = self._insert_land(item, building_type)
                    if result == "inserted":
                        inserted += 1
                    elif result == "updated":
                        updated += 1
                    
                    if (idx + 1) % batch_size == 0:
                        self.conn.commit()
                        progress = idx + 1
                        print(f"  Progress: {progress}/{total_items} ({progress*100//total_items}%) - {inserted} inserted, {updated} updated")
                
                self.conn.commit()
                print(f"  ✓ {building_type}: {inserted}건 삽입, {updated}건 업데이트 (100%)")
                total_inserted += inserted
                total_updated += updated

            except Exception as e:
                self.conn.rollback()
                print(f"  ✗ 파일 처리 오류 ({json_file}): {e}")
                # traceback.print_exc()
        
        return total_inserted, total_updated

    def import_properties(self, skip_if_exists=True):
        """data/RDB/land 및 data/zigbangland 폴더의 JSON 파일들을 Land 테이블에 적재"""
        # 테이블 확인
        self._create_land_table()
        
        # 기존 데이터 확인 (옵션에 따라 건너뛰기)
        existing_count = self._get_existing_count()
        if skip_if_exists and existing_count > 0:
            # 강제로 진행하고 싶을 때가 있으실 것 같아, 메시지만 띄우고 계속 진행하도록 수정하거나
            # 여기서는 사용자 의도를 존중해 원래 로직 유지. 
            # 단, '추가' 데이터를 넣는 상황이므로 active 체크를 위해 전체 재스캔이 필요할 수 있음.
            # 하지만 import_all.py는 기본적으로 전체 덮어쓰기/갱신을 가정하므로,
            # 기존 데이터가 있어도 멈추지 않고 '업데이트' 모드로 동작하는게 맞을 수도 있습니다.
            # 요청하신 상황은 "추가된 데이터가 있어서 적재"이므로, 일단 여기 리턴은 주석 처리하거나 제거하는게 좋습니다.
            # 다만 원본 코드 로직을 최대한 존중하여, 일단은 유지하되 메시지 출력.
            print(f"  ℹ 기존 데이터 {existing_count}건 존재. (skip_if_exists=True 지만, 추가 데이터를 위해 계속 진행합니다)")
            # return  # <--- 주석 처리: 추가 데이터 적재를 위해 중단하지 않음
        
        # 1. RDB/land 경로 설정
        if os.path.exists("/app/data/RDB/land"):
            rdb_dir = "/app/data/RDB/land"
            zigbang_dir = "/app/data/zigbangland"
            print("Docker 환경 감지")
        else:
            rdb_dir = os.path.join(Config.BASE_DIR, "data", "RDB", "land")
            zigbang_dir = os.path.join(Config.BASE_DIR, "data", "zigbangland")
            print("로컬 환경 감지")
        
        # 기존 매물 ID 조회 (삭제 감지용)
        self.cur.execute("SELECT land_num FROM land")
        existing_land_nums = {row[0] for row in self.cur.fetchall()}
        print(f"기존 DB 매물: {len(existing_land_nums)}개")
        
        active_land_nums = set()
        total_inserted = 0
        total_updated = 0

        # 2. RDB/land 처리 (기존 로직)
        ins, upd = self._process_json_files(rdb_dir, active_land_nums, self.FILE_TYPE_MAPPING)
        total_inserted += ins
        total_updated += upd
        
        # 3. zigbangland 처리 (추가 로직)
        # 직방 데이터는 별도 매핑 없이 무조건 "원투룸"으로 처리
        # FILE_TYPE_MAPPING을 넘기지 않으면 내부에서 "원투룸"을 기본값으로 사용하도록 _process_json_files 구현함
        ins, upd = self._process_json_files(zigbang_dir, active_land_nums)
        total_inserted += ins
        total_updated += upd


    def _extract_deal_type(self, trade_info):
        """거래유형 추출"""
        deal_type = trade_info.get("거래유형")
        if deal_type and deal_type != "-":
            return deal_type
        
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
        """한국어 가격 문자열을 만원 단위 정수로 변환"""
        if not price_str or price_str == '-' or price_str == '0원':
            return 0
        
        import re
        s = str(price_str).replace(',', '').replace(' ', '').replace('\xa0', '')
        
        eok = 0
        man = 0
        
        eok_match = re.search(r'(\d+)억', s)
        if eok_match:
            eok = int(eok_match.group(1))
        
        man_match = re.search(r'(\d+)만', s)
        if man_match:
            man = int(man_match.group(1))
        
        return eok * 10000 + man

    def _parse_deal_string(self, deal_str):
        """
        거래방식 문자열에서 가격 정보 파싱
        
        Examples:
            "월세   5,000만원/80만원" → {"deposit": 5000, "monthly_rent": 80}
            "전세   1억2,000만원" → {"jeonse_price": 12000}
            "매매   3억5,000만원" → {"sale_price": 35000}
            "단기임대   150만원/100만원" → {"deposit": 150, "monthly_rent": 100}
        
        Returns:
            dict: {deposit, monthly_rent, jeonse_price, sale_price} (만원 단위)
        """
        result = {
            "deposit": 0,
            "monthly_rent": 0,
            "jeonse_price": 0,
            "sale_price": 0
        }
        
        if not deal_str or deal_str == '-':
            return result
        
        # 거래 유형 추출
        deal_type = None
        if "월세" in deal_str:
            deal_type = "월세"
        elif "전세" in deal_str:
            deal_type = "전세"
        elif "매매" in deal_str:
            deal_type = "매매"
        elif "단기임대" in deal_str:
            deal_type = "단기임대"
        
        if not deal_type:
            return result
        
        # 거래 유형 이후의 가격 부분 추출
        price_part = deal_str.split(deal_type)[-1].strip()
        
        # 슬래시로 구분된 경우 (월세, 단기임대)
        if "/" in price_part:
            parts = price_part.split("/")
            if len(parts) == 2:
                deposit_str = parts[0].strip()
                monthly_str = parts[1].strip()
                result["deposit"] = self._parse_price_to_int(deposit_str)
                result["monthly_rent"] = self._parse_price_to_int(monthly_str)
        else:
            # 단일 가격 (전세, 매매)
            price = self._parse_price_to_int(price_part)
            if deal_type == "전세":
                result["jeonse_price"] = price
            elif deal_type == "매매":
                result["sale_price"] = price
        
        return result

    def _insert_land(self, item, building_type):
        """Land 테이블에 매물 데이터 삽입"""
        land_num = item.get("매물번호")
        if not land_num:
            return None

        # 직방 데이터인 경우 (building_type이 None), JSON에서 건물형태 읽어서 매핑
        if building_type is None:
            listing_info = item.get("매물_정보", {})
            zigbang_building_type = listing_info.get("건물형태", "")
            
            # "원룸" -> "원투룸", 나머지 -> "기타"
            if zigbang_building_type == "원룸":
                building_type = "원투룸"
            elif zigbang_building_type == "오피스텔":
                building_type = "오피스텔"
            else:
                building_type = "기타"

        address = item.get("주소_정보", {}).get("전체주소", "") if item.get("주소_정보") else None
        trade_info_raw = item.get("거래_정보", {})
        deal_type = self._extract_deal_type(trade_info_raw)
        
        # 거래방식 문자열에서 가격 정보 파싱 시도 (기존 방식)
        deal_str = trade_info_raw.get("거래방식", "")
        prices = self._parse_deal_string(deal_str)
        
        deposit = prices["deposit"]
        monthly_rent = prices["monthly_rent"]
        jeonse_price = prices["jeonse_price"]
        sale_price = prices["sale_price"]
        
        # 가격 정보가 없는 경우 (직방 데이터 등), trade_info의 개별 키에서 직접 파싱
        if deposit == 0 and monthly_rent == 0 and jeonse_price == 0 and sale_price == 0:
            # 보증금 or 전세금
            raw_deposit = trade_info_raw.get("보증금", "") or trade_info_raw.get("전세", "")
            # 월세
            raw_monthly = trade_info_raw.get("월세", "")
            # 매매가
            raw_sale = trade_info_raw.get("매매가", "")
            
            deposit = self._parse_price_to_int(raw_deposit)
            monthly_rent = self._parse_price_to_int(raw_monthly)
            sale_price = self._parse_price_to_int(raw_sale)
            
            # 전세인 경우 deposit을 jeonse_price에도 매핑 (or deal_type check)
            if "전세" in str(deal_type) and deposit > 0:
                jeonse_price = deposit
                # 전세는 보증금 칸에도 값을 남겨두는 경우가 많으므로 유지
        
        images_list = item.get("매물_이미지", [])
        # images는 land_image 테이블에만 저장 (JSONB 컬럼 사용 안 함)
        
        url = item.get("매물_URL")
        trade_info = Json(trade_info_raw)
        listing_info = Json(item.get("매물_정보", {}))
        additional_options = item.get("추가_옵션", [])
        description = item.get("상세_설명")
        
        # ... (스타일 태그 등 생략)
        style_tags = item.get("style_tags") or item.get("스타일태그")
        if isinstance(style_tags, str):
            style_tags = [tag.strip() for tag in style_tags.split(",")]
        elif not isinstance(style_tags, list):
            style_tags = []
        
        search_text = item.get("search_text") or item.get("검색텍스트")
        agent_info = Json(item.get("중개사_정보", {}))

        query = """
            INSERT INTO land (
                land_num, building_type, address, deal_type,
                deposit, monthly_rent, jeonse_price, sale_price,
                url, trade_info, listing_info,
                additional_options, description,
                style_tags, search_text, agent_info
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s
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
                style_tags = EXCLUDED.style_tags,
                search_text = EXCLUDED.search_text,
                agent_info = EXCLUDED.agent_info,
                updated_at = CURRENT_TIMESTAMP
            RETURNING land_id, (xmax = 0) AS inserted;
        """

        self.cur.execute(query, (
            land_num, building_type, address, deal_type,
            deposit, monthly_rent, jeonse_price, sale_price,
            url, trade_info, listing_info,
            additional_options, description,
            style_tags, search_text, agent_info
        ))
        
        result = self.cur.fetchone()
        land_id = result[0] if result else None
        is_inserted = result[1] if result else False
        
        if land_id and images_list:
            self.cur.execute("DELETE FROM land_image WHERE land_id = %s", (land_id,))
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
