"""
Neo4j에서 지오코딩된 좌표를 추출하여 원본 JSON 파일에 병합하는 스크립트

사용법:
    cd scripts
    ..\apps\backend\.venv\Scripts\python.exe export_coords_to_json.py
"""

import os
import sys
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase

# .env 파일 로드 (프로젝트 루트)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Neo4j 연결 정보
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# 데이터 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(PROJECT_ROOT, "GraphDB_data", "home_data")
TARGET_DIR = os.path.join(PROJECT_ROOT, "data", "landData")


def get_coords_from_neo4j():
    """Neo4j에서 모든 Property의 좌표 데이터를 가져옴"""
    print(f"Neo4j 연결 중... ({NEO4J_URI})")
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    coords = {}
    
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (p:Property)
                WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
                RETURN p.id AS listing_id, p.latitude AS lat, p.longitude AS lng
            """)
            
            for record in result:
                listing_id = record["listing_id"]
                coords[listing_id] = {
                    "lat": record["lat"],
                    "lng": record["lng"]
                }
            
            print(f"✓ Neo4j에서 {len(coords)}개의 좌표 데이터를 가져왔습니다.")
    finally:
        driver.close()
    
    return coords


def merge_coords_to_json(coords):
    """좌표 데이터를 원본 JSON 파일에 병합"""
    
    if not os.path.exists(SOURCE_DIR):
        print(f"✗ 소스 디렉토리가 없습니다: {SOURCE_DIR}")
        return
    
    json_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.json')]
    print(f"\n처리할 JSON 파일: {len(json_files)}개")
    
    total_merged = 0
    total_not_found = 0
    
    for json_file in json_files:
        source_path = os.path.join(SOURCE_DIR, json_file)
        target_path = os.path.join(TARGET_DIR, json_file)
        
        print(f"\n처리 중: {json_file}")
        
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        merged_count = 0
        not_found_count = 0
        
        for item in data:
            listing_id = item.get("매물번호")
            
            if listing_id and listing_id in coords:
                # 좌표 정보 추가
                item["좌표_정보"] = {
                    "위도": coords[listing_id]["lat"],
                    "경도": coords[listing_id]["lng"]
                }
                merged_count += 1
            else:
                not_found_count += 1
        
        # 결과 저장 (data/landData에 저장)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ 좌표 병합: {merged_count}개")
        print(f"  - 좌표 없음: {not_found_count}개")
        print(f"  → 저장: {target_path}")
        
        total_merged += merged_count
        total_not_found += not_found_count
    
    return total_merged, total_not_found


def main():
    print("=" * 60)
    print("Neo4j 좌표 데이터 → JSON 병합 스크립트")
    print("=" * 60)
    
    # 1. Neo4j에서 좌표 가져오기
    coords = get_coords_from_neo4j()
    
    if not coords:
        print("\n✗ Neo4j에서 좌표 데이터를 가져오지 못했습니다.")
        print("  - Neo4j가 실행 중인지 확인하세요: docker-compose up -d neo4j")
        print("  - 데이터가 임포트되었는지 확인하세요.")
        sys.exit(1)
    
    # 2. JSON 파일에 병합
    total_merged, total_not_found = merge_coords_to_json(coords)
    
    # 3. 결과 요약
    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"총 병합된 매물: {total_merged}개")
    print(f"좌표 없는 매물: {total_not_found}개")
    print(f"\n결과 파일 위치: {TARGET_DIR}")


if __name__ == "__main__":
    main()
