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
        # 1. data/GraphDB_data/land 디렉토리에서 JSON 파일 읽기 (기존)
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
            active_ids = set()  # 현재 활성 매물 ID 추적

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
                        
                        # 유효한 ID로 기록
                        active_ids.add(listing_id)
                        
                        # 이미 존재하는 매물이면 스킵 (좌표는 변하지 않는다고 가정)
                        # 업데이트가 필요하다면 이 확인을 제거하거나 별도 로직 추가
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

            # 판매 완료된 매물 삭제
            sold_ids = existing_ids - active_ids
            if sold_ids:
                print(f"\nDeleting {len(sold_ids)} sold properties from Neo4j...")
                self._delete_sold_properties(session, list(sold_ids))
                print("✅ Deletion completed.")
            else:
                print("\nNo sold properties to delete.")

            print(f"\n✅ Import completed!")
            print(f"Total imported: {total_imported}")
            print(f"Total skipped: {total_skipped}")
            print(f"Total deleted: {len(sold_ids)}")

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
