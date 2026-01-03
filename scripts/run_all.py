#!/usr/bin/env python
"""
전체 데이터 파이프라인 실행 스크립트
1. 데이터 Import (Neo4j, Postgres, ES)
2. 가격 분류 모델 적용
"""
import sys
import subprocess
from pathlib import Path

def run_script(script_path, cwd=None):
    print(f"\n🚀 실행 중: {script_path}")
    result = subprocess.run([sys.executable, str(script_path)], cwd=cwd)
    if result.returncode != 0:
        print(f"❌ 실패: {script_path} (Exit code: {result.returncode})")
        return False
    return True

def main():
    base_dir = Path(__file__).parent
    
    print("\n" + "=" * 70)
    print(" " * 20 + "🚀 전체 파이프라인 시작")
    print("=" * 70)
    
    # 1. 데이터 Import
    print("\n" + "=" * 70)
    print(" " * 15 + "📦 [Step 1/2] 데이터 Import 시작")
    print("=" * 70)
    import_script = base_dir / "03_import" / "import_all.py"
    if not run_script(import_script):
        sys.exit(1)
        
    # 2. 가격 분류 모델 적용
    print("\n" + "=" * 70)
    print(" " * 10 + "🤖 [Step 2/2] 가격 분류 모델 적용 시작")
    print("=" * 70)
    analysis_script = base_dir / "04_analysis" / "price_model" / "apply_price_classification.py"
    if analysis_script.exists():
        print(f"📍 스크립트 경로: {analysis_script}")
        if not run_script(analysis_script):
            sys.exit(1)
    else:
        print(f"⚠️ 분석 스크립트를 찾을 수 없습니다: {analysis_script}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✅ 모든 작업이 성공적으로 완료되었습니다!")
    print("=" * 70)

if __name__ == "__main__":
    main()
