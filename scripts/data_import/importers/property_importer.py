import os
import json
from pathlib import Path
from config import Config
from database import Database

class PropertyImporter:
    """
    매물 데이터를 Neo4j에 import하는 클래스
    
    주요 변경사항:
    - 데이터 소스: data/GraphDB_data/land/*.json (좌표 정보 포함)
    - Neo4j 저장: 매물번호 + 좌표만 저장 (주소, 건물명 등 제외)
    - 상세 정보: PostgreSQL RDB에서 관리
    - Geocoding: 불필요 (JSON에 좌표 이미 포함)
    """
    
    def __init__(self):
        self.driver = Database.get_driver()

    def import_properties(self):
        """매물 데이터를 Neo4j에 import"""
        # data/GraphDB_data/land 디렉토리에서 JSON 파일 읽기
        land_dir = Path(Config.DATA_DIR) / "land"
        
        if not land_dir.exists():
            print(f"Land data directory not found: {land_dir}")
            return

        json_files = list(land_dir.glob("*.json"))
        print(f"Found {len(json_files)} JSON files with coordinates to process.")

        with self.driver.session() as session:
            # 제약 조건 및 인덱스 생성
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Property) REQUIRE p.id IS UNIQUE")
            session.run("CREATE POINT INDEX property_location_index IF NOT EXISTS FOR (p:Property) ON (p.location)")
            
            # 기존 매물 ID 조회 (중복 import 방지)
            print("Fetching existing properties...")
            result = session.run("MATCH (p:Property) RETURN p.id AS id")
            existing_ids = {record["id"] for record in result}
            print(f"Found {len(existing_ids)} existing properties.")

            total_imported = 0
            total_skipped = 0

            for file_idx, json_file in enumerate(json_files, 1):
                print(f"\n[{file_idx}/{len(json_files)}] Processing {json_file.name}...")
                
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    batch = []
                    batch_size = 500  # Reduced from 1000 for stability
                    skipped = 0
                    file_total = len(data)
                    file_processed = 0

                    for item in data:
                        listing_id = item.get("매물번호")
                        coords_info = item.get("좌표_정보", {})
                        
                        # 매물번호 검증
                        if not listing_id:
                            skipped += 1
                            continue
                        
                        # 중복 확인
                        if listing_id in existing_ids:
                            skipped += 1
                            continue

                        # 좌표 정보 추출
                        lat = coords_info.get("위도")
                        lng = coords_info.get("경도")
                        
                        if lat is None or lng is None:
                            skipped += 1
                            continue
                        
                        # 배치에 추가 (매물번호 + 좌표만)
                        batch.append({
                            "id": listing_id,
                            "latitude": lat,
                            "longitude": lng
                        })
                        
                        # 배치 크기에 도달하면 insert
                        if len(batch) >= batch_size:
                            self._insert_batch(session, batch)
                            total_imported += len(batch)
                            file_processed += len(batch)
                            print(f"  Property progress: {file_processed}/{file_total} ({file_processed*100//file_total}%)")
                            batch = []
                    
                    # 남은 배치 insert
                    if batch:
                        self._insert_batch(session, batch)
                        total_imported += len(batch)
                        file_processed += len(batch)
                        print(f"  Property progress: {file_processed}/{file_total} (100%)")
                    
                    total_skipped += skipped
                    print(f"  Imported: {file_total - skipped}, Skipped: {skipped}")

                except Exception as e:
                    print(f"  Error processing file {json_file.name}: {e}")

            print(f"\n✅ Import completed!")
            print(f"Total imported: {total_imported}")
            print(f"Total skipped: {total_skipped}")

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

if __name__ == "__main__":
    importer = PropertyImporter()
    importer.import_properties()
    Database.close()
