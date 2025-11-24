#!/usr/bin/env python
"""
RDB 매물 데이터를 청크로 나누고 pgvector에 임베딩 저장
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from libs.db.postgres import get_connection

def build_embeddings():
    print("Building embeddings...")
    # TODO: Implement embedding generation

if __name__ == "__main__":
    build_embeddings()
