import sys
import os
import pandas as pd
import requests
import time
from pathlib import Path

# 프로젝트 루트 경로 추가 (config, database 임포트용)
# 현재 위치: scripts/data_import/importers/neo4j_importers/temperature/
# 상위로 3단계 이동해야 scripts/data_import/ 에 도달함
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from config import Config
from database import Database

class PetScoreImporter:
    def __init__(self):
        self.driver = Database.get_driver()
        self.base_dir = Path(Config.BASE_DIR)
        self.kakao_api_key = Config.KAKAO_API_KEY
        
    def get_coords(self, address):
        """카카오 API를 이용해 주소를 좌표로 변환"""
        if not address or not self.kakao_api_key:
            return None, None
            
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {self.kakao_api_key}"}
        params = {"query": address}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['documents']:
                    return float(data['documents'][0]['y']), float(data['documents'][0]['x'])
        except Exception as e:
            print(f"  [Error] Geocoding failed for {address}: {e}")
        return None, None

    def import_nodes(self):
        """반려동물 전용 시설(놀이터 등) 노드 생성"""
        print("Importing PetPlayground nodes...")
        playground_csv = self.base_dir / "data" / "GraphDB_data" / "pet" / "반려동물 놀이터.csv"
        
        if not playground_csv.exists():
            print(f"File not found: {playground_csv}")
            return

        try:
            df = pd.read_csv(playground_csv, encoding='utf-8')
        except:
            df = pd.read_csv(playground_csv, encoding='cp949')

        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:PetPlayground) REQUIRE p.id IS UNIQUE")
            
            query = """
            UNWIND $batch AS row
            MERGE (p:PetPlayground {id: row.id})
            SET p.name = row.name,
                p.latitude = toFloat(row.lat),
                p.longitude = toFloat(row.lon),
                p.location = point({latitude: toFloat(row.lat), longitude: toFloat(row.lon)})
            """
            
            batch = []
            for i, row in df.iterrows():
                # 주소 컬럼(위치)에서 좌표 추출
                lat, lon = None, None
                if '위도' in row and pd.notna(row['위도']):
                    lat, lon = row['위도'], row['경도']
                elif '위치' in row:
                    lat, lon = self.get_coords(row['위치'])
                    time.sleep(0.1) # Rate limit 방지
                
                if lat and lon:
                    batch.append({
                        "id": f"PG_{i}",
                        "name": row.get('공원명') or row.get('시설명'),
                        "lat": lat,
                        "lon": lon
                    })
                
                if len(batch) >= 100:
                    session.run(query, batch=batch)
                    batch = []
            if batch:
                session.run(query, batch=batch)
        print("Finished importing PetPlayground nodes.")

    def calculate_scores(self):
        """매물별 반려동물 온도 계산 및 저장"""
        print("Calculating Pet Temperature for all properties...")
        
        with self.driver.session() as session:
            # 기존 점수 삭제
            session.run("MATCH (p:Property)-[r:HAS_TEMPERATURE]->(m:Metric {name: 'Pet'}) DELETE r")

            query = """
            MATCH (p:Property)
            CALL {
                WITH p
                
                // A. 반려동물 놀이터 (1km)
                OPTIONAL MATCH (pg:PetPlayground)
                WHERE point.distance(p.location, pg.location) <= 1000
                WITH p, 
                     count(pg) as pg_cnt,
                     sum(CASE WHEN point.distance(p.location, pg.location) <= 500 THEN 2 ELSE 1 END) as pg_score_raw

                // B. 동물병원 (1km)
                OPTIONAL MATCH (h:Hospital)
                WHERE h.category = '동물병원' AND point.distance(p.location, h.location) <= 1000
                WITH p, pg_score_raw, pg_cnt,
                     count(h) as h_cnt,
                     sum(CASE WHEN point.distance(p.location, h.location) <= 500 THEN 2 ELSE 1 END) as h_score_raw

                // C. 애견 공원 (산책로, 800m)
                OPTIONAL MATCH (pk:Park)
                WHERE pk.공원면적_num >= 116 AND point.distance(p.location, pk.location) <= 800
                WITH p, pg_score_raw, pg_cnt, h_score_raw, h_cnt,
                     count(pk) as pk_cnt,
                     sum(CASE WHEN point.distance(p.location, pk.location) <= 400 THEN 1.5 ELSE 1 END) as pk_score_raw

                // D. 기타 시설 (Grooming, Cafe, Supplies - 상가 데이터에서 추출)
                OPTIONAL MATCH (s:Store)
                WHERE (s.category = '애완동물/애완용품 소매업' OR s.name CONTAINS '애견' OR s.name CONTAINS '펫' OR s.name CONTAINS '반려')
                      AND NOT (s.category CONTAINS '독서실' OR s.category CONTAINS '스터디' OR s.category CONTAINS '네일' OR s.category CONTAINS '피부')
                      AND point.distance(p.location, s.location) <= 700
                WITH p, pg_score_raw, pg_cnt, h_score_raw, h_cnt, pk_score_raw, pk_cnt,
                     sum(CASE WHEN s.name CONTAINS '카페' OR s.name CONTAINS '커피' THEN 1 ELSE 0 END) as cafe_cnt,
                     count(s) as s_all_cnt,
                     sum(CASE WHEN point.distance(p.location, s.location) <= 300 THEN 1.5 ELSE 1 END) as s_score_raw

                // 가중치 계산 (Max capping 적용하여 100점 만점 지수로 변환)
                WITH p, pg_cnt, h_cnt, pk_cnt, cafe_cnt, s_all_cnt,
                     (CASE WHEN pg_score_raw * 20 > 30 THEN 30.0 ELSE toFloat(pg_score_raw * 20) END +
                      CASE WHEN h_score_raw * 10 > 25 THEN 25.0 ELSE toFloat(h_score_raw * 10) END +
                      CASE WHEN pk_score_raw * 5 > 15 THEN 15.0 ELSE toFloat(pk_score_raw * 5) END +
                      CASE WHEN s_score_raw * 5 > 30 THEN 30.0 ELSE toFloat(s_score_raw * 5) END) as raw_score
                
                // 30~43°C 스케일 변환
                WITH p, pg_cnt, h_cnt, pk_cnt, cafe_cnt, s_all_cnt, (30.0 + (13.0 * (raw_score / 100.0))) as pet_temp
                
                MERGE (m:Metric {name: 'Pet'})
                MERGE (p)-[r:HAS_TEMPERATURE]->(m)
                SET r.temperature = round(pet_temp * 10) / 10.0,
                    r.playground_count = pg_cnt,
                    r.hospital_count = h_cnt,
                    r.park_count = pk_cnt,
                    r.cafe_count = cafe_cnt,
                    r.etc_count = s_all_cnt - cafe_cnt,
                    r.updated_at = datetime()
            } IN TRANSACTIONS OF 1000 ROWS
            """
            session.run(query)
        print("Pet Temperature calculation completed.")

if __name__ == "__main__":
    importer = PetScoreImporter()
    importer.import_nodes()
    importer.calculate_scores()
    Database.close()
