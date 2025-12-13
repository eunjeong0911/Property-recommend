"""
고급 Feature Engineering 사용 예시
"""
from pathlib import Path
from data_loader import DataLoader
from preprocessor import PriceDataPreprocessor


def example_basic_usage():
    """기본 사용 예시"""

    print("\n" + "=" * 70)
    print("📊 고급 Feature Engineering 사용 예시")
    print("=" * 70)

    # 1. 데이터 로딩
    data_dir = "C:/dev/SKN18-FINAL-1TEAM/data/actual_transaction_price"
    loader = DataLoader(data_dir)
    train_df, test_df = loader.load_train_test(
        train_filename="월세_train(24.08~25.08).csv",
        test_filename="월세_test(25.09~25.10).csv"
    )

    # 2. Preprocessor 초기화
    preprocessor = PriceDataPreprocessor()

    # 3. 타깃 생성
    print("\n[Step 1] 타깃 생성")
    train_df = preprocessor.create_target(train_df)
    test_df = preprocessor.create_target(test_df)
    print(f"✅ 타깃 컬럼 생성: {preprocessor.target_log}")

    # 4. 고급 피처 엔지니어링 적용
    print("\n[Step 2] 고급 피처 엔지니어링 적용")
    train_df, test_df = preprocessor.advanced_feature_engineering(train_df, test_df)

    # 5. 최종 피처 확인
    print(f"\n✅ 생성된 피처들:")
    print(f"   총 {len(preprocessor.candidate_features)}개 피처")
    print(f"\n   범주형 피처:")
    categorical_features = [
        "면적_qcat", "구_권역", "분기_라벨", "층_bin", "건축시대",
        "자치구_거래량_구간", "금리_국면", "금리_z_구간",
        "전용면적_자치구수준_z", "건축연도_자치구수준_z", "층수_자치구수준_z",
        "건물용도"
    ]
    for feat in categorical_features:
        if feat in preprocessor.candidate_features:
            print(f"      - {feat}")

    print(f"\n   수치형 피처:")
    numeric_features = [
        "자치구명_LE", "법정동명_LE", "자치구_건물용도_LE",
        "임대면적", "층", "건축연차",
        "KORIBOR", "기업대출", "전세자금대출", "CD",
        "무담보콜금리", "변동형주택담보대출", "소비자물가"
    ]
    for feat in numeric_features:
        if feat in preprocessor.candidate_features:
            print(f"      - {feat}")

    # 6. 모델링용 데이터 준비
    print(f"\n[Step 3] 모델링용 데이터 준비")

    # 타깃이 없는 행 제거
    train_ml = train_df.dropna(subset=[preprocessor.target_log]).copy()

    # 피처/타깃 분리
    X_train = train_ml[preprocessor.candidate_features]
    y_train = train_ml[preprocessor.target_log]

    X_test = test_df[preprocessor.candidate_features]
    y_test = test_df[preprocessor.target_log]

    print(f"✅ 모델링 데이터 준비 완료:")
    print(f"   - X_train: {X_train.shape}")
    print(f"   - y_train: {y_train.shape}")
    print(f"   - X_test:  {X_test.shape}")
    print(f"   - y_test:  {y_test.shape}")

    # 7. 샘플 데이터 확인
    print(f"\n[Step 4] 샘플 데이터 확인")
    print("\n첫 5개 행:")
    print(X_train.head())

    print("\n" + "=" * 70)
    print("✅ 예시 실행 완료!")
    print("=" * 70)

    return X_train, y_train, X_test, y_test


if __name__ == "__main__":
    # 예시 실행
    X_train, y_train, X_test, y_test = example_basic_usage()

    print("\n💡 다음 단계:")
    print("   1. 이 데이터로 모델을 학습할 수 있습니다.")
    print("   2. main.py를 실행하여 전체 파이프라인을 실행할 수 있습니다:")
    print("      python main.py --data_dir <데이터 경로>")
