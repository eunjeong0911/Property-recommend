import os
import sys

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from database import Database

class TrafficScoreImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def import_traffic_score(self):
        """
        Calculate and import 'Traffic Temperature' (Max 100)
        
        Metric (Total 100):
        1. Subway (60 pts)
           - Max if < 300m. 0 if > 800m. Linear decay.
           
        2. Bus (40 pts)
           - Count stops within 300m.
           - 3 pts per stop. Max 40 pts.
        """
        print("Calculating Traffic Temperature...")
        
        with self.driver.session() as session:
            # Clear existing score
            session.run("""
            MATCH (p:Property)-[r:HAS_TEMPERATURE]->(m:Metric {name: 'Traffic'})
            DELETE r
            """)
            
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                
                // 1. Subway (Max 60)
                OPTIONAL MATCH (p)-[r1:NEAR_SUBWAY]->(s:SubwayStation)
                
                // Use closest station
                WITH p, min(r1.distance) as dist_subway
                WITH p, dist_subway,
                     CASE 
                        WHEN dist_subway IS NULL THEN 0
                        WHEN dist_subway <= 300 THEN 60
                        WHEN dist_subway >= 800 THEN 0
                        ELSE 60 * (1 - (toFloat(dist_subway) - 300) / (800 - 300))
                     END as score_subway
                     
                // 2. Bus (Max 40)
                // Count bus stops within 300m
                OPTIONAL MATCH (p)-[r2:NEAR_BUS]->(b:BusStation)
                WHERE r2.distance <= 300
                WITH p, score_subway, count(b) as bus_count
                WITH p, score_subway, bus_count,
                     CASE 
                        WHEN bus_count * 3 > 40 THEN 40
                        ELSE bus_count * 3
                     END as score_bus
                     
                // Total Score
                WITH p, (score_subway + score_bus) as total_score
                
                MERGE (m:Metric {name: 'Traffic'})
                MERGE (p)-[r:HAS_TEMPERATURE]->(m)
                SET r.temperature = round(total_score, 1),
                    r.updated_at = datetime()
            } IN TRANSACTIONS OF 1000 ROWS
            """)
            
        print("Finished calculating Traffic Temperature.")

if __name__ == "__main__":
    importer = TrafficScoreImporter()
    importer.import_traffic_score()
