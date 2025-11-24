#!/usr/bin/env python
"""
RDB 데이터를 Neo4j 그래프로 동기화
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from libs.db.postgres import get_connection
from libs.db.neo4j import get_driver

def sync_graph():
    print("Syncing graph database...")
    # TODO: Implement graph sync

if __name__ == "__main__":
    sync_graph()
