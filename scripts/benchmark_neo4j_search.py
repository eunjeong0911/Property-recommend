
import os
import time
import sys
from neo4j import GraphDatabase

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def benchmark_search():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    print(f"Connecting to {uri} as {user}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Example Query from apps/rag/nodes/neo4j_search_node.py (University Search)
    query = """
    MATCH (anchor:College) 
    WHERE (anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
    
    MATCH (p:Property)-[r_anchor:NEAR_COLLEGE]->(anchor)
    
    OPTIONAL MATCH (p)-[r_sub:NEAR_SUBWAY]->(sub:SubwayStation)
    
    WITH p, anchor, r_anchor, sub, r_sub,
         (5000 - coalesce(toInteger(r_anchor.distance), 5000)) as total_score
    
    RETURN p.id as id, total_score,
           CASE WHEN sub IS NOT NULL 
                THEN [{name: sub.name, dist: coalesce(toInteger(r_sub.distance), 9999), time: coalesce(toInteger(r_sub.walking_time), 9999)}]
                ELSE [] 
           END as poi_details,
           [{name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)}] as edu_details
    ORDER BY total_score DESC LIMIT 300
    """
    
    # Common test keywords
    keywords = ["서울대", "연세대", "홍대", "홍익대학교"]
    
    print("\n--- Benchmarking Queries ---")
    
    with driver.session() as session:
        for keyword in keywords:
            start_time = time.time()
            # Run query (forcing it to consume results)
            result = session.run(query, keyword=keyword)
            records = list(result)
            end_time = time.time()
            
            duration = end_time - start_time
            print(f"Keyword: '{keyword}' - Found {len(records)} results in {duration:.4f} seconds.")

            # Explain the query to see hits
            explain_result = session.run("EXPLAIN " + query, keyword=keyword)
            # Just printing that we ran explain
            
    driver.close()

if __name__ == "__main__":
    benchmark_search()
