"""
Neo4j 데이터만 Import하는 스크립트
PostgreSQL 제외, Neo4j 노드 + 관계만 생성
"""
import sys
import os
from pathlib import Path

# Add scripts/03_import to path for config/db_health_check
IMPORT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(IMPORT_DIR))

from config import Config
from db_health_check import DatabaseHealthCheck
from database import Database

# Neo4j importer imports (현재 폴더 기준)
from facility.transport_importer import TransportImporter
from facility.amenity_importer import AmenityImporter
from facility.safety_importer import SafetyImporter
from facility.animal_importer import AnimalImporter
from facility.culture_importer import CultureImporter
from temperature.safety_score_importer import SafetyScoreImporter
from temperature.convenience_score_importer import ConvenienceScoreImporter
from temperature.traffic_score_importer import TrafficScoreImporter
from temperature.culture_score_importer import CultureScoreImporter
from temperature.pet_score_importer import PetScoreImporter
from property.property_importer import PropertyImporter


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
        print("1. 매물 데이터 Import (Neo4j) - 우선 실행")
        print("=" * 70)
        print("\n[1-1] 매물 데이터 Import 중...")
        prop = PropertyImporter()
        prop.import_properties()
        print("✓ 매물 데이터 Import 완료\n")

        print("=" * 70)
        print("2. 교통 데이터 Import")
        print("=" * 70)
        transport = TransportImporter()
        print("\n[2-1] 지하철역 데이터 Import 중...")
        transport.import_subway()
        print("\n[2-2] 버스정류장 데이터 Import 중...")
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
        print("\n[2-4] 대형 점포 데이터 Import 중...")
        amenity.import_large_store()
        print("✓ 편의시설 데이터 Import 완료\n")
        
        print("=" * 70)
        print("2-1. 문화시설 및 공원 데이터 Import")
        print("=" * 70)
        culture = CultureImporter()
        print("\n[2-1-1] 문화시설 데이터 Import 중...")
        culture.import_culture_nodes()
        print("\n[2-1-2] 공원 데이터 Import 중...")
        culture.import_park()
        print("✓ 문화시설 및 공원 데이터 Import 완료\n")
        
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
        print("3-1. 반려동물 놀이터 데이터 Import") # New section for animal importer
        print("=" * 70)
        animal = AnimalImporter()
        print("\n[3-1-1] 반려동물 놀이터 데이터 Import 중...")
        animal.import_pet_places()
        print("\n[3-1-2] 반려동물 상가 데이터 Import 중...")
        animal.import_pet_stores()
        print("✓ 반려동물 데이터 Import 완료\n")
        
        # Property import moved to start

        
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
        amenity.link_large_mart()
        amenity.link_laundry()
        
        print("\n[5-3] 문화시설/공원 데이터 연결 중...")
        culture.link_culture()
        culture.link_park()
        
        print("\n[5-4] 안전시설 데이터 연결 중...")
        safety.link_cctv()
        safety.link_bell()
        safety.link_police()
        safety.link_fire()
        
        print("\n[5-5] 반려동물 시설 데이터 연결 중...")
        animal.link_pet_places()
        animal.link_pet_stores()
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
        print("✓ 교통 온도 계산 완료")

        print("\n[6-4] 문화 온도 계산 및 Import 중...")
        culture_score = CultureScoreImporter()
        culture_score.import_culture_score()
        print("✓ 문화 온도 계산 완료")

        print("\n[6-5] 반려동물 온도 계산 및 Import 중...")
        pet_score = PetScoreImporter()
        pet_score.import_nodes()
        pet_score.calculate_scores()
        print("✓ 반려동물 온도 계산 완료\n")
        
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
