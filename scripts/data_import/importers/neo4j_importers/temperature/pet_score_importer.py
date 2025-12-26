import os
import sys

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from database import Database

class PetScoreImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def import_pet_score(self):
        """
        Calculate and import 'Pet Temperature' (Max 100)
        
        Metric (Total 100 Cap):
        1. Animal Hospital: 20 pts (Essential)
        2. Pet Playground: 30 pts (Premium/Scarce)
        3. Pet Shop: 5 pts (Convenience)
        
        Logic:
        - Linear Distance Decay within 500m
        - Score = Weight * (1 - distance/500)
        - Final Score = Min(100, Sum)
        """
        print("Calculating Pet Temperature...")
        
        with self.driver.session() as session:
            # Clear existing score
            session.run("""
            MATCH (p:Property)-[r:HAS_TEMPERATURE]->(m:Metric {name: 'Pet'})
            DELETE r
            """)
            
            # Batch processing
            session.run("""
            MATCH (p:Property)
            CALL {
                WITH p
                
                // 1. Animal Hospital (20 pts)
                OPTIONAL MATCH (p)-[r1:NEAR_ANIMAL_HOSPITAL]->(h:AnimalHospital)
                WHERE r1.distance <= 500
                WITH p, 
                     CASE 
                        WHEN r1 IS NULL THEN 0 
                        ELSE 20 * (1 - r1.distance / 500.0) 
                     END as unit_h
                WITH p, sum(unit_h) as score_hospital
                
                // 2. Pet Playground (30 pts)
                OPTIONAL MATCH (p)-[r2:NEAR_PET_PLAYGROUND]->(pg:PetPlayground)
                WHERE r2.distance <= 500
                WITH p, score_hospital, 
                     CASE 
                        WHEN r2 IS NULL THEN 0 
                        ELSE 30 * (1 - r2.distance / 500.0) 
                     END as unit_pg
                WITH p, score_hospital, sum(unit_pg) as score_playground
                
                // 3. Pet Shop (5 pts)
                OPTIONAL MATCH (p)-[r3:NEAR_PET_SHOP]->(s:PetShop)
                WHERE r3.distance <= 500
                WITH p, score_hospital, score_playground,
                     CASE 
                        WHEN r3 IS NULL THEN 0 
                        ELSE 5 * (1 - r3.distance / 500.0) 
                     END as unit_s
                WITH p, score_hospital, score_playground, sum(unit_s) as score_shop
                
                WITH p, (score_hospital + score_playground + score_shop) as total_score
                
                MERGE (m:Metric {name: 'Pet'})
                MERGE (p)-[r:HAS_TEMPERATURE]->(m)
                SET r.temperature = round(CASE WHEN total_score > 100 THEN 100.0 ELSE total_score END, 1),
                    r.updated_at = datetime()
            } IN TRANSACTIONS OF 1000 ROWS
            """)
            
        print("Finished calculating Pet Temperature.")

if __name__ == "__main__":
    importer = PetScoreImporter()
    importer.import_pet_score()
