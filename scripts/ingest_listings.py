#!/usr/bin/env python
"""
매물 데이터 수집 및 RDB 저장 스크립트
"""
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from libs.db.postgres import get_connection

def ingest_listings():
    data_dir = Path(__file__).parent.parent / "data" / "landData"
    
    conn = get_connection()
    cur = conn.cursor()
    
    for json_file in data_dir.glob("*.json"):
        print(f"Processing {json_file.name}...")
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # TODO: Insert data into database
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    ingest_listings()
