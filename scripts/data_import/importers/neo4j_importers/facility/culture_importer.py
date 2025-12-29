"""
Culture Facility Importer
문화시설(영화관, 미술관, 도서관 등) + 공원 데이터를 Neo4j에 임포트하고 Property와 연결합니다.
"""
import sys
import os
import glob
import pandas as pd

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from config import Config
from database import Database


class CultureImporter:
    def __init__(self):
        self.driver = Database.get_driver()
        self.data_dir = os.path.join(Config.BASE_DIR, "data", "GraphDB_data")
    
    def _get_existing_count(self, session, label):
        result = session.run(f"MATCH (n:{label}) RETURN count(n) as cnt")
        return result.single()["cnt"]
    
    def _get_property_count(self, session):
        result = session.run("MATCH (p:Property) RETURN count(p) as cnt")
        return result.single()["cnt"]
    
    def _get_link_count(self, session, rel_type):
        result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as cnt")
        return result.single()["cnt"]
    
    # ==================== 문화시설 ====================
    def import_culture_nodes(self):
        """문화시설 노드 임포트"""
        print("Importing Culture nodes...")
        
        with self.driver.session() as session:
            existing = self._get_existing_count(session, "Culture")
            if existing > 0:
                print(f"  ⏭ Culture nodes already exist ({existing}). Skipping.")
                return
            
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Culture) REQUIRE c.id IS UNIQUE")
            session.run("CREATE POINT INDEX culture_location_index IF NOT EXISTS FOR (c:Culture) ON (c.location)")
            
            # 1. 문화공간 데이터
            culture_file = os.path.join(self.data_dir, "culture", "서울시 문화공간 정보.csv")
            if os.path.exists(culture_file):
                df = pd.read_csv(culture_file, encoding='utf-8')
                print(f"  Found {len(df)} culture spaces")
                
                batch = []
                for idx, row in df.iterrows():
                    lat = row.get('위도') or row.get('WGS84위도')
                    lon = row.get('경도') or row.get('WGS84경도')
                    name = row.get('시설명') or row.get('문화공간명') or f"Culture_{idx}"
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
                        self._insert_culture_batch(session, batch)
                        batch = []
                
                if batch:
                    self._insert_culture_batch(session, batch)
                print(f"  Imported {len(df)} culture spaces")
            
            # 2. 영화관 데이터
            cinema_file = os.path.join(self.data_dir, "culture", "서울시 영화상영관 인허가 정보.csv")
            if os.path.exists(cinema_file):
                df = pd.read_csv(cinema_file, encoding='utf-8')
                print(f"  Found {len(df)} cinemas")
                
                batch = []
                for idx, row in df.iterrows():
                    lat = row.get('위도') or row.get('WGS84위도')
                    lon = row.get('경도') or row.get('WGS84경도')
                    name = row.get('사업장명') or row.get('상호명') or f"Cinema_{idx}"
                    
                    if pd.notna(lat) and pd.notna(lon):
                        batch.append({
                            "id": f"CINEMA_{idx}",
                            "name": str(name),
                            "category": "영화관",
                            "lat": float(lat),
                            "lon": float(lon)
                        })
                    
                    if len(batch) >= 100:
                        self._insert_culture_batch(session, batch)
                        batch = []
                
                if batch:
                    self._insert_culture_batch(session, batch)
                print(f"  Imported {len(df)} cinemas")
        
        print("Finished importing Culture nodes.")
        self.link_culture()
    
    def _insert_culture_batch(self, session, batch):
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
            existing = self._get_link_count(session, "NEAR_CULTURE")
            if existing > 0:
                print(f"  ⏭ NEAR_CULTURE links already exist ({existing}). Skipping.")
                return
            
            total = self._get_property_count(session)
            if total == 0:
                print("  ⚠ No properties found. Skipping.")
                return
            
            print(f"  Total properties: {total}")
            
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
                    SET r.distance = toInteger(round(point.distance(p.location, c.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, c.location) * 1.3) / 80))
                    RETURN count(r) as cnt
                """, offset=offset, limit=batch_size)
                linked_count += result.single()["cnt"]
                offset += batch_size
                progress = min(offset, total)
                print(f"  Culture linking: {progress}/{total} ({progress*100//total}%) - {linked_count} links")
        
        print(f"Finished linking Culture facilities. Total links: {linked_count}")
    
    # ==================== 공원 ====================
    def import_park(self):
        """공원 노드 임포트"""
        print("Importing Park nodes...")
        
        with self.driver.session() as session:
            existing = self._get_existing_count(session, "Park")
            if existing > 0:
                print(f"  ⏭ Parks already exist ({existing}). Skipping import.")
                return
        
        park_dir = os.path.join(self.data_dir, "park")
        files = glob.glob(os.path.join(park_dir, "*.csv"))
        print(f"Found {len(files)} Park data files.")
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Park) REQUIRE p.id IS UNIQUE")
            session.run("CREATE POINT INDEX park_location_index IF NOT EXISTS FOR (p:Park) ON (p.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (p:Park {id: row.id})
            SET p.name = row.name,
                p.type = row.type,
                p.area = row.area,
                p.latitude = row.lat,
                p.longitude = row.lon,
                p.location = point({latitude: row.lat, longitude: row.lon})
            """
            
            for file_idx, file_path in enumerate(files, 1):
                print(f"  [{file_idx}/{len(files)}] Processing {os.path.basename(file_path)}...")
                try:
                    df = pd.read_csv(file_path, encoding='cp949')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='utf-8')
                
                df = df.dropna(subset=['위도', '경도'])
                total_rows = len(df)
                    
                batch_size = 300
                batch = []
                processed = 0
                
                for _, row in df.iterrows():
                    area_val = row.get('공원면적', 0)
                    if pd.isna(area_val):
                        area_val = 0
                    
                    batch.append({
                        "id": str(row['관리번호']),
                        "name": str(row['공원명']),
                        "type": str(row['공원구분']),
                        "area": float(area_val),
                        "lat": float(row['위도']),
                        "lon": float(row['경도'])
                    })
                    
                    if len(batch) >= batch_size:
                        session.run(query, batch=batch)
                        processed += len(batch)
                        print(f"    Park progress: {processed}/{total_rows} ({processed*100//total_rows}%)")
                        batch = []
                if batch:
                    session.run(query, batch=batch)
                    processed += len(batch)
                    print(f"    Park progress: {processed}/{total_rows} (100%)")
                    
        print("Finished importing Parks.")
        self.link_park()
    
    def link_park(self):
        """Property와 Park 간 NEAR_PARK 관계 생성 (500m 이내)"""
        print("Linking Parks (500m)...")
        
        with self.driver.session() as session:
            existing = self._get_link_count(session, "NEAR_PARK")
            if existing > 0:
                print(f"  ⏭ NEAR_PARK links already exist ({existing}). Skipping.")
                return
            
            total = self._get_property_count(session)
            if total == 0:
                print("  ⚠ No properties found. Skipping.")
                return
            print(f"  Total properties: process: {total}")
            
            batch_size = 500
            offset = 0
            linked_count = 0
            
            while offset < total:
                result = session.run("""
                    MATCH (p:Property)
                    WITH p SKIP $offset LIMIT $limit
                    MATCH (pk:Park)
                    WHERE point.distance(p.location, pk.location) < 500
                    MERGE (p)-[r:NEAR_PARK]->(pk)
                    SET r.distance = toInteger(round(point.distance(p.location, pk.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, pk.location) * 1.3) / 80))
                    RETURN count(r) as cnt
                """, offset=offset, limit=batch_size)
                linked_count += result.single()["cnt"]
                offset += batch_size
                progress = min(offset, total)
                print(f"  Park linking: {progress}/{total} ({progress*100//total}%) - {linked_count} links")
        
        print(f"Finished linking Parks. Total links: {linked_count}")


if __name__ == "__main__":
    importer = CultureImporter()
    importer.import_culture_nodes()
    importer.import_park()
    Database.close()

