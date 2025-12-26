import os
import pandas as pd
from config import Config
from database import Database

class AnimalImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def import_pet_places(self):
        file_path = os.path.join(Config.DATA_DIR, "animal", "animal_places.csv")
        print(f"Loading Animal Places from {file_path}...")
        
        if not os.path.exists(file_path):
             print(f"Warning: File not found {file_path}. Skipping Animal Import.")
             return

        df = pd.read_csv(file_path)
        # Ensure we have coordinates
        df = df.dropna(subset=['위도', '경도'])

        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:PetPlayground) REQUIRE p.id IS UNIQUE")
            session.run("CREATE POINT INDEX pet_playground_location_index IF NOT EXISTS FOR (p:PetPlayground) ON (p.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (p:PetPlayground {id: row.id})
            SET p.name = row.name,
                p.address = row.address,
                p.latitude = row.lat,
                p.longitude = row.lon,
                p.location = point({latitude: row.lat, longitude: row.lon})
            """
            
            batch_size = 1000
            batch = []
            
            for _, row in df.iterrows():
                # Composite ID: Name + Lat + Lon
                uid = f"{row['공원명']}_{row['위도']}_{row['경도']}"
                
                batch.append({
                    "id": uid,
                    "name": str(row['공원명']),
                    "address": str(row['위치']),
                    "lat": float(row['위도']),
                    "lon": float(row['경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []
            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing Pet Playgrounds.")
        self.link_pet_places()

    def link_pet_places(self):
        print("Linking Pet Playgrounds (1km)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (pp:PetPlayground)
                WHERE point.distance(p.location, pp.location) < 1000
                MERGE (p)-[r:NEAR_PET_PLAYGROUND]->(pp)
                SET r.distance = toInteger(round(point.distance(p.location, pp.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, pp.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def import_pet_stores(self):
        file_path = os.path.join(Config.DATA_DIR, "store_data", "소상공인시장진흥공단_상가(상권)정보_서울_cleaned.csv")
        print(f"Loading Animal Stores from {file_path}...")

        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
        target_categories = ['동물병원', '애완동물/애완용품 소매업']
        df = df[df['상권업종소분류명'].isin(target_categories)]

        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:AnimalHospital) REQUIRE a.id IS UNIQUE")
            session.run("CREATE POINT INDEX animal_hospital_location_index IF NOT EXISTS FOR (a:AnimalHospital) ON (a.location)")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (ps:PetShop) REQUIRE ps.id IS UNIQUE")
            session.run("CREATE POINT INDEX pet_shop_location_index IF NOT EXISTS FOR (ps:PetShop) ON (ps.location)")

            query = """
            UNWIND $batch AS row
            MERGE (s:Store {id: row.id})
            SET s.name = row.name,
                s.category = row.category,
                s.latitude = row.lat,
                s.longitude = row.lon,
                s.location = point({latitude: row.lat, longitude: row.lon})
            WITH s, row
            
            CALL {
                WITH s, row
                WITH s, row
                WHERE row.category = '동물병원'
                SET s:AnimalHospital
            }
            CALL {
                WITH s, row
                WITH s, row
                WHERE row.category = '애완동물/애완용품 소매업'
                SET s:PetShop
            }
            """
            
            batch_size = 2000
            batch = []
            
            for _, row in df.iterrows():
                batch.append({
                    "id": str(row['상가업소번호']),
                    "name": str(row['상호명']),
                    "category": str(row['상권업종소분류명']),
                    "lat": float(row['위도']),
                    "lon": float(row['경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []
            if batch:
                session.run(query, batch=batch)
        
        print("Finished importing Animal Stores (Hospital, PetShop).")
        self.link_pet_stores()

    def link_pet_stores(self):
        print("Linking Animal Stores (500m)...")
        with self.driver.session() as session:
            # Animal Hospital
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (ah:AnimalHospital)
                WHERE point.distance(p.location, ah.location) < 500
                MERGE (p)-[r:NEAR_ANIMAL_HOSPITAL]->(ah)
                SET r.distance = toInteger(round(point.distance(p.location, ah.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, ah.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)
            
            # Pet Shop
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (ps:PetShop)
                WHERE point.distance(p.location, ps.location) < 500
                MERGE (p)-[r:NEAR_PET_SHOP]->(ps)
                SET r.distance = toInteger(round(point.distance(p.location, ps.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, ps.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)
