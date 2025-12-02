import sys
import os

# Add scripts/data_import to sys.path to find config and database modules
sys.path.append(os.path.join(os.getcwd(), 'scripts', 'data_import'))

from database import Database

def reset_database():
    print("Connecting to Neo4j...")
    driver = Database.get_driver()
    with driver.session() as session:
        print("Deleting all data from Neo4j...")
        # Delete all nodes and relationships
        session.run("MATCH (n) DETACH DELETE n")
        
        # Optional: Drop all constraints and indexes if you want a completely fresh start
        # But usually for data re-import, keeping schema is fine. 
        # The user just asked to delete "data that went in".
        
        print("All nodes and relationships have been deleted.")
    Database.close()

if __name__ == "__main__":
    reset_database()
