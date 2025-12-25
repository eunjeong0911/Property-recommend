import os
import sys

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from database import Database

class ConvenienceScoreImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def import_convenience_score(self):
        """
        Calculate and import 'Convenience Temperature' (Max 100)
        
        Metric (Total 100):
        1. Retail (40 pts)
           - Convenience Store (20 pts): 
             - Max if < 50m. 0 if > 150m. Linear decay.
           - Laundry (20 pts):
             - Max if < 100m. 0 if > 250m. Linear decay.
             
        2. Shopping (40 pts)
           - Mart/Dept (40 pts):
             - Max if < 300m. 0 if > 1000m. Linear decay.
             
        3. Leisure (20 pts)
           - Park (20 pts) [Filtered >= 1500m2]:
             - Max if < 150m. 0 if > 500m. Linear decay.
        """
        print("Calculating Convenience Temperature...")
        
        with self.driver.session() as session:
            # Clear existing score
            session.run("""
            MATCH (p:Property)-[r:HAS_TEMPERATURE]->(m:Metric {name: 'LivingConvenience'})
            DELETE r
            """)
            
            # Use batch processing for properties
            # We calculate score per property
            
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                
                // 1. Retail: Convenience Store (Max 20)
                // Threshold: 50m (Max), 150m (Zero)
                OPTIONAL MATCH (p)-[r1:NEAR_CONVENIENCE]->(c:Convenience)
                WITH p, min(r1.distance) as dist_conv
                WITH p, dist_conv,
                     CASE 
                        WHEN dist_conv IS NULL THEN 0
                        WHEN dist_conv <= 50 THEN 20
                        WHEN dist_conv >= 150 THEN 0
                        ELSE 20 * (1 - (toFloat(dist_conv) - 50) / (150 - 50))
                     END as score_conv
                     
                // 2. Retail: Laundry (Max 20)
                // Threshold: 100m (Max), 250m (Zero)
                OPTIONAL MATCH (p)-[r2:NEAR_LAUNDRY]->(l:Laundry)
                WITH p, score_conv, min(r2.distance) as dist_laundry
                WITH p, score_conv, dist_laundry,
                     CASE 
                        WHEN dist_laundry IS NULL THEN 0
                        WHEN dist_laundry <= 100 THEN 20
                        WHEN dist_laundry >= 250 THEN 0
                        ELSE 20 * (1 - (toFloat(dist_laundry) - 100) / (250 - 100))
                     END as score_laundry

                // 3. Shopping: Mart (Max 40)
                // Threshold: 300m (Max), 1000m (Zero)
                OPTIONAL MATCH (p)-[r3:NEAR_LARGEMART]->(m:Mart)
                WITH p, score_conv, score_laundry, min(r3.distance) as dist_mart
                WITH p, score_conv, score_laundry, dist_mart,
                     CASE 
                        WHEN dist_mart IS NULL THEN 0
                        WHEN dist_mart <= 300 THEN 40
                        WHEN dist_mart >= 1000 THEN 0
                        ELSE 40 * (1 - (toFloat(dist_mart) - 300) / (1000 - 300))
                     END as score_mart

                // 4. Leisure: Park (Max 20)
                // Threshold: 150m (Max), 500m (Zero)
                // Note: Park nodes are already filtered by area >= 1500m2 during import
                OPTIONAL MATCH (p)-[r4:NEAR_PARK]->(pk:Park)
                WITH p, score_conv, score_laundry, score_mart, min(r4.distance) as dist_park
                WITH p, score_conv, score_laundry, score_mart, dist_park,
                     CASE 
                        WHEN dist_park IS NULL THEN 0
                        WHEN dist_park <= 150 THEN 20
                        WHEN dist_park >= 500 THEN 0
                        ELSE 20 * (1 - (toFloat(dist_park) - 150) / (500 - 150))
                     END as score_park

                // Total Score (Medical removed)
                WITH p, (score_conv + score_laundry + score_mart + score_park) as total_score
                
                MERGE (m:Metric {name: 'LivingConvenience'})
                MERGE (p)-[r:HAS_TEMPERATURE]->(m)
                SET r.temperature = round(total_score, 1),
                    r.updated_at = datetime()
            } IN TRANSACTIONS OF 1000 ROWS
            """)
            
        print("Finished calculating Convenience Temperature.")

if __name__ == "__main__":
    importer = ConvenienceScoreImporter()
    importer.import_convenience_score()
