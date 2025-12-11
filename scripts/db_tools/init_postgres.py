import os
import sys
import psycopg2

# Add data_import directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_import"))

from config import Config

def init_db():
    print("Initializing PostgreSQL database...")
    
    # Connect to DB
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Read init.sql
    init_sql_path = os.path.join(Config.BASE_DIR, "infra", "postgres", "init.sql")
    print(f"Reading schema from {init_sql_path}")
    
    with open(init_sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
        
    # Execute SQL
    try:
        # Drop existing tables to ensure fresh schema
        print("Dropping existing tables...")
        cur.execute("DROP TABLE IF EXISTS listing_embeddings CASCADE;")
        cur.execute("DROP TABLE IF EXISTS listings CASCADE;")
        
        print("Applying new schema...")
        cur.execute(sql)
        print("Schema initialized successfully.")
    except Exception as e:
        print(f"Error initializing schema: {e}")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_db()
