import os
import pandas as pd
from config import Config
from database import Database

class TransportImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def _get_existing_count(self, session, label):
        result = session.run(f"MATCH (n:{label}) RETURN count(n) as cnt")
        return result.single()["cnt"]

    def import_subway(self):
        with self.driver.session() as session:
            existing = self._get_existing_count(session, "SubwayStation")
            if existing > 0:
                print(f"  ⏭ Subway stations already exist ({existing}). Skipping import.")
                return
        
        file_path = os.path.join(Config.DATA_DIR, "subway_station", "지하철_노선도.csv")
        print(f"Loading Subway data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949', on_bad_lines='skip')
            
        total_rows = len(df)
        print(f"Found {total_rows} Subway Stations.")
        
        with self.driver.session() as session:
            try:
                session.run("DROP CONSTRAINT ON (s:SubwayStation) ASSERT s.name IS UNIQUE")
            except Exception:
                pass
            
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:SubwayStation) REQUIRE (s.name, s.line) IS UNIQUE")
            session.run("CREATE POINT INDEX subway_location_index IF NOT EXISTS FOR (s:SubwayStation) ON (s.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (s:SubwayStation {name: row.name, line: row.line})
            SET s.latitude = row.lat,
                s.longitude = row.lon,
                s.location = point({latitude: row.lat, longitude: row.lon})
            """
            
            batch_size = 300
            batch = []
            processed = 0
            
            for _, row in df.iterrows():
                batch.append({
                    "name": str(row['역사명']),
                    "line": str(row['노선명']),
                    "lat": float(row['역위도']),
                    "lon": float(row['역경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    processed += len(batch)
                    print(f"  Subway progress: {processed}/{total_rows} ({processed*100//total_rows}%)")
                    batch = []
                    
            if batch:
                session.run(query, batch=batch)
                processed += len(batch)
                print(f"  Subway progress: {processed}/{total_rows} (100%)")
                
            print("Finished importing Subway Stations.")
        self.link_subway()

    def link_subway(self):
        print("Linking Subway Stations (1.5km)...")
        with self.driver.session() as session:
            # Check if already linked
            result = session.run("MATCH ()-[r:NEAR_SUBWAY]->() RETURN count(r) as cnt")
            existing = result.single()["cnt"]
            if existing > 0:
                print(f"  ⏭ Subway links already exist ({existing}). Skipping.")
                return
            
            result = session.run("MATCH (p:Property) RETURN count(p) as cnt")
            total = result.single()["cnt"]
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
                    MATCH (s:SubwayStation)
                    WHERE point.distance(p.location, s.location) < 1500
                    MERGE (p)-[r:NEAR_SUBWAY]->(s)
                    SET r.distance = toInteger(round(point.distance(p.location, s.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, s.location) * 1.3) / 80))
                    RETURN count(r) as cnt
                """, offset=offset, limit=batch_size)
                linked_count += result.single()["cnt"]
                offset += batch_size
                progress = min(offset, total)
                print(f"  Subway linking: {progress}/{total} ({progress*100//total}%) - {linked_count} links")
                
            print(f"  Linking Subway completed. Total links: {linked_count}")

    def import_bus(self):
        with self.driver.session() as session:
            existing = self._get_existing_count(session, "BusStation")
            if existing > 0:
                print(f"  ⏭ Bus stations already exist ({existing}). Skipping import.")
                return
        
        file_path = os.path.join(Config.DATA_DIR, "bus_station", "bus_data_fixed.csv")
        print(f"Loading Bus data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
        df = df[df['도시명'].str.contains("서울특별시", na=False)]
        total_rows = len(df)
        print(f"Found {total_rows} Bus Stations in Seoul.")
        
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
            
            batch_size = 500
            batch = []
            processed = 0
            
            for _, row in df.iterrows():
                batch.append({
                    "id": str(row['정류장번호']),
                    "name": str(row['정류장명']),
                    "lat": float(row['위도']),
                    "lon": float(row['경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    processed += len(batch)
                    print(f"  Bus progress: {processed}/{total_rows} ({processed*100//total_rows}%)")
                    batch = []
                    
            if batch:
                session.run(query, batch=batch)
                processed += len(batch)
                print(f"  Bus progress: {processed}/{total_rows} (100%)")
                
            print("Finished importing Bus Stations.")
        self.link_bus()

    def link_bus(self):
        print("Linking Bus Stations (200m)...")
        with self.driver.session() as session:
            # Check if already linked
            result = session.run("MATCH ()-[r:NEAR_BUS]->() RETURN count(r) as cnt")
            existing = result.single()["cnt"]
            if existing > 0:
                print(f"  ⏭ Bus links already exist ({existing}). Skipping.")
                return
            
            result = session.run("MATCH (p:Property) RETURN count(p) as cnt")
            total = result.single()["cnt"]
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
                    MATCH (b:BusStation)
                    WHERE point.distance(p.location, b.location) < 200
                    MERGE (p)-[r:NEAR_BUS]->(b)
                    SET r.distance = toInteger(round(point.distance(p.location, b.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, b.location) * 1.3) / 80))
                    RETURN count(r) as cnt
                """, offset=offset, limit=batch_size)
                linked_count += result.single()["cnt"]
                offset += batch_size
                progress = min(offset, total)
                print(f"  Bus linking: {progress}/{total} ({progress*100//total}%) - {linked_count} links")
                
            print(f"  Linking Bus completed. Total links: {linked_count}")

if __name__ == "__main__":
    importer = TransportImporter()
    importer.import_subway()
    importer.import_bus()
    Database.close()
