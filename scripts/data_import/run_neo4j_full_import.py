import sys
import os
import subprocess

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from db_health_check import DatabaseHealthCheck
from importers.transport_importer import TransportImporter
from importers.amenity_importer import AmenityImporter
from importers.safety_importer import SafetyImporter
# from importers.property_importer import PropertyImporter
from importers.postgres_importer import PostgresImporter
from database import Database


def main():
    print("\n" + "=" * 70)
    print(" " * 20 + "데이터 Import 파이프라인 시작")
    print("=" * 70 + "\n")
    
    # 통계 추적
    stats = {
        "transport_subway": {"success": 0, "failed": 0},
        "transport_bus": {"success": 0, "failed": 0},
        "amenity_medical": {"success": 0, "failed": 0},
        "amenity_college": {"success": 0, "failed": 0},
        "amenity_store": {"success": 0, "failed": 0},
        "amenity_park": {"success": 0, "failed": 0},
        "safety_cctv": {"success": 0, "failed": 0},
        "safety_bell": {"success": 0, "failed": 0},
        "safety_police": {"success": 0, "failed": 0},
        "safety_fire": {"success": 0, "failed": 0},
        "property_neo4j": {"success": 0, "failed": 0},
        "property_postgres": {"success": 0, "failed": 0},
        "linking": {"success": 0, "failed": 0}
    }
    
    try:
        # 1. 환경 변수 검증
        print("[1/3] 환경 변수 검증 중...")
        Config.validate_env_vars()
        Config.validate_kakao_api_key()
        print("✓ 환경 변수 검증 완료\n")
        
        # 2. 데이터베이스 연결 검증
        print("[2/3] 데이터베이스 연결 검증 중...")
        DatabaseHealthCheck.wait_for_neo4j(
            Config.NEO4J_URI,
            Config.NEO4J_USER,
            Config.NEO4J_PASSWORD
        )
        DatabaseHealthCheck.wait_for_postgres(
            Config.POSTGRES_HOST,
            Config.POSTGRES_PORT,
            Config.POSTGRES_DB,
            Config.POSTGRES_USER,
            Config.POSTGRES_PASSWORD
        )
        print("✓ 데이터베이스 연결 검증 완료\n")
        
        # 3. 데이터 Import
        print("[3/3] 데이터 Import 시작...\n")
        
        # Transport
        print("=" * 70)
        print("1. 교통 데이터 Import")
        print("=" * 70)
        try:
            transport = TransportImporter()
            print("\n[1-1] 지하철역 데이터 Import 중...")
            transport.import_subway()
            stats["transport_subway"]["success"] = 1
            
            print("\n[1-2] 버스정류장 데이터 Import 중...")
            transport.import_bus()
            stats["transport_bus"]["success"] = 1
            print("✓ 교통 데이터 Import 완료\n")
        except Exception as e:
            print(f"✗ 교통 데이터 Import 실패: {e}\n")
            stats["transport_subway"]["failed"] = 1
            stats["transport_bus"]["failed"] = 1
        
        # Amenity
        print("=" * 70)
        print("2. 편의시설 데이터 Import")
        print("=" * 70)
        try:
            amenity = AmenityImporter()
            
            print("\n[2-1] 의료시설 데이터 Import 중...")
            amenity.import_medical()
            stats["amenity_medical"]["success"] = 1
            
            print("\n[2-2] 대학교 데이터 Import 중...")
            amenity.import_college()
            stats["amenity_college"]["success"] = 1
            
            print("\n[2-3] 편의점 데이터 Import 중...")
            amenity.import_store()
            stats["amenity_store"]["success"] = 1
            
            print("\n[2-4] 공원 데이터 Import 중...")
            amenity.import_park()
            stats["amenity_park"]["success"] = 1
            
            print("✓ 편의시설 데이터 Import 완료\n")
        except Exception as e:
            print(f"✗ 편의시설 데이터 Import 실패: {e}\n")
            stats["amenity_medical"]["failed"] = 1
            stats["amenity_college"]["failed"] = 1
            stats["amenity_store"]["failed"] = 1
            stats["amenity_park"]["failed"] = 1
        
        # Safety & Office
        print("=" * 70)
        print("3. 안전시설 데이터 Import")
        print("=" * 70)
        try:
            safety = SafetyImporter()
            
            print("\n[3-1] CCTV 데이터 Import 중...")
            safety.import_cctv()
            stats["safety_cctv"]["success"] = 1
            
            print("\n[3-2] 안심벨 데이터 Import 중...")
            safety.import_bell()
            stats["safety_bell"]["success"] = 1
            
            print("\n[3-3] 경찰서 데이터 Import 중...")
            safety.import_police()
            stats["safety_police"]["success"] = 1
            
            print("\n[3-4] 소방서 데이터 Import 중...")
            safety.import_fire()
            stats["safety_fire"]["success"] = 1
            
            print("✓ 안전시설 데이터 Import 완료\n")
        except Exception as e:
            print(f"✗ 안전시설 데이터 Import 실패: {e}\n")
            stats["safety_cctv"]["failed"] = 1
            stats["safety_bell"]["failed"] = 1
            stats["safety_police"]["failed"] = 1
            stats["safety_fire"]["failed"] = 1
        
        # Property (Neo4j)
        print("=" * 70)
        print("4. 매물 데이터 Import (Auto-Crawl Pipeline)")
        print("=" * 70)
        try:
            print("\n[4-1] 매물 데이터 파이프라인(크롤링->지오코딩->Import) 실행 중...")
            
            # import_properties_full.py 스크립트 경로
            current_dir = os.path.dirname(os.path.abspath(__file__))
            pipeline_script = os.path.join(current_dir, "importers", "import_properties_full.py")
            
            # 서브프로세스로 실행 (환경변수 상속)
            subprocess.run([sys.executable, pipeline_script], check=True)
            
            stats["property_neo4j"]["success"] = 1
            print("✓ 매물 데이터 Import 완료\n")
        except subprocess.CalledProcessError as e:
            print(f"✗ 매물 데이터 파이프라인 실행 실패 (Exit Code: {e.returncode})\n")
            stats["property_neo4j"]["failed"] = 1
        except Exception as e:
            print(f"✗ 매물 데이터 Import 실패: {e}\n")
            stats["property_neo4j"]["failed"] = 1
        
        # Property (PostgreSQL)
        print("=" * 70)
        print("5. 매물 데이터 Import (PostgreSQL)")
        print("=" * 70)
        pg_importer = None
        try:
            print("\n[5-1] 매물 데이터 Import 중...")
            pg_importer = PostgresImporter()
            pg_importer.import_properties()
            stats["property_postgres"]["success"] = 1
            print("✓ 매물 데이터 Import (PostgreSQL) 완료\n")
        except Exception as e:
            print(f"✗ 매물 데이터 Import (PostgreSQL) 실패: {e}\n")
            stats["property_postgres"]["failed"] = 1
        finally:
            if pg_importer:
                pg_importer.close()
        
        # Linking
        print("=" * 70)
        print("6. 데이터 연결 (Linking)")
        print("=" * 70)
        try:
            print("\n[6-1] 교통 데이터 연결 중...")
            transport.link_subway()
            transport.link_bus()
            
            print("\n[6-2] 편의시설 데이터 연결 중...")
            amenity.link_hospital()
            amenity.link_pharmacy()
            amenity.link_college()
            amenity.link_convenience()
            amenity.link_park()
            
            print("\n[6-3] 안전시설 데이터 연결 중...")
            safety.link_cctv()
            safety.link_bell()
            safety.link_police()
            safety.link_fire()
            
            stats["linking"]["success"] = 1
            print("✓ 데이터 연결 완료\n")
        except Exception as e:
            print(f"✗ 데이터 연결 실패: {e}\n")
            stats["linking"]["failed"] = 1
        
    except Exception as e:
        print(f"\n✗ 치명적 오류 발생: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        Database.close()
    
    # 최종 요약
    print("\n" + "=" * 70)
    print(" " * 25 + "Import 완료 요약")
    print("=" * 70)
    
    total_success = sum(s["success"] for s in stats.values())
    total_failed = sum(s["failed"] for s in stats.values())
    
    print(f"\n총 작업: {total_success + total_failed}개")
    print(f"  ✓ 성공: {total_success}개")
    print(f"  ✗ 실패: {total_failed}개")
    
    print("\n상세 결과:")
    print("  교통 데이터:")
    print(f"    - 지하철역: {'✓' if stats['transport_subway']['success'] else '✗'}")
    print(f"    - 버스정류장: {'✓' if stats['transport_bus']['success'] else '✗'}")
    
    print("  편의시설 데이터:")
    print(f"    - 의료시설: {'✓' if stats['amenity_medical']['success'] else '✗'}")
    print(f"    - 대학교: {'✓' if stats['amenity_college']['success'] else '✗'}")
    print(f"    - 편의점: {'✓' if stats['amenity_store']['success'] else '✗'}")
    print(f"    - 공원: {'✓' if stats['amenity_park']['success'] else '✗'}")
    
    print("  안전시설 데이터:")
    print(f"    - CCTV: {'✓' if stats['safety_cctv']['success'] else '✗'}")
    print(f"    - 안심벨: {'✓' if stats['safety_bell']['success'] else '✗'}")
    print(f"    - 경찰서: {'✓' if stats['safety_police']['success'] else '✗'}")
    print(f"    - 소방서: {'✓' if stats['safety_fire']['success'] else '✗'}")
    
    print("  매물 데이터:")
    print(f"    - Neo4j: {'✓' if stats['property_neo4j']['success'] else '✗'}")
    print(f"    - PostgreSQL: {'✓' if stats['property_postgres']['success'] else '✗'}")
    
    print("  데이터 연결:")
    print(f"    - Linking: {'✓' if stats['linking']['success'] else '✗'}")
    
    print("\n" + "=" * 70)
    
    if total_failed > 0:
        print("\n⚠ 일부 작업이 실패했습니다. 위의 오류 메시지를 확인하세요.")
        sys.exit(1)
    else:
        print("\n✓ 모든 데이터 Import가 성공적으로 완료되었습니다!")


if __name__ == "__main__":
    main()
