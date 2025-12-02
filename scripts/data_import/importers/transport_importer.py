import os
import pandas as pd
from config import Config
from database import Database

class TransportImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def import_subway(self):
        file_path = os.path.join(Config.DATA_DIR, "subway_station", "지하철_노선도.csv")
        print(f"Loading Subway data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949', on_bad_lines='skip')
            
        print(f"Found {len(df)} Subway Stations.")
        
        with self.driver.session() as session:
            # session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:SubwayStation) REQUIRE s.name IS UNIQUE")
            # 복합 키(이름 + 노선)로 유니크 제약 조건 설정 (같은 이름의 역이 다른 노선에 있을 수 있음)
            try:
                session.run("DROP CONSTRAINT ON (s:SubwayStation) ASSERT s.name IS UNIQUE")
            except Exception:
                pass # 제약 조건이 없으면 패스
            
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:SubwayStation) REQUIRE (s.name, s.line) IS UNIQUE")
            session.run("CREATE POINT INDEX subway_location_index IF NOT EXISTS FOR (s:SubwayStation) ON (s.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (s:SubwayStation {name: row.name, line: row.line})
            SET s.latitude = row.lat,
                s.longitude = row.lon,
                s.location = point({latitude: row.lat, longitude: row.lon})
            """
            
            batch_size = 500
            batch = []
            
            for _, row in df.iterrows():
                batch.append({
                    "name": str(row['역사명']),
                    "line": str(row['노선명']),
                    "lat": float(row['역위도']),
                    "lon": float(row['역경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []
                    
            if batch:
                session.run(query, batch=batch)
                
            print("Finished importing Subway Stations.")
            self._link_subway(session)

    def _link_subway(self, session):
        print("Linking Subway Stations (1km)...")
        query = """
        MATCH (p:Property)
        CALL {
            WITH p
            MATCH (s:SubwayStation)
            WHERE point.distance(p.location, s.location) < 1000
            MERGE (p)-[r:NEAR_SUBWAY]->(s)
            SET r.distance = point.distance(p.location, s.location),
                r.walking_time = (point.distance(p.location, s.location) * 1.3) / 80
        } IN TRANSACTIONS OF 1000 ROWS
        """
        session.run(query)
        print("Linking Subway completed.")

    def import_bus(self):
        # file_path = os.path.join(Config.DATA_DIR, "bus_station", "국토교통부_전국 버스정류장 위치정보_20241031_utf8_clean.csv")
        file_path = os.path.join(Config.DATA_DIR, "bus_station", "bus_data_fixed.csv")
        print(f"Loading Bus data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
        df = df[df['도시명'].str.contains("서울특별시", na=False)]
        print(f"Found {len(df)} Bus Stations in Seoul.")
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (b:BusStation) REQUIRE b.id IS UNIQUE")
            session.run("CREATE POINT INDEX bus_location_index IF NOT EXISTS FOR (b:BusStation) ON (b.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (b:BusStation {id: row.id})
            SET b.name = row.name,
                b.latitude = row.lat,
                b.longitude = row.lon,
                b.location = point({latitude: row.lat, longitude: row.lon})
            """
            
            batch_size = 1000
            batch = []
            
            for _, row in df.iterrows():
                batch.append({
                    "id": str(row['정류장번호']),
                    "name": str(row['정류장명']),
                    "lat": float(row['위도']),
                    "lon": float(row['경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []
                    
            if batch:
                session.run(query, batch=batch)
                
            print("Finished importing Bus Stations.")
            self._link_bus(session)

    def _link_bus(self, session):
        print("Linking Bus Stations (200m)...")
        query = """
        MATCH (p:Property)
        CALL {
            WITH p
            MATCH (b:BusStation)
            WHERE point.distance(p.location, b.location) < 200
            MERGE (p)-[r:NEAR_BUS]->(b)
            SET r.distance = point.distance(p.location, b.location),
                r.walking_time = (point.distance(p.location, b.location) * 1.3) / 80
        } IN TRANSACTIONS OF 1000 ROWS
        """
        session.run(query)
        print("Linking Bus completed.")

if __name__ == "__main__":
    importer = TransportImporter()
    importer.import_subway()
    importer.import_bus()
    Database.close()
