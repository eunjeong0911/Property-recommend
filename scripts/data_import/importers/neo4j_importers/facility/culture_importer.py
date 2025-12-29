"""
Culture Facility Importer
서울시 문화공간 및 영화관 데이터를 Neo4j에 임포트하고 Property와 연결합니다.
"""
import sys
import os
import pandas as pd

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from config import Config
from database import Database


class CultureImporter:
    def __init__(self):
        self.driver = Database.get_driver()
        self.data_dir = os.path.join(Config.BASE_DIR, "data", "GraphDB_data", "culture")
    
    def import_culture_nodes(self):
        """문화시설 노드 임포트"""
        print("Importing Culture nodes...")
        
        with self.driver.session() as session:
            # Constraint 생성
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Culture) REQUIRE c.id IS UNIQUE")
            
            # 1. 문화공간 데이터
            culture_file = os.path.join(self.data_dir, "서울시 문화공간 정보.csv")
            if os.path.exists(culture_file):
                df = pd.read_csv(culture_file, encoding='utf-8')
                print(f"  Found {len(df)} culture spaces")
                
                batch = []
                for idx, row in df.iterrows():
                    # 컬럼명 확인 후 적절히 매핑
                    lat = row.get('위도') or row.get('WGS84위도') or row.get('latitude')
                    lon = row.get('경도') or row.get('WGS84경도') or row.get('longitude')
                    name = row.get('시설명') or row.get('문화공간명') or row.get('공간명') or f"Culture_{idx}"
                    category = row.get('분류') or row.get('카테고리') or 'culture'
                    
                    if pd.notna(lat) and pd.notna(lon):
                        batch.append({
                            "id": f"CULTURE_{idx}",
                            "name": str(name),
                            "category": str(category),
                            "lat": float(lat),
                            "lon": float(lon)
                        })
                    
                    if len(batch) >= 100:
                        self._insert_batch(session, batch)
                        batch = []
                
                if batch:
                    self._insert_batch(session, batch)
                print(f"  Imported {len(df)} culture spaces")
            
            # 2. 영화관 데이터
            cinema_file = os.path.join(self.data_dir, "서울시 영화상영관 인허가 정보.csv")
            if os.path.exists(cinema_file):
                df = pd.read_csv(cinema_file, encoding='utf-8')
                print(f"  Found {len(df)} cinemas")
                
                batch = []
                for idx, row in df.iterrows():
                    lat = row.get('위도') or row.get('WGS84위도') or row.get('latitude')
                    lon = row.get('경도') or row.get('WGS84경도') or row.get('longitude')
                    name = row.get('사업장명') or row.get('상호명') or row.get('영화관명') or f"Cinema_{idx}"
                    
                    if pd.notna(lat) and pd.notna(lon):
                        batch.append({
                            "id": f"CINEMA_{idx}",
                            "name": str(name),
                            "category": "cinema",
                            "lat": float(lat),
                            "lon": float(lon)
                        })
                    
                    if len(batch) >= 100:
                        self._insert_batch(session, batch)
                        batch = []
                
                if batch:
                    self._insert_batch(session, batch)
                print(f"  Imported {len(df)} cinemas")
        
        print("Finished importing Culture nodes.")
        self.link_culture()
    
    def _insert_batch(self, session, batch):
        session.run("""
        UNWIND $batch as row
        MERGE (c:Culture {id: row.id})
        SET c.name = row.name,
            c.category = row.category,
            c.latitude = row.lat,
            c.longitude = row.lon,
            c.location = point({latitude: row.lat, longitude: row.lon})
        """, batch=batch)
    
    def link_culture(self):
        """Property와 Culture 간 NEAR_CULTURE 관계 생성 (500m 이내)"""
        print("Linking Culture facilities (500m)...")
        
        with self.driver.session() as session:
            # 기존 관계 확인
            result = session.run("MATCH ()-[r:NEAR_CULTURE]->() RETURN count(r) as cnt")
            existing = result.single()['cnt']
            if existing > 0:
                print(f"  ⏭ NEAR_CULTURE links already exist ({existing}). Skipping.")
                return
            
            # Property 수 확인
            result = session.run("MATCH (p:Property) RETURN count(p) as cnt")
            total = result.single()['cnt']
            if total == 0:
                print("  ⚠ No properties found. Skipping.")
                return
            
            print(f"  Total properties: {total}")
            
            # 배치 처리
            batch_size = 500
            offset = 0
            linked_count = 0
            
            while offset < total:
                result = session.run("""
                    MATCH (p:Property)
                    WITH p SKIP $offset LIMIT $limit
                    MATCH (c:Culture)
                    WHERE point.distance(p.location, c.location) < 500
                    MERGE (p)-[r:NEAR_CULTURE]->(c)
                    SET r.distance = toInteger(round(point.distance(p.location, c.location)))
                    RETURN count(r) as cnt
                """, offset=offset, limit=batch_size)
                linked_count += result.single()["cnt"]
                offset += batch_size
                progress = min(offset, total)
                print(f"  Culture linking: {progress}/{total} ({progress*100//total}%) - {linked_count} links")
        
        print(f"Finished linking Culture facilities. Total links: {linked_count}")


if __name__ == "__main__":
    importer = CultureImporter()
    importer.import_culture_nodes()
    importer.link_culture()
    Database.close()
