import subprocess
import sys
import os

# 프로젝트 루트 경로
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
python_exe = sys.executable  # 현재 실행 중인 Python 사용
importers_dir = os.path.dirname(os.path.abspath(__file__))

# 실행할 임포터 목록 (Safety, Convenience, Culture, Pet 순서)
importers = [
    "safety_score_importer.py",
    "convenience_score_importer.py",
    "culture_score_importer.py",
    "pet_score_importer.py",
    "traffic_score_importer.py",  # 가중치 조정 후 실행 예정
]

print("=" * 50)
print("🌡️ 온도 임포터 순차 실행 시작")
print("=" * 50)

for importer in importers:
    importer_path = os.path.join(importers_dir, importer)
    print(f"\n▶ 실행 중: {importer}")
    print("-" * 40)
    
    result = subprocess.run(
        [python_exe, importer_path],
        cwd=project_root,
        capture_output=False
    )
    
    if result.returncode == 0:
        print(f"✅ {importer} 완료!")
    else:
        print(f"❌ {importer} 실패 (exit code: {result.returncode})")

print("\n" + "=" * 50)
print("🎉 모든 임포터 실행 완료!")
print("=" * 50)
