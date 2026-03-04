import os
import json
import psycopg2
import sys
from pathlib import Path

# Add scripts/03_import to path
current_dir = os.path.dirname(os.path.abspath(__file__))
import_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # scripts/03_import/neo4j/property/ -> scripts/03_import
# property folder is inside neo4j folder ?? Wait.
# scripts/03_import/neo4j/property/property_importer.py
# .parent -> property
# .parent -> neo4j
# .parent -> 03_import
import_dir = str(Path(__file__).resolve().parent.parent.parent) 

sys.path.append(import_dir)

from config import Config
from database import Database

class PropertyImporter:
    """
    매물 데이터를 Neo4j에 import하는 클래스
    
    주요 변경사항:
    - 데이터 소스: PostgreSQL RDB (land 테이블)
    - Neo4j 저장: 매물번호 + 좌표만 저장 (주소, 건물명 등 제외)
    - 상세 정보: PostgreSQL RDB에서 관리
    - 좌표: RDB/land/*.json에서 geocoding된 좌표 사용
    """
    
    def __init__(self):
        self.driver = Database.get_driver()
        self.pg_conn = None

    def _get_postgres_connection(self):
        """PostgreSQL 연결 생성"""
        if self.pg_conn is None or self.pg_conn.closed:
            self.pg_conn = psycopg2.connect(
                host=Config.POSTGRES_HOST,
                port=Config.POSTGRES_PORT,
                database=Config.POSTGRES_DB,
                user=Config.POSTGRES_USER,
                password=Config.POSTGRES_PASSWORD
            )
        return self.pg_conn

    def import_properties(self):
        """매물 데이터를 PostgreSQL에서 읽어 Neo4j에 import"""
        print("Reading property data from PostgreSQL...")
        
        try:
            # PostgreSQL에서 매물 데이터 읽기
            pg_conn = self._get_postgres_connection()
            cursor = pg_conn.cursor()
            
            # land 테이블에서 매물번호만 조회
            print("Executing query: SELECT land_num FROM land...")
            cursor.execute("SELECT land_num FROM land ORDER BY land_num")
            postgres_land_nums = {row[0] for row in cursor.fetchall()}
            print(f"✓ Found {len(postgres_land_nums)} properties in PostgreSQL")
            
            if len(postgres_land_nums) == 0:
                print("⚠ No properties found. Skipping.")
                cursor.close()
                return
                
        except Exception as e:
            print(f"❌ Error connecting to PostgreSQL or querying data: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # RDB/land/*.json에서 좌표 정보 읽기
        land_dir = Path(Config.DATA_DIR).parent / "RDB" / "land"
        
        if not land_dir.exists():
            print(f"⚠️ Land data directory not found: {land_dir}")
            print("Falling back to GraphDB_data/land...")
            land_dir = Path(Config.DATA_DIR) / "land"
        
        # JSON 파일 목록 수집
        json_files = []
        
        if land_dir.exists():
            json_files.extend(list(land_dir.glob("*.json")))
        
        # 2. data/zigbangland 디렉토리 추가 (직방)
        # Docker: /app/data/zigbangland, Local: ../data/zigbangland (Config 기준)
        if os.path.exists("/app/data/zigbangland"):
            zigbang_dir = Path("/app/data/zigbangland")
            print("Docker 환경 감지: zigbangland")
        else:
            zigbang_dir = Path(Config.BASE_DIR) / "data" / "zigbangland"
            print(f"로컬 환경 감지: {zigbang_dir}")
        
        if zigbang_dir.exists():
            json_files.extend(list(zigbang_dir.glob("*.json")))

        print(f"Found {len(json_files)} JSON files with coordinates to process.")
        
        # JSON 파일들을 읽어서 coords_map 생성
        coords_map = {}
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # JSON 파일이 리스트인 경우
                    if isinstance(data, list):
                        for item in data:
                            # land_num 또는 매물번호 필드 확인 (한글 필드명 지원)
                            land_num = item.get('land_num') or item.get('매물번호')
                            
                            # 좌표 정보 추출 (flat 또는 nested 구조 모두 지원)
                            lat = None
                            lon = None
                            
                            # 1. Flat 구조 확인
                            lat = item.get('latitude') or item.get('위도')
                            lon = item.get('longitude') or item.get('경도')
                            
                            # 2. Nested 구조 확인 (좌표_정보 안에 있는 경우)
                            if not lat or not lon:
                                coord_info = item.get('좌표_정보', {})
                                if isinstance(coord_info, dict):
                                    lat = coord_info.get('latitude') or coord_info.get('위도')
                                    lon = coord_info.get('longitude') or coord_info.get('경도')
                            
                            if land_num and lat and lon:
                                coords_map[str(land_num)] = {
                                    'latitude': float(lat),
                                    'longitude': float(lon)
                                }
                    # JSON 파일이 딕셔너리인 경우
                    elif isinstance(data, dict):
                        land_num = data.get('land_num') or data.get('매물번호')
                        
                        # 좌표 정보 추출
                        lat = data.get('latitude') or data.get('위도')
                        lon = data.get('longitude') or data.get('경도')
                        
                        # Nested 구조 확인
                        if not lat or not lon:
                            coord_info = data.get('좌표_정보', {})
                            if isinstance(coord_info, dict):
                                lat = coord_info.get('latitude') or coord_info.get('위도')
                                lon = coord_info.get('longitude') or coord_info.get('경도')
                        
                        if land_num and lat and lon:
                            coords_map[str(land_num)] = {
                                'latitude': float(lat),
                                'longitude': float(lon)
                            }
            except Exception as e:
                print(f"⚠️ Error reading {json_file}: {e}")
                continue
        
        print(f"✓ Loaded coordinates for {len(coords_map)} properties from JSON files")

        with self.driver.session() as session:
            # 제약 조건 및 인덱스 생성
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Property) REQUIRE p.id IS UNIQUE")
            session.run("CREATE POINT INDEX property_location_index IF NOT EXISTS FOR (p:Property) ON (p.location)")
            
            # 기존 매물 ID 조회
            print("Fetching existing properties from Neo4j...")
            result = session.run("MATCH (p:Property) RETURN p.id AS id")
            existing_ids = {record["id"] for record in result}
            print(f"Found {len(existing_ids)} existing properties in Neo4j")

            # PostgreSQL에 있는 매물만 Neo4j에 반영
            batch = []
            batch_size = 500
            total_imported = 0
            total_skipped = 0

            for land_num in postgres_land_nums:
                # 좌표 정보 확인
                if land_num not in coords_map:
                    total_skipped += 1
                    continue
                
                coords = coords_map[land_num]
                batch.append({
                    "id": land_num,
                    "latitude": coords["latitude"],
                    "longitude": coords["longitude"]
                })
                
                # 배치 크기에 도달하면 insert
                if len(batch) >= batch_size:
                    self._insert_batch(session, batch)
                    total_imported += len(batch)
                    print(f"  Progress: {total_imported}/{len(postgres_land_nums)} ({total_imported*100//len(postgres_land_nums)}%)")
                    batch = []
            
            # 남은 배치 insert
            if batch:
                self._insert_batch(session, batch)
                total_imported += len(batch)
                print(f"  Progress: {total_imported}/{len(postgres_land_nums)} (100%)")

            # PostgreSQL에 없는 매물은 Neo4j에서 삭제 (판매 완료)
            sold_ids = existing_ids - postgres_land_nums
            if sold_ids:
                print(f"\nDeleting {len(sold_ids)} sold properties from Neo4j...")
                self._delete_sold_properties(session, list(sold_ids))
                print("✅ Deletion completed")
            else:
                print("\nNo sold properties to delete")

            print(f"\n✅ Import completed!")
            print(f"Total imported/updated: {total_imported}")
            print(f"Total skipped (no coords): {total_skipped}")
            print(f"Total deleted: {len(sold_ids)}")
        
        cursor.close()

    def _insert_batch(self, session, batch):
        """
        매물 배치를 Neo4j에 insert
        
        Neo4j Property 노드 구조:
        - id: 매물번호 (Primary Key)
        - latitude: 위도
        - longitude: 경도
        - location: Neo4j Point (공간 검색용)
        
        주의: 주소, 건물명, 가격 등 상세 정보는 PostgreSQL에서 관리
        """
        query = """
        UNWIND $batch AS row
        MERGE (p:Property {id: row.id})
        SET p.latitude = row.latitude,
            p.longitude = row.longitude,
            p.location = point({latitude: row.latitude, longitude: row.longitude})
        """
        session.run(query, batch=batch)

    def _delete_sold_properties(self, session, sold_ids):
        """
        판매 완료된 매물을 Neo4j에서 삭제
        """
        batch_size = 1000
        for i in range(0, len(sold_ids), batch_size):
            batch = sold_ids[i:i+batch_size]
            query = """
            UNWIND $batch AS id
            MATCH (p:Property {id: id})
            DETACH DELETE p
            """
            session.run(query, batch=batch)
            print(f"  Deleted batch {i//batch_size + 1}/{len(sold_ids)//batch_size + 1}")

if __name__ == "__main__":
    importer = PropertyImporter()
    importer.import_properties()
    Database.close()
