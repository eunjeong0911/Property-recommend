import os
import sys

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from database import Database

class CultureScoreImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def import_culture_score(self):
        """
        Calculate and import 'Culture Temperature' (Max 100)
        
        Metric (Total 100):
        1. Entertainment (Max 40 pts)
           - Cinema (20 pts each)
             - Cap at 40 (2 cinemas)
             
        2. Arts & Performance (Max 40 pts)
           - Art Museum (20 pts each)
           - Performance Hall (15 pts each)
             - Sum count * points, Cap at 40
             
        3. History & Education (Max 20 pts)
           - Museum/Memorial (10 pts each)
           - Library (5 pts each)
           - Other/Culture Center (5 pts each)
             - Sum count * points, Cap at 20
        """
        print("Calculating Culture Temperature...")
        
        with self.driver.session() as session:
            # Clear existing score
            session.run("""
            MATCH (p:Property)-[r:HAS_TEMPERATURE]->(m:Metric {name: 'Culture'})
            DELETE r
            """)
            
            # Step 1: Calculate and store Raw Score (0-100)
            print("  Step 1: Calculating Raw Scores...")
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                
                // 1. Entertainment: Cinema (Weight 30, Max 60)
                OPTIONAL MATCH (p)-[r1:NEAR_CULTURE]->(c1:Culture)
                WHERE c1.category = '영화관' AND r1.distance <= 500
                WITH p, r1
                WITH p, 
                     CASE 
                        WHEN r1 IS NULL THEN 0 
                        ELSE 30 * (1 - r1.distance / 500.0) 
                     END as unit_score
                WITH p, sum(unit_score) as raw_cinema
                
                // 2. Arts: Art Museum (30), Performance (25) (Max 60)
                OPTIONAL MATCH (p)-[r2:NEAR_CULTURE]->(c2:Culture)
                WHERE c2.category IN ['미술관', '공연장'] AND r2.distance <= 500
                WITH p, raw_cinema, c2, r2
                WITH p, raw_cinema,
                     CASE 
                        WHEN c2 IS NULL THEN 0
                        WHEN c2.category = '미술관' THEN 30 * (1 - r2.distance / 500.0)
                        ELSE 25 * (1 - r2.distance / 500.0)
                     END as unit_arts
                WITH p, raw_cinema, sum(unit_arts) as raw_arts

                // 3. History/Edu: Museum (15), Library/Other (10) (Max 30)
                OPTIONAL MATCH (p)-[r3:NEAR_CULTURE]->(c3:Culture)
                WHERE c3.category IN ['박물관/기념관', '도서관', '기타', '문화원'] AND r3.distance <= 500
                WITH p, raw_cinema, raw_arts, c3, r3
                WITH p, raw_cinema, raw_arts,
                     CASE 
                        WHEN c3 IS NULL THEN 0
                        WHEN c3.category = '박물관/기념관' THEN 15 * (1 - r3.distance / 500.0)
                        ELSE 10 * (1 - r3.distance / 500.0)
                     END as unit_edu
                WITH p, raw_cinema, raw_arts, sum(unit_edu) as raw_edu
                
                // 4. Park (Max 20) - 공원 추가
                OPTIONAL MATCH (p)-[r4:NEAR_PARK]->(pk:Park)
                WITH p, raw_cinema, raw_arts, raw_edu, min(r4.distance) as dist_park
                WITH p, raw_cinema, raw_arts, raw_edu,
                     CASE 
                        WHEN dist_park IS NULL THEN 0
                        WHEN dist_park <= 150 THEN 20
                        WHEN dist_park >= 500 THEN 0
                        ELSE 20 * (1 - (toFloat(dist_park) - 150) / (500 - 150))
                     END as raw_park
                     
                WITH p, 
                     CASE WHEN raw_cinema > 60 THEN 60.0 ELSE raw_cinema END as score_ent,
                     CASE WHEN raw_arts > 60 THEN 60.0 ELSE raw_arts END as score_arts,
                     CASE WHEN raw_edu > 30 THEN 30.0 ELSE raw_edu END as score_edu,
                     raw_park as score_park
                
                // Total: 문화(150 cap) + 공원(20) = 170점 만점 → 100점 스케일
                WITH p, (score_ent + score_arts + score_edu + score_park) * (100.0/170.0) as raw_total
                
                WITH p, CASE WHEN raw_total > 100 THEN 100.0 ELSE raw_total END as capped_total
                
                // raw_score와 temperature를 한 번에 계산 (평균 50 기준)
                WITH p, capped_total,
                     CASE 
                        WHEN capped_total <= 50 THEN capped_total * (36.5 / 50.0)
                        ELSE 36.5 + (capped_total - 50) * (63.5 / 50.0)
                     END as culture_temp
                
                MERGE (m:Metric {name: 'Culture'})
                MERGE (p)-[r:HAS_TEMPERATURE]->(m)
                SET r.temperature = round(CASE WHEN culture_temp > 100 THEN 100.0 WHEN culture_temp < 0 THEN 0.0 ELSE culture_temp END, 1),
                    r.raw_score = capped_total,
                    r.updated_at = datetime()
            } IN TRANSACTIONS OF 1000 ROWS
            """)
            
        print("Finished calculating Culture Temperature.")

if __name__ == "__main__":
    importer = CultureScoreImporter()
    importer.import_culture_score()
