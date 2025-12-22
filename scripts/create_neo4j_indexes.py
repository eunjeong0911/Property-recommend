"""
Script to create TEXT indexes in Neo4j database.
Run this after Neo4j container starts to apply init.cypher indexes.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.graphs import Neo4jGraph


def create_indexes():
    """Create TEXT indexes in Neo4j."""
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password1234")
    )
    
    # TEXT INDEX creation queries from init.cypher
    indexes = [
        "CREATE TEXT INDEX subway_name_text IF NOT EXISTS FOR (s:SubwayStation) ON (s.name)",
        "CREATE TEXT INDEX college_name_text IF NOT EXISTS FOR (c:College) ON (c.name)",
        "CREATE TEXT INDEX hospital_name_text IF NOT EXISTS FOR (h:Hospital) ON (h.name)",
        "CREATE TEXT INDEX park_name_text IF NOT EXISTS FOR (p:Park) ON (p.name)",
        "CREATE TEXT INDEX general_hospital_name_text IF NOT EXISTS FOR (g:GeneralHospital) ON (g.name)",
    ]
    
    print("Creating TEXT indexes...")
    for idx_query in indexes:
        try:
            graph.query(idx_query)
            print(f"  OK: {idx_query.split('INDEX ')[1].split(' IF')[0]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Verify indexes
    print("\nVerifying indexes...")
    result = graph.query("SHOW INDEXES")
    text_indexes = [row for row in result if row.get("type") == "TEXT"]
    
    print(f"Found {len(text_indexes)} TEXT indexes:")
    for row in text_indexes:
        print(f"  - {row.get('name')}: {row.get('labelsOrTypes')}.{row.get('properties')}")
    
    return len(text_indexes) >= 4


if __name__ == "__main__":
    success = create_indexes()
    sys.exit(0 if success else 1)
