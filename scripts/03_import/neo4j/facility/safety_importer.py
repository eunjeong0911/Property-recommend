import os
import pandas as pd
from config import Config
from database import Database

class SafetyImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def _get_existing_count(self, session, label):
        result = session.run(f"MATCH (n:{label}) RETURN count(n) as cnt")
        return result.single()["cnt"]

    def _get_property_count(self, session):
        result = session.run("MATCH (p:Property) RETURN count(p) as cnt")
        return result.single()["cnt"]

    def _get_link_count(self, session, rel_type):
        result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as cnt")
        return result.single()["cnt"]

    def import_cctv(self):
        with self.driver.session() as session:
            existing = self._get_existing_count(session, "CCTV")
            if existing > 0: 
                print(f"  ⏭ CCTV already exists ({existing}). Skipping import.")
                return
        
        file_path = os.path.join(Config.DATA_DIR, "safety", "12_04_08_E_CCTV정보.xlsx")
        print(f"Loading CCTV data from {file_path}...")
        
        df = pd.read_excel(file_path)
        df = df[df['소재지도로명주소'].str.contains("서울특별시", na=False)]
        df = df.dropna(subset=['WGS84위도', 'WGS84경도'])
        total_rows = len(df)
        print(f"Found {total_rows} CCTV records.")
        
        with self.driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:CCTV) REQUIRE c.id IS UNIQUE")
                session.run("CREATE POINT INDEX cctv_location_index IF NOT EXISTS FOR (c:CCTV) ON (c.location)")
            except Exception as e:
                print(f"Warning: Schema creation failed: {e}")

            query = """
            UNWIND $batch AS row
            MERGE (c:CCTV {id: row.id})
            SET c.purpose = row.purpose,
                c.count = row.count,
                c.latitude = row.lat,
                c.longitude = row.lon,
                c.location = point({latitude: row.lat, longitude: row.lon}),
                c.address = row.address
            """
            
            batch_size = 500
            batch = []
            processed = 0
            
            for _, row in df.iterrows():
                cctv_id = f"CCTV_{row['번호']}"
                address = str(row['소재지도로명주소'])
                
                batch.append({
                    "id": cctv_id,
                    "purpose": str(row['설치목적구분']),
                    "count": int(row['카메라대수']) if pd.notna(row['카메라대수']) else 1,
                    "lat": float(row['WGS84위도']),
                    "lon": float(row['WGS84경도']),
                    "address": address
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    processed += len(batch)
                    print(f"  CCTV progress: {processed}/{total_rows} ({processed*100//total_rows}%)")
                    batch = []
            if batch:
                session.run(query, batch=batch)
                processed += len(batch)
                print(f"  CCTV progress: {processed}/{total_rows} (100%)")
                
        print("Finished importing CCTV.")
        self.link_cctv()

    def link_cctv(self):
        print("Linking CCTV (200m)...")
        with self.driver.session() as session:
            total = self._get_property_count(session)
            if total == 0:
                print("  ⚠ No properties found. Skipping.")
                return
            print(f"  Total properties to process: {total}")
            
            batch_size = 500
            offset = 0
            linked_count = 0
            
            while offset < total:
                result = session.run("""
                    MATCH (p:Property)
                    WITH p SKIP $offset LIMIT $limit
                    MATCH (c:CCTV)
                    WHERE point.distance(p.location, c.location) < 200
                    MERGE (p)-[r:NEAR_CCTV]->(c)
                    SET r.distance = toInteger(round(point.distance(p.location, c.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, c.location) * 1.3) / 80))
                    RETURN count(r) as cnt
                """, offset=offset, limit=batch_size)
                linked_count += result.single()["cnt"]
                offset += batch_size
                progress = min(offset, total)
                print(f"  CCTV linking: {progress}/{total} ({progress*100//total}%) - {linked_count} links")

    def import_bell(self):
        with self.driver.session() as session:
            existing = self._get_existing_count(session, "EmergencyBell")
            if existing > 0:
                print(f"  ⏭ Emergency bells already exist ({existing}). Skipping import.")
                return
        
        file_path = os.path.join(Config.DATA_DIR, "safety", "12_04_09_E_안전비상벨위치정보.xlsx")
        print(f"Loading Emergency Bell data from {file_path}...")
        
        df = pd.read_excel(file_path)
        df = df[df['소재지도로명주소'].str.contains("서울특별시", na=False)]
        df = df.dropna(subset=['WGS84위도', 'WGS84경도'])
        total_rows = len(df)
        print(f"Found {total_rows} Emergency Bell records.")
        
        with self.driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (b:EmergencyBell) REQUIRE b.id IS UNIQUE")
                session.run("CREATE POINT INDEX bell_location_index IF NOT EXISTS FOR (b:EmergencyBell) ON (b.location)")
            except Exception as e:
                print(f"Warning: Schema creation failed: {e}")

            query = """
            UNWIND $batch AS row
            MERGE (b:EmergencyBell {id: row.id})
            SET b.location_desc = row.location_desc,
                b.latitude = row.lat,
                b.longitude = row.lon,
                b.location = point({latitude: row.lat, longitude: row.lon}),
                b.address = row.address,
                b.police_station = row.police_station
            """
            
            batch_size = 500
            batch = []
            processed = 0
            
            for _, row in df.iterrows():
                bell_id = str(row['안전비상벨관리번호'])
                address = str(row['소재지도로명주소'])
                
                batch.append({
                    "id": bell_id,
                    "location_desc": str(row['설치위치']) if pd.notna(row['설치위치']) else "",
                    "lat": float(row['WGS84위도']),
                    "lon": float(row['WGS84경도']),
                    "address": address,
                    "police_station": str(row['관리기관명']) if pd.notna(row['관리기관명']) else ""
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    processed += len(batch)
                    print(f"  Bell progress: {processed}/{total_rows} ({processed*100//total_rows}%)")
                    batch = []
            if batch:
                session.run(query, batch=batch)
                processed += len(batch)
                print(f"  Bell progress: {processed}/{total_rows} (100%)")
                
        print("Finished importing Emergency Bells.")
        self.link_bell()

    def link_bell(self):
        print("Linking Emergency Bells (200m)...")
        with self.driver.session() as session:
            total = self._get_property_count(session)
            if total == 0:
                print("  ⚠ No properties found. Skipping.")
                return
            print(f"  Total properties to process: {total}")
            
            batch_size = 500
            offset = 0
            linked_count = 0
            
            while offset < total:
                result = session.run("""
                    MATCH (p:Property)
                    WITH p SKIP $offset LIMIT $limit
                    MATCH (b:EmergencyBell)
                    WHERE point.distance(p.location, b.location) < 200
                    MERGE (p)-[r:NEAR_BELL]->(b)
                    SET r.distance = toInteger(round(point.distance(p.location, b.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, b.location) * 1.3) / 80))
                    RETURN count(r) as cnt
                """, offset=offset, limit=batch_size)
                linked_count += result.single()["cnt"]
                offset += batch_size
                progress = min(offset, total)
                print(f"  Bell linking: {progress}/{total} ({progress*100//total}%) - {linked_count} links")

    def import_police(self):
        with self.driver.session() as session:
            existing = self._get_existing_count(session, "PoliceStation")
            if existing > 0:
                print(f"  ⏭ Police stations already exist ({existing}). Skipping import.")
                return
        
        file_path = os.path.join(Config.DATA_DIR, "office", "경찰청_전국 지구대 파출소 주소 현황_20241231.csv")
        print(f"Loading Police data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
        df = df[df['주소'].str.contains("서울특별시", na=False)]
        df = df.dropna(subset=['위도', '경도'])
        total_rows = len(df)
        
        print(f"Found {total_rows} police stations with coordinates")
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:PoliceStation) REQUIRE p.id IS UNIQUE")
            session.run("CREATE POINT INDEX police_location_index IF NOT EXISTS FOR (p:PoliceStation) ON (p.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (p:PoliceStation {id: row.id})
            SET p.name = row.name,
                p.division = row.division,
                p.latitude = row.lat,
                p.longitude = row.lon,
                p.location = point({latitude: row.lat, longitude: row.lon}),
                p.address = row.address
            """
            
            batch_size = 100
            batch = []
            processed = 0
            
            for _, row in df.iterrows():
                address = str(row['주소'])
                lat = float(row['위도'])
                lon = float(row['경도'])
                    
                police_id = f"POLICE_{row['연번']}_{row['관서명']}"
                
                batch.append({
                    "id": police_id,
                    "name": str(row['관서명']),
                    "division": str(row['구분']),
                    "lat": lat,
                    "lon": lon,
                    "address": address
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    processed += len(batch)
                    print(f"  Police progress: {processed}/{total_rows} ({processed*100//total_rows}%)")
                    batch = []
                    
            if batch:
                session.run(query, batch=batch)
                processed += len(batch)
                print(f"  Police progress: {processed}/{total_rows} (100%)")
                
        print("Finished importing Police Stations.")
        self.link_police()

    def link_police(self):
        print("Linking Police Stations (1km)...")
        with self.driver.session() as session:
            total = self._get_property_count(session)
            if total == 0:
                print("  ⚠ No properties found. Skipping.")
                return
            print(f"  Total properties to process: {total}")
            
            batch_size = 500
            offset = 0
            linked_count = 0
            
            while offset < total:
                result = session.run("""
                    MATCH (p:Property)
                    WITH p SKIP $offset LIMIT $limit
                    MATCH (pol:PoliceStation)
                    WHERE point.distance(p.location, pol.location) < 1000
                    MERGE (p)-[r:NEAR_POLICE]->(pol)
                    SET r.distance = toInteger(round(point.distance(p.location, pol.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, pol.location) * 1.3) / 80))
                    RETURN count(r) as cnt
                """, offset=offset, limit=batch_size)
                linked_count += result.single()["cnt"]
                offset += batch_size
                progress = min(offset, total)
                print(f"  Police linking: {progress}/{total} ({progress*100//total}%) - {linked_count} links")

    def import_fire(self):
        with self.driver.session() as session:
            existing = self._get_existing_count(session, "FireStation")
            if existing > 0:
                print(f"  ⏭ Fire stations already exist ({existing}). Skipping import.")
                return
        
        file_path = os.path.join(Config.DATA_DIR, "office", "소방청_시도 소방서 현황_20250701.csv")
        print(f"Loading Fire Station data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
        df = df[df['소방본부'].str.contains("서울", na=False)]
        df = df.dropna(subset=['위도', '경도'])
        total_rows = len(df)
        
        print(f"Found {total_rows} fire stations with coordinates")
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:FireStation) REQUIRE f.id IS UNIQUE")
            session.run("CREATE POINT INDEX fire_location_index IF NOT EXISTS FOR (f:FireStation) ON (f.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (f:FireStation {id: row.id})
            SET f.name = row.name,
                f.hq = row.hq,
                f.latitude = row.lat,
                f.longitude = row.lon,
                f.location = point({latitude: row.lat, longitude: row.lon}),
                f.address = row.address
            """
            
            batch_size = 100
            batch = []
            processed = 0
            
            for _, row in df.iterrows():
                address = str(row['주소'])
                lat = float(row['위도'])
                lon = float(row['경도'])
                    
                fire_id = f"FIRE_{row['순번']}_{row['소방서']}"
                
                batch.append({
                    "id": fire_id,
                    "name": str(row['소방서']),
                    "hq": str(row['소방본부']),
                    "lat": lat,
                    "lon": lon,
                    "address": address
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    processed += len(batch)
                    print(f"  Fire progress: {processed}/{total_rows} ({processed*100//total_rows}%)")
                    batch = []
                    
            if batch:
                session.run(query, batch=batch)
                processed += len(batch)
                print(f"  Fire progress: {processed}/{total_rows} (100%)")
                
        print("Finished importing Fire Stations.")
        self.link_fire()

    def link_fire(self):
        print("Linking Fire Stations (2.5km)...")
        with self.driver.session() as session:
            total = self._get_property_count(session)
            if total == 0:
                print("  ⚠ No properties found. Skipping.")
                return
            print(f"  Total properties to process: {total}")
            
            batch_size = 500
            offset = 0
            linked_count = 0
            
            while offset < total:
                result = session.run("""
                    MATCH (p:Property)
                    WITH p SKIP $offset LIMIT $limit
                    MATCH (f:FireStation)
                    WHERE point.distance(p.location, f.location) < 2500
                    MERGE (p)-[r:NEAR_FIRE]->(f)
                    SET r.distance = toInteger(round(point.distance(p.location, f.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, f.location) * 1.3) / 80))
                    RETURN count(r) as cnt
                """, offset=offset, limit=batch_size)
                linked_count += result.single()["cnt"]
                offset += batch_size
                progress = min(offset, total)
                print(f"  Fire linking: {progress}/{total} ({progress*100//total}%) - {linked_count} links")

if __name__ == "__main__":
    importer = SafetyImporter()
    importer.import_cctv()
    importer.import_bell()
    importer.import_police()
    importer.import_fire()
    Database.close()
