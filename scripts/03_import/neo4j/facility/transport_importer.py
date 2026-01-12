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
            # 연결되지 않은 매물 개수 확인
            result = session.run("MATCH (p:Property) WHERE NOT (p)-[:NEAR_SUBWAY]->() RETURN count(p) as cnt")
            unlinked_total = result.single()["cnt"]
            
            if unlinked_total == 0:
                print("  ⏭ All properties are already linked to Subway. Skipping.")
                return
            
            print(f"  Properties to link: {unlinked_total}")
            
            batch_size = 500
            offset = 0
            linked_count = 0
            
            # 반복문: 남은 미연결 매물이 없을 때까지
            # 주의: LIMIT으로 끊어서 처리하되, WHERE 조건이 있으므로 offset을 쓸 필요 없이 배치를 반복하면 됨
            # 하지만 안전하게 '처리된 수'를 추적
            
            while True:
                # 연결이 없는 매물 $limit개를 가져와서 연결 생성
                # offset을 쓰면 안됨 (처리되면 조건에서 빠지므로)
                result = session.run("""
                    MATCH (p:Property)
                    WHERE NOT (p)-[:NEAR_SUBWAY]->()
                    WITH p LIMIT $limit
                    MATCH (s:SubwayStation)
                    WHERE point.distance(p.location, s.location) < 1500
                    MERGE (p)-[r:NEAR_SUBWAY]->(s)
                    SET r.distance = toInteger(round(point.distance(p.location, s.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, s.location) * 1.3) / 80))
                    RETURN count(p) as processed_node_cnt, count(r) as created_rel_cnt
                """, limit=batch_size)
                
                record = result.single()
                processed_nodes = record["processed_node_cnt"]
                created_rels = record["created_rel_cnt"]
                
                if processed_nodes == 0:
                    break
                    
                linked_count += created_rels
                offset += processed_nodes
                print(f"  Subway linking progress: {offset}/{unlinked_total} (approx) - {created_rels} new links")

            print(f"  Linking Subway completed. Total new links: {linked_count}")

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
            # 연결되지 않은 매물 개수 확인
            result = session.run("MATCH (p:Property) WHERE NOT (p)-[:NEAR_BUS]->() RETURN count(p) as cnt")
            unlinked_total = result.single()["cnt"]
            
            if unlinked_total == 0:
                 print("  ⏭ All properties are already linked to Bus. Skipping.")
                 return
            
            print(f"  Properties to link: {unlinked_total}")
            
            batch_size = 500
            offset = 0
            linked_count = 0
            
            while True:
                result = session.run("""
                    MATCH (p:Property)
                    WHERE NOT (p)-[:NEAR_BUS]->()
                    WITH p LIMIT $limit
                    MATCH (b:BusStation)
                    WHERE point.distance(p.location, b.location) < 200
                    MERGE (p)-[r:NEAR_BUS]->(b)
                    SET r.distance = toInteger(round(point.distance(p.location, b.location))),
                        r.walking_time = toInteger(round((point.distance(p.location, b.location) * 1.3) / 80))
                    RETURN count(p) as processed_node_cnt, count(r) as created_rel_cnt
                """, limit=batch_size)
                
                record = result.single()
                processed_nodes = record["processed_node_cnt"]
                created_rels = record["created_rel_cnt"]
                
                if processed_nodes == 0:
                    break
                    
                linked_count += created_rels
                offset += processed_nodes
                print(f"  Bus linking progress: {offset}/{unlinked_total} (approx) - {created_rels} new links")
                
            print(f"  Linking Bus completed. Total new links: {linked_count}")

if __name__ == "__main__":
    importer = TransportImporter()
    importer.import_subway()
    importer.import_bus()
    Database.close()
