import sys
import subprocess
import time
import os

def run_script(script_path, cwd=None, env=None):
    """
    파이썬 스크립트 실행
    :param script_path: 실행할 스크립트의 절대 경로
    :param cwd: 스크립트를 실행할 작업 디렉토리 (None일 경우 현재 프로세스 CWD 사용)
    :param env: 추가할 환경변수
    """
    script_name = os.path.basename(script_path)
    print(f"\n🚀 [{script_name}] 실행 시작...")
    if cwd:
        print(f"   📂 Working Dir: {cwd}")
    print("=" * 60)
    
    start_time = time.time()
    
    # 환경변수 병합
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    
    try:
        # 스크립트 실행
        result = subprocess.run(
            [sys.executable, script_path], 
            check=True,
            cwd=cwd, 
            env=run_env
        )
        
        elapsed = time.time() - start_time
        print("=" * 60)
        print(f"✅ [{script_name}] 완료! (소요시간: {int(elapsed)}초)")
        return True
        
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print(f"❌ [{script_name}] 실행 중 오류 발생 (Exit Code: {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
        return False

def main():
    print("full_import_pipeline".center(60, "="))
    print("서울시 매물 통합 Import 파이프라인 (크롤링 -> 지오코딩 -> Neo4j)")
    print("=" * 60)
    
    total_start = time.time()
    
    # 1. 경로 계산
    # 현재 파일 위치: scripts/data_import/importers/import_properties_full.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 프로젝트 루트: scripts/data_import/importers -> (3단계 위) -> root
    # parent(importers) -> parent(data_import) -> parent(scripts) -> parent(root) => 4단계
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    
    # 크롤링 스크립트 위치 (scripts/dataCrawling/피터팬 매물 데이터)
    crawl_dir = os.path.join(root_dir, "scripts", "dataCrawling", "피터팬 매물 데이터")
    
    # Import 관련 경로 (scripts/data_import)
    import_base_dir = os.path.join(root_dir, "scripts", "data_import")

    # ---------------------------------------------------------
    # 1단계: 크롤링 + 병합 + 판매완료 정리
    # ---------------------------------------------------------
    crawl_script = os.path.join(crawl_dir, "crawl_seoul.py")
    
    # 크롤링은 반드시 해당 폴더(crawl_dir)에서 실행해야 data 폴더 및 txt 파일을 올바르게 찾습니다.
    if not run_script(crawl_script, cwd=crawl_dir):
        print("\n⛔ 크롤링 단계에서 실패하여 작업을 중단합니다.")
        sys.exit(1)
    
    # ---------------------------------------------------------
    # 2단계: 지오코딩 (좌표 변환)
    # ---------------------------------------------------------
    geocode_script = os.path.join(crawl_dir, "geocode_addresses.py")
    
    # 지오코딩도 동일한 폴더에서 실행 (데이터 읽기 위함)
    if not run_script(geocode_script, cwd=crawl_dir):
        print("\n⛔ 지오코딩 단계에서 실패했습니다.")
        sys.exit(1)
        
    # ---------------------------------------------------------
    # 3단계: Neo4j Import
    # ---------------------------------------------------------
    # property_importer.py는 현재 스크립트 위치 기준 neo4j_importers/property 폴더 안에 있음
    importer_script = os.path.join(current_dir, "neo4j_importers", "property", "property_importer.py")
    
    # DATA_DIR 환경변수 설정: importer가 올바른 데이터 경로(data/GraphDB_data)를 찾도록 설정
    data_dir_env = os.path.join(root_dir, "data", "GraphDB_data")
    
    env = {
        "PYTHONPATH": import_base_dir,  # config.py 로드를 위해 필요
        "DATA_DIR": data_dir_env        # 데이터 경로 강제 지정
    }
    
    if not run_script(importer_script, env=env): # cwd는 현재 폴더 유지해도 무방
        print("\n⛔ Neo4j Import 단계에서 실패했습니다.")
        sys.exit(1)
        
    total_elapsed = time.time() - total_start
    hours, rem = divmod(total_elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    
    print("\n" + "=" * 60)
    print(f"🎉 모든 작업이 성공적으로 완료되었습니다!")
    print(f"⏱️ 총 소요 시간: {int(hours)}시간 {int(minutes)}분 {int(seconds)}초")
    print("=" * 60)

if __name__ == "__main__":
    main()
