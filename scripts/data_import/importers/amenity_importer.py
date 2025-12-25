import os
import pandas as pd
import glob
from config import Config
from database import Database

class AmenityImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def import_medical(self):
        print("Importing Medical Data...")
        # Hospital
        hospital_file = os.path.join(Config.DATA_DIR, "medical", "1.병원정보서비스(2025.9).xlsx")
        self._import_hospital(hospital_file)
        # Pharmacy
        pharmacy_file = os.path.join(Config.DATA_DIR, "medical", "2. 약국정보서비스(2025.9).xlsx")
        self._import_pharmacy(pharmacy_file)

    def _import_hospital(self, file_path):
        print(f"Loading Hospital data from {file_path}...")
        df = pd.read_excel(file_path)
        # df = df[df['도로명전체주소'].str.contains("서울특별시", na=False)]
        df = df[df['주소'].str.contains("서울특별시", na=False)]
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (h:Hospital) REQUIRE h.id IS UNIQUE")
            session.run("CREATE POINT INDEX hospital_location_index IF NOT EXISTS FOR (h:Hospital) ON (h.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (h:Hospital {id: row.id})
            SET h.name = row.name,
                h.category = row.category,
                h.latitude = row.lat,
                h.longitude = row.lon,
                h.location = point({latitude: row.lat, longitude: row.lon})
            WITH h
            CALL {
                WITH h
                WITH h
                WHERE h.category = '종합병원'
                SET h:GeneralHospital
            }
            """
            
            batch_size = 1000
            batch = []
            
            for _, row in df.iterrows():
                batch.append({
                    "id": str(row['암호화요양기호']),
                    "name": str(row['요양기관명']),
                    "category": str(row['종별코드명']),
                    "lat": float(row['좌표(Y)']),
                    "lon": float(row['좌표(X)'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []
            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing Hospitals.")
        self.link_hospital()

    def link_hospital(self):
        print("Linking Hospitals...")
        with self.driver.session() as session:
            # General Hospital (1km)
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (h:GeneralHospital)
                WHERE point.distance(p.location, h.location) < 1000
                MERGE (p)-[r:NEAR_GENERAL_HOSPITAL]->(h)
                SET r.distance = toInteger(round(point.distance(p.location, h.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, h.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)
            # Other Hospital (300m)
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (h:Hospital)
                WHERE h.category <> '종합병원' AND point.distance(p.location, h.location) < 300
                MERGE (p)-[r:NEAR_HOSPITAL]->(h)
                SET r.distance = toInteger(round(point.distance(p.location, h.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, h.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def _import_pharmacy(self, file_path):
        print(f"Loading Pharmacy data from {file_path}...")
        df = pd.read_excel(file_path)
        # df = df[df['도로명전체주소'].str.contains("서울특별시", na=False)]
        df = df[df['주소'].str.contains("서울특별시", na=False)]
        df = df.dropna(subset=['좌표(X)', '좌표(Y)'])
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Pharmacy) REQUIRE p.id IS UNIQUE")
            session.run("CREATE POINT INDEX pharmacy_location_index IF NOT EXISTS FOR (p:Pharmacy) ON (p.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (p:Pharmacy {id: row.id})
            SET p.name = row.name,
                p.latitude = row.lat,
                p.longitude = row.lon,
                p.location = point({latitude: row.lat, longitude: row.lon})
            """
            
            batch_size = 1000
            batch = []
            
            for _, row in df.iterrows():
                batch.append({
                    "id": str(row['암호화요양기호']),
                    "name": str(row['요양기관명']),
                    "lat": float(row['좌표(Y)']),
                    "lon": float(row['좌표(X)'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []
            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing Pharmacies.")
        self.link_pharmacy()

    def link_pharmacy(self):
        print("Linking Pharmacies (200m)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (ph:Pharmacy)
                WHERE point.distance(p.location, ph.location) < 200
                MERGE (p)-[r:NEAR_PHARMACY]->(ph)
                SET r.distance = toInteger(round(point.distance(p.location, ph.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, ph.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def import_college(self):
        file_path = os.path.join(Config.DATA_DIR, "college", "교육부_대학교 주소기반 좌표정보_20241030.csv")
        print(f"Loading College data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
        df = df[df['학교구분'] != '대학원']
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:College) REQUIRE c.id IS UNIQUE")
            session.run("CREATE POINT INDEX college_location_index IF NOT EXISTS FOR (c:College) ON (c.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (c:College {id: row.id})
            SET c.name = row.name,
                c.type = row.type,
                c.latitude = row.lat,
                c.longitude = row.lon,
                c.location = point({latitude: row.lat, longitude: row.lon})
            """
            
            batch_size = 500
            batch = []
            
            for _, row in df.iterrows():
                batch.append({
                    "id": str(row['학교코드']),
                    "name": str(row['학교명']),
                    "type": str(row['학교구분']),
                    "lat": float(row['위도']),
                    "lon": float(row['경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []
            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing Colleges.")
        self.link_college()

    def link_college(self):
        print("Linking Colleges (2km)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (c:College)
                WHERE point.distance(p.location, c.location) < 2000
                MERGE (p)-[r:NEAR_COLLEGE]->(c)
                SET r.distance = toInteger(round(point.distance(p.location, c.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, c.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def import_large_store(self):
        file_path = os.path.join(Config.DATA_DIR, "store_data", "서울시 대규모점포 인허가 정보.csv")
        print(f"Loading Large Store data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding='cp949')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='euc-kr')

        # Filter categories
        target_categories = ['대형마트', '백화점', '쇼핑센터', '복합쇼핑몰', '구분없음']
        df = df[df['업태구분명'].isin(target_categories)]  
        df = df.dropna(subset=['위도', '경도'])

        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Mart) REQUIRE m.id IS UNIQUE")
            session.run("CREATE POINT INDEX mart_location_index IF NOT EXISTS FOR (m:Mart) ON (m.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (m:Mart {id: row.id})
            SET m.name = row.name,
                m.category = row.category,
                m.latitude = row.lat,
                m.longitude = row.lon,
                m.location = point({latitude: row.lat, longitude: row.lon})
            SET m:LargeStore
            """
            
            batch_size = 1000
            batch = []
            
            for _, row in df.iterrows():
                # Use composite ID as no unique ID guaranteed: Name + Lat + Lon
                uid = f"{row['사업장명']}_{row['위도']}_{row['경도']}"
                
                batch.append({
                    "id": uid,
                    "name": str(row['사업장명']),
                    "category": str(row['업태구분명']),
                    "lat": float(row['위도']),
                    "lon": float(row['경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []
            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing Large Stores.")
        self.link_large_mart()

    def link_large_mart(self):
        print("Linking Large Marts (500m)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (m:Mart)
                WHERE point.distance(p.location, m.location) < 500
                MERGE (p)-[r:NEAR_LARGEMART]->(m)
                SET r.distance = toInteger(round(point.distance(p.location, m.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, m.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def import_store(self):
        file_path = os.path.join(Config.DATA_DIR, "store_data", "소상공인시장진흥공단_상가(상권)정보_서울_cleaned.csv")
        print(f"Loading Store data from {file_path}...")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
        # Refined Logic:
        # Import only '세탁소' (Laundry) and '편의점' (Convenience)
        # Exclude Cafe/Coffee/Mart(Small) based on user instruction
        
        target_categories = ['세탁소', '편의점']
        df = df[df['상권업종소분류명'].isin(target_categories)]
        
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Store) REQUIRE s.id IS UNIQUE")
            session.run("CREATE POINT INDEX store_location_index IF NOT EXISTS FOR (s:Store) ON (s.location)")
            
            # Additional Indices
            session.run("CREATE INDEX store_laundry_index IF NOT EXISTS FOR (s:Laundry) ON (s.id)")
            session.run("CREATE INDEX store_convenience_index IF NOT EXISTS FOR (s:Convenience) ON (s.id)")
            
            query = """
            UNWIND $batch AS row
            MERGE (s:Store {id: row.id})
            SET s.name = row.name,
                s.category = row.category,
                s.latitude = row.lat,
                s.longitude = row.lon,
                s.location = point({latitude: row.lat, longitude: row.lon})
            WITH s, row
            
            // Apply Labels conditionally
            CALL {
                WITH s, row
                WITH s, row
                WHERE row.category = '편의점'
                SET s:Convenience
            }
            CALL {
                WITH s, row
                WITH s, row
                WHERE row.category = '세탁소'
                SET s:Laundry
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
                
        print("Finished importing Stores (Laundry, Convenience).")
        self.link_convenience()
        self.link_laundry()

    def link_convenience(self):
        print("Linking Convenience Stores (200m)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (c:Convenience)
                WHERE point.distance(p.location, c.location) < 200
                MERGE (p)-[r:NEAR_CONVENIENCE]->(c)
                SET r.distance = toInteger(round(point.distance(p.location, c.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, c.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def link_laundry(self):
        print("Linking Laundries (200m)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (l:Laundry)
                WHERE point.distance(p.location, l.location) < 200
                MERGE (p)-[r:NEAR_LAUNDRY]->(l)
                SET r.distance = toInteger(round(point.distance(p.location, l.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, l.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def import_park(self):
        park_dir = os.path.join(Config.DATA_DIR, "park")
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
            
            for file_path in files:
                try:
                    df = pd.read_csv(file_path, encoding='cp949')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='utf-8')
                    
                batch_size = 500
                batch = []
                
                for _, row in df.iterrows():
                    if pd.isna(row['위도']) or pd.isna(row['경도']):
                        continue
                    
                    # Area Handling (Filter < 1500m2)
                    raw_area = str(row['공원면적'])
                    try:
                         # Remove likely non-numeric chars if any, though usually just numeric or empty
                         # If it contains comma, remove it
                        area_val = float(raw_area.replace(',', ''))
                    except ValueError:
                        area_val = 0.0

                    if area_val < 1500:
                        continue

                    batch.append({
                        "id": str(row['관리번호']),
                        "name": str(row['공원명']),
                        "type": str(row['공원구분']),
                        "area": area_val,
                        "lat": float(row['위도']),
                        "lon": float(row['경도'])
                    })
                    
                    if len(batch) >= batch_size:
                        session.run(query, batch=batch)
                        batch = []
                if batch:
                    session.run(query, batch=batch)
                    
        print("Finished importing Parks.")
        self.link_park()

    def link_park(self):
        print("Linking Parks (500m)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (pk:Park)
                WHERE point.distance(p.location, pk.location) < 500
                MERGE (p)-[r:NEAR_PARK]->(pk)
                SET r.distance = toInteger(round(point.distance(p.location, pk.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, pk.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)

    def import_culture(self):
        print("Importing Culture Facilities...")
        
        # 1. 서울시 문화공간 정보
        file_path1 = os.path.join(Config.DATA_DIR, "culture", "서울시 문화공간 정보.csv")
        print(f"Loading Culture data from {file_path1}...")
        try:
            df1 = pd.read_csv(file_path1, encoding='utf-8')
        except UnicodeDecodeError:
            df1 = pd.read_csv(file_path1, encoding='euc-kr')
            
        # 2. 서울시 영화상영관 인허가 정보
        file_path2 = os.path.join(Config.DATA_DIR, "culture", "서울시 영화상영관 인허가 정보.csv")
        print(f"Loading Cinema data from {file_path2}...")
        try:
            df2 = pd.read_csv(file_path2, encoding='utf-8')
        except UnicodeDecodeError:
            df2 = pd.read_csv(file_path2, encoding='euc-kr')

        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Culture) REQUIRE c.id IS UNIQUE")
            session.run("CREATE POINT INDEX culture_location_index IF NOT EXISTS FOR (c:Culture) ON (c.location)")
            
            query = """
            UNWIND $batch AS row
            MERGE (c:Culture {id: row.id})
            SET c.name = row.name,
                c.category = row.category,
                c.latitude = row.lat,
                c.longitude = row.lon,
                c.location = point({latitude: row.lat, longitude: row.lon})
            """
            
            batch_size = 1000
            batch = []
            
            # Process Culture Space
            # Cols: 주제분류, 문화시설명, 위도, 경도
            for _, row in df1.iterrows():
                if pd.isna(row['위도']) or pd.isna(row['경도']):
                    continue
                
                # Composite ID: Name + Lat + Lon
                uid = f"{row['문화시설명']}_{row['위도']}_{row['경도']}"
                
                batch.append({
                    "id": uid,
                    "name": str(row['문화시설명']),
                    "category": str(row['주제분류']),
                    "lat": float(row['위도']),
                    "lon": float(row['경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []

            # Process Cinema
            # Cols: 사업장명, 위도, 경도
            for _, row in df2.iterrows():
                if pd.isna(row['위도']) or pd.isna(row['경도']):
                    continue
                    
                uid = f"{row['사업장명']}_{row['위도']}_{row['경도']}"
                
                batch.append({
                    "id": uid,
                    "name": str(row['사업장명']),
                    "category": '영화관',
                    "lat": float(row['위도']),
                    "lon": float(row['경도'])
                })
                
                if len(batch) >= batch_size:
                    session.run(query, batch=batch)
                    batch = []

            if batch:
                session.run(query, batch=batch)
                
        print("Finished importing Culture Facilities.")
        self.link_culture()

    def link_culture(self):
        print("Linking Culture Facilities (500m)...")
        with self.driver.session() as session:
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                MATCH (c:Culture)
                WHERE point.distance(p.location, c.location) < 500
                MERGE (p)-[r:NEAR_CULTURE]->(c)
                SET r.distance = toInteger(round(point.distance(p.location, c.location))),
                    r.walking_time = toInteger(round((point.distance(p.location, c.location) * 1.3) / 80))
            } IN TRANSACTIONS OF 1000 ROWS
            """)

if __name__ == "__main__":
    importer = AmenityImporter()
    importer.import_medical()
    importer.import_college()
    importer.import_large_store()
    importer.import_store()
    importer.import_culture() # Added
    importer.import_park()
    Database.close()
