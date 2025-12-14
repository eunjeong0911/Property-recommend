"""
중개사 신뢰도 모델 - 이진 분류 전체 파이프라인 실행
순서:
1) 데이터 로드 (_00)
2) 타겟 생성 (_01)
3) 피처 생성 (_02)
4) 모델 학습 (_03)
5) 예측 (_04)
"""
from pathlib import Path
import sys
import os

# 프로젝트 루트로 작업 디렉토리 변경
# binary → pipeline → trust_model → models → reco → apps → SKN18-FINAL-1TEAM (7 levels)
project_root = Path(__file__).parent.parent.parent.parent.parent.parent.parent
os.chdir(project_root)
print(f"📁 작업 디렉토리: {project_root}")

# binary 폴더 경로 추가
binary_dir = Path(__file__).parent
sys.path.insert(0, str(binary_dir))

# 개별 단계 import
from _00_load_data import main as step00_load_data
from _01_targer_engineering import main as step01_create_target
from _02_feature_engineering import main as step02_create_features
from _03_train_model import main as step03_train
from _04_predict import main as step04_predict


def main():
    print("\n" + "=" * 60)
    print("🚀 이진 분류 파이프라인 실행")
    print("=" * 60)

    try:
        # 1) 데이터 로드
        print("\n\n=== [1단계] 데이터 로드 ===")
        df = step00_load_data()
        print("✅ 1단계 완료")

        # 2) 타겟 생성
        print("\n\n=== [2단계] 타겟 생성 (2등급) ===")
        df = step01_create_target(df)
        print("✅ 2단계 완료")

        # 3) 피처 생성
        print("\n\n=== [3단계] 피처 생성 ===")
        _, X, feature_names = step02_create_features(df)
        print("✅ 3단계 완료")

        # 4) 모델 학습
        print("\n\n=== [4단계] 모델 학습 ===")
        step03_train()
        print("✅ 4단계 완료")

        # 5) 예측
        print("\n\n=== [5단계] 예측 ===")
        step04_predict()
        print("✅ 5단계 완료")

        print("\n" + "=" * 60)
        print("🎉 이진 분류 파이프라인 완료!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
