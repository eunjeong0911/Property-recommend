import os
import pandas as pd
import time
from config import Config
from database import Database
from geocoder import Geocoder

class SafetyImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def import_cctv(self):
        file_path = os.path.join(Config.DATA_DIR, "safety", "12_04_08_E_CCTV정보.xlsx")
        print(f"Loading CCTV data from {file_path}...")
        
        df = pd.read_excel(file_path)
        df = df[df['소재지도로명주소'].str.contains("서울특별시", na=False)]
        df = df.dropna(subset=['WGS84위도', 'WGS84경도'])
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:CCTV) REQUIRE c.id IS UNIQUE")
            session.run("CREATE POINT INDEX cctv_location_index IF NOT EXISTS FOR (c:CCTV) ON (c.location)")
            
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
            
            batch_size = 1000
            batch = []
            
            for _, row in df.iterrows():
                cctv_id = f"CCTV_{row['관리번호']}_{row['번호']}"
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
                    batch = []
            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing CCTV.")
        self._link_cctv()

    def _link_cctv(self):
        print("Linking CCTV (300m)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (c:CCTV)
                WHERE point.distance(p.location, c.location) < 300
                MERGE (p)-[r:NEAR_CCTV]->(c)
                SET r.distance = point.distance(p.location, c.location),
                    r.walking_time = (point.distance(p.location, c.location) * 1.3) / 80
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def import_bell(self):
        file_path = os.path.join(Config.DATA_DIR, "safety", "12_04_09_E_안전비상벨위치정보.xlsx")
        print(f"Loading Emergency Bell data from {file_path}...")
        
        df = pd.read_excel(file_path)
        df = df[df['소재지도로명주소'].str.contains("서울특별시", na=False)]
        df = df.dropna(subset=['WGS84위도', 'WGS84경도'])
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (b:EmergencyBell) REQUIRE b.id IS UNIQUE")
            session.run("CREATE POINT INDEX bell_location_index IF NOT EXISTS FOR (b:EmergencyBell) ON (b.location)")
            
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
            
            batch_size = 1000
            batch = []
            
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
                    batch = []
            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing Emergency Bells.")
        self._link_bell()

    def _link_bell(self):
        print("Linking Emergency Bells (300m)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (b:EmergencyBell)
                WHERE point.distance(p.location, b.location) < 300
                MERGE (p)-[r:NEAR_BELL]->(b)
                SET r.distance = point.distance(p.location, b.location),
                    r.walking_time = (point.distance(p.location, b.location) * 1.3) / 80
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def import_police(self):
        file_path = os.path.join(Config.DATA_DIR, "office", "경찰청_전국 지구대 파출소 주소 현황_20241231.csv")
        print(f"Loading Police data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
        df = df[df['주소'].str.contains("서울특별시", na=False)]
        
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
            
            for _, row in df.iterrows():
                address = str(row['주소'])
                lat, lon = Geocoder.get_coordinates(address)
                
                if lat is None or lon is None:
                    continue
                    
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
                    batch = []
                    time.sleep(0.1)
                    
            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing Police Stations.")
        self._link_police()

    def _link_police(self):
        print("Linking Police Stations (1km)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (pol:PoliceStation)
                WHERE point.distance(p.location, pol.location) < 1000
                MERGE (p)-[r:NEAR_POLICE]->(pol)
                SET r.distance = point.distance(p.location, pol.location),
                    r.walking_time = (point.distance(p.location, pol.location) * 1.3) / 80
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def import_fire(self):
        file_path = os.path.join(Config.DATA_DIR, "office", "소방청_시도 소방서 현황_20250701.csv")
        print(f"Loading Fire Station data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
        df = df[df['소방본부'].str.contains("서울", na=False)]
        
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
            
            for _, row in df.iterrows():
                address = str(row['주소'])
                lat, lon = Geocoder.get_coordinates(address)
                
                if lat is None or lon is None:
                    continue
                    
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
                    batch = []
                    time.sleep(0.1)
                    
            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing Fire Stations.")
        self._link_fire()

    def _link_fire(self):
        print("Linking Fire Stations (2.5km)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (f:FireStation)
                WHERE point.distance(p.location, f.location) < 2500
                MERGE (p)-[r:NEAR_FIRE]->(f)
                SET r.distance = point.distance(p.location, f.location),
                    r.walking_time = (point.distance(p.location, f.location) * 1.3) / 80
            } IN TRANSACTIONS OF 1000 ROWS
            """)

if __name__ == "__main__":
    importer = SafetyImporter()
    importer.import_cctv()
    importer.import_bell()
    importer.import_police()
    importer.import_fire()
    Database.close()
