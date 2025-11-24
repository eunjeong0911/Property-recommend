#!/usr/bin/env python
"""
로그 재적재 스크립트
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

def backfill_logs():
    print("Backfilling logs...")
    # TODO: Implement log backfill

if __name__ == "__main__":
    backfill_logs()
