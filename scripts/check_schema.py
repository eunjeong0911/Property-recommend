import os
from langchain_community.graphs import Neo4jGraph
from dotenv import load_dotenv

load_dotenv()

def check_schema():
    url = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    print(f"Connecting to {url}...")
    
    try:
        graph = Neo4jGraph(
            url=url, 
            username=username, 
            password=password
        )
        
        print("Schema:")
        print(graph.schema)
        with open("schema.txt", "w", encoding="utf-8") as f:
            f.write(graph.schema)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
