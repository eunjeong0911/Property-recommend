import os
import sys
import subprocess
import time

def run_step(step_name, script_path, cwd=None, env=None):
    """서브프로세스로 스크립트 실행"""
    print(f"\n{'='*80}")
    print(f"🚀 [Start] {step_name}")
    print(f"📜 Script: {script_path}")
    print(f"{'='*80}")
    start_time = time.time()
    
    try:
        # 환경변수 설정
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
            
        # 스크립트 실행
        subprocess.run([sys.executable, script_path], check=True, cwd=cwd, env=run_env)
        
        elapsed = time.time() - start_time
        print(f"\n✅ [Success] {step_name} (Time: {elapsed:.1f}s)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ [Failed] {step_name} (Exit Code: {e.returncode})")
        return False
    except Exception as e:
        print(f"\n❌ [Error] {step_name}: {e}")
        return False

def main():
    # 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__)) # scripts/data_import
    scripts_dir = os.path.dirname(current_dir)             # scripts
    project_root = os.path.dirname(scripts_dir)            # SKN18-FINAL-1TEAM
    
    print(f"📂 Project Root: {project_root}")
    
    # PYTHONPATH 설정 (libs 모듈 및 공통 스크립트 참조를 위해 프로젝트 루트 추가)
    env = {"PYTHONPATH": project_root}
    if "PYTHONPATH" in os.environ:
        env["PYTHONPATH"] += os.pathsep + os.environ["PYTHONPATH"]

    # =========================================================================
    # Step 1: 데이터 크롤링 (Crawling)
    # =========================================================================
    crawl_script = os.path.join(scripts_dir, "dataCrawling", "피터팬 매물 데이터", "crawl_seoul.py")
    
    # 크롤링 스크립트가 로컬 모듈을 import할 수 있도록 cwd 설정
    crawl_cwd = os.path.dirname(crawl_script)
    
    print("\n⚠️ 주의: 크롤링 작업은 시간이 오래 걸릴 수 있습니다.")
    print("   중단하려면 Ctrl+C를 누르세요.")
    time.sleep(2) # 사용자가 읽을 시간 부여
    
    if not run_step("1. 데이터 크롤링 (Seoul Real Estate Crawling)", crawl_script, cwd=crawl_cwd, env=env):
        print("\n⛔ 크롤링 실패로 인해 전체 파이프라인을 중단합니다.")
        sys.exit(1)

    # =========================================================================
    # Step 2: 전체 데이터 가공 및 적재 (Full EtL & Import)
    # - Geocoding, Preprocessing, Neo4j, Postgres, OpenSearch, Embedding, Linking
    # =========================================================================
    import_script = os.path.join(current_dir, "run_neo4j_full_import.py")
    
    if not run_step("2. 전체 데이터 적재 파이프라인 (Full Import Pipeline)", import_script, env=env):
        print("\n⛔ 데이터 적재 실패.")
        sys.exit(1)

    print("\n" + "="*80)
    print("🎉 [Complete] 모든 작업이 성공적으로 완료되었습니다!")
    print("="*80)

if __name__ == "__main__":
    main()
