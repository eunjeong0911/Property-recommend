"""
Neo4j 데이터만 Import하는 스크립트
PostgreSQL 제외, Neo4j 노드 + 관계만 생성
"""
import sys
import os

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from db_health_check import DatabaseHealthCheck
from importers.neo4j_importers.facility.transport_importer import TransportImporter
from importers.neo4j_importers.facility.amenity_importer import AmenityImporter
from importers.neo4j_importers.facility.safety_importer import SafetyImporter
from importers.neo4j_importers.temperature.safety_score_importer import SafetyScoreImporter
from importers.neo4j_importers.temperature.convenience_score_importer import ConvenienceScoreImporter
from importers.neo4j_importers.temperature.traffic_score_importer import TrafficScoreImporter
from importers.neo4j_importers.property.property_importer import PropertyImporter
from database import Database


def main():
    print("\n" + "=" * 70)
    print(" " * 15 + "Neo4j 데이터 Import 파이프라인 시작")
    print("=" * 70 + "\n")
    
    try:
        # 1. 환경 변수 검증
        print("[1/2] 환경 변수 검증 중...")
        Config.validate_env_vars()
        Config.validate_kakao_api_key()
        print("✓ 환경 변수 검증 완료\n")
        
        # 2. Neo4j 연결 검증
        print("[2/2] Neo4j 연결 검증 중...")
        DatabaseHealthCheck.wait_for_neo4j(
            Config.NEO4J_URI,
            Config.NEO4J_USER,
            Config.NEO4J_PASSWORD
        )
        print("✓ Neo4j 연결 검증 완료\n")
        
        # 3. 데이터 Import
        print("=" * 70)
        print("1. 교통 데이터 Import")
        print("=" * 70)
        transport = TransportImporter()
        print("\n[1-1] 지하철역 데이터 Import 중...")
        transport.import_subway()
        print("\n[1-2] 버스정류장 데이터 Import 중...")
        transport.import_bus()
        print("✓ 교통 데이터 Import 완료\n")
        
        print("=" * 70)
        print("2. 편의시설 데이터 Import")
        print("=" * 70)
        amenity = AmenityImporter()
        print("\n[2-1] 의료시설 데이터 Import 중...")
        amenity.import_medical()
        print("\n[2-2] 대학교 데이터 Import 중...")
        amenity.import_college()
        print("\n[2-3] 편의점 데이터 Import 중...")
        amenity.import_store()
        print("\n[2-4] 공원 데이터 Import 중...")
        amenity.import_park()
        print("\n[2-5] 대형 점포 데이터 Import 중...")
        amenity.import_large_store()
        print("\n[2-6] 문화 시설 데이터 Import 중...")
        amenity.import_culture()
        print("✓ 편의시설 데이터 Import 완료\n")
        
        print("=" * 70)
        print("3. 안전시설 데이터 Import")
        print("=" * 70)
        safety = SafetyImporter()
        print("\n[3-1] CCTV 데이터 Import 중...")
        safety.import_cctv()
        print("\n[3-2] 안심벨 데이터 Import 중...")
        safety.import_bell()
        print("\n[3-3] 경찰서 데이터 Import 중...")
        safety.import_police()
        print("\n[3-4] 소방서 데이터 Import 중...")
        safety.import_fire()
        print("✓ 안전시설 데이터 Import 완료\n")
        
        print("=" * 70)
        print("4. 매물 데이터 Import (Neo4j)")
        print("=" * 70)
        print("\n[4-1] 매물 데이터 Import 중...")
        prop = PropertyImporter()
        prop.import_properties()
        print("✓ 매물 데이터 Import 완료\n")
        
        print("=" * 70)
        print("5. 데이터 연결 (Linking)")
        print("=" * 70)
        print("\n[5-1] 교통 데이터 연결 중...")
        transport.link_subway()
        transport.link_bus()
        
        print("\n[5-2] 편의시설 데이터 연결 중...")
        amenity.link_hospital()
        amenity.link_pharmacy()
        amenity.link_college()
        amenity.link_convenience()
        amenity.link_park()
        amenity.link_large_mart()
        amenity.link_laundry()
        amenity.link_culture()
        
        print("\n[5-3] 안전시설 데이터 연결 중...")
        safety.link_cctv()
        safety.link_bell()
        safety.link_police()
        safety.link_fire()
        print("✓ 데이터 연결 완료\n")
        
        print("=" * 70)
        print("6. 점수/온도 계산 (Score Calculation)")
        print("=" * 70)
        print("\n[6-1] 안전 온도 계산 및 Import 중...")
        safety_score = SafetyScoreImporter()
        safety_score.import_safety_score()
        print("✓ 안전 온도 계산 완료")

        print("\n[6-2] 편의/생활 온도 계산 및 Import 중...")
        conv_score = ConvenienceScoreImporter()
        conv_score.import_convenience_score()
        print("✓ 편의/생활 온도 계산 완료")
        
        print("\n[6-3] 교통 온도 계산 및 Import 중...")
        traffic_score = TrafficScoreImporter()
        traffic_score.import_traffic_score()
        print("✓ 교통 온도 계산 완료\n")
        
        print("=" * 70)
        print("✓ Neo4j 데이터 Import 완료!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        Database.close()


if __name__ == "__main__":
    main()
