"""
매물 가격 예측 및 평가 모듈
학습된 모델을 사용하여 개별 매물의 적정 가격을 예측하고 평가합니다.
"""
import os
import pickle
import pandas as pd
import numpy as np
from typing import Tuple, Dict, List

# 모듈 import
try:
    from .data_preprocessing import preprocess_data
    from .feature_engineering import create_all_features, prepare_ml_features
    from .model import load_model
except ImportError:
    from data_preprocessing import preprocess_data
    from feature_engineering import create_all_features, prepare_ml_features
    from model import load_model


def predict_single_property(model, property_features: pd.DataFrame) -> float:
    """
    단일 매물의 예상 가격을 예측합니다.

    Args:
        model: 학습된 모델
        property_features: 매물의 특성 데이터프레임 (1행)

    Returns:
        float: 예상 환산보증금 (만원)
    """
    # 로그 변환된 예측값을 원래 스케일로 복원
    y_pred_log = model.predict(property_features)
    y_pred = np.expm1(y_pred_log)
    return y_pred[0]


def evaluate_price_difference(actual_price: float, predicted_price: float,
                               threshold_cheap: float = 0.1,
                               threshold_expensive: float = 0.1) -> Tuple[str, float, float]:
    """
    실제 가격과 예상 가격의 차이를 평가합니다.

    Args:
        actual_price: 실제 환산보증금 (만원)
        predicted_price: 예상 환산보증금 (만원)
        threshold_cheap: 싸다고 판단하는 임계값 비율 (기본값: 10%)
        threshold_expensive: 비싸다고 판단하는 임계값 비율 (기본값: 10%)

    Returns:
        tuple: (평가, 차이금액, 차이비율)
            - 평가: "싸다", "적정", "비싸다"
            - 차이금액: 실제가격 - 예상가격 (만원)
            - 차이비율: (실제가격 - 예상가격) / 예상가격 * 100 (%)
    """
    difference = actual_price - predicted_price
    difference_ratio = (difference / predicted_price) * 100

    if difference_ratio < -threshold_cheap * 100:
        evaluation = "싸다"
    elif difference_ratio > threshold_expensive * 100:
        evaluation = "비싸다"
    else:
        evaluation = "적정"

    return evaluation, difference, difference_ratio


def predict_and_evaluate_properties(model, df_processed: pd.DataFrame,
                                     original_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    모든 매물에 대해 가격을 예측하고 평가합니다.

    Args:
        model: 학습된 모델
        df_processed: 전처리 및 특성 엔지니어링이 완료된 데이터프레임
        original_df: 원본 데이터프레임 (추가 정보 표시용, 옵션)

    Returns:
        pd.DataFrame: 예측 결과가 포함된 데이터프레임
    """
    # 특성 준비
    df_ml = prepare_ml_features(df_processed)

    # 타겟 분리
    X = df_ml.drop(columns=["환산보증금"])
    y_actual = df_ml["환산보증금"]

    # 예측
    y_pred_log = model.predict(X)
    y_pred = np.expm1(y_pred_log)

    # 결과 데이터프레임 생성
    results = pd.DataFrame({
        "실제_환산보증금": y_actual.values,
        "예상_환산보증금": y_pred,
        "차이_금액": y_actual.values - y_pred,
        "차이_비율(%)": ((y_actual.values - y_pred) / y_pred) * 100
    })

    # 평가 추가
    results["가격_평가"] = results.apply(
        lambda row: evaluate_price_difference(
            row["실제_환산보증금"],
            row["예상_환산보증금"]
        )[0],
        axis=1
    )

    # 원본 데이터의 일부 정보 추가
    if original_df is not None and len(original_df) == len(results):
        # 주요 정보 컬럼 추가
        info_columns = []

        if "주소_정보.전체주소" in df_processed.columns:
            results["주소"] = df_processed["주소_정보.전체주소"].values

        if "거래_정보.거래방식" in original_df.columns:
            results["거래방식"] = original_df["거래_정보.거래방식"].values

        if "전용면적_평" in df_processed.columns:
            results["전용면적_평"] = df_processed["전용면적_평"].values

        if "방수" in df_processed.columns:
            results["방수"] = df_processed["방수"].values

        if "층" in df_processed.columns:
            results["층"] = df_processed["층"].values

    # 컬럼 순서 재정렬
    column_order = []
    if "주소" in results.columns:
        column_order.append("주소")
    if "거래방식" in results.columns:
        column_order.append("거래방식")
    if "전용면적_평" in results.columns:
        column_order.append("전용면적_평")
    if "방수" in results.columns:
        column_order.append("방수")
    if "층" in results.columns:
        column_order.append("층")

    column_order.extend([
        "실제_환산보증금",
        "예상_환산보증금",
        "차이_금액",
        "차이_비율(%)",
        "가격_평가"
    ])

    results = results[column_order]

    return results


def analyze_price_distribution(results_df: pd.DataFrame) -> Dict:
    """
    가격 평가 분포를 분석합니다.

    Args:
        results_df: 예측 결과 데이터프레임

    Returns:
        dict: 분석 결과
    """
    total_count = len(results_df)

    evaluation_counts = results_df["가격_평가"].value_counts()

    analysis = {
        "전체_매물수": total_count,
        "싸다_개수": evaluation_counts.get("싸다", 0),
        "적정_개수": evaluation_counts.get("적정", 0),
        "비싸다_개수": evaluation_counts.get("비싸다", 0),
        "싸다_비율(%)": (evaluation_counts.get("싸다", 0) / total_count) * 100,
        "적정_비율(%)": (evaluation_counts.get("적정", 0) / total_count) * 100,
        "비싸다_비율(%)": (evaluation_counts.get("비싸다", 0) / total_count) * 100,
        "평균_차이_금액": results_df["차이_금액"].mean(),
        "평균_차이_비율(%)": results_df["차이_비율(%)"].mean(),
        "최대_저렴한_매물_차이": results_df["차이_금액"].min(),
        "최대_비싼_매물_차이": results_df["차이_금액"].max()
    }

    return analysis


def save_prediction_results(results_df: pd.DataFrame,
                            output_dir: str = None,
                            filename: str = None) -> str:
    """
    예측 결과를 CSV 파일로 저장합니다.

    Args:
        results_df: 예측 결과 데이터프레임
        output_dir: 저장 디렉토리
        filename: 파일명

    Returns:
        str: 저장된 파일 경로
    """
    from datetime import datetime

    if output_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "outputs")

    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"price_predictions_{timestamp}.csv"

    filepath = os.path.join(output_dir, filename)
    results_df.to_csv(filepath, index=False, encoding='utf-8-sig')

    print(f"✓ 예측 결과 저장 완료: {filepath}")
    return filepath


def get_cheap_properties(results_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    가장 저렴한(싸다) 매물 목록을 반환합니다.

    Args:
        results_df: 예측 결과 데이터프레임
        top_n: 반환할 매물 개수

    Returns:
        pd.DataFrame: 저렴한 매물 목록 (차이 비율이 낮은 순)
    """
    cheap_properties = results_df[results_df["가격_평가"] == "싸다"].copy()
    cheap_properties = cheap_properties.sort_values("차이_비율(%)")
    return cheap_properties.head(top_n)


def get_expensive_properties(results_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    가장 비싼(비싸다) 매물 목록을 반환합니다.

    Args:
        results_df: 예측 결과 데이터프레임
        top_n: 반환할 매물 개수

    Returns:
        pd.DataFrame: 비싼 매물 목록 (차이 비율이 높은 순)
    """
    expensive_properties = results_df[results_df["가격_평가"] == "비싸다"].copy()
    expensive_properties = expensive_properties.sort_values("차이_비율(%)", ascending=False)
    return expensive_properties.head(top_n)


def main(model_path: str, data_path: str, save_results: bool = True):
    """
    전체 예측 및 평가 파이프라인을 실행합니다.

    Args:
        model_path: 학습된 모델 파일 경로
        data_path: 데이터 파일 경로
        save_results: 결과 저장 여부

    Returns:
        tuple: (results_df, analysis)
    """
    print("=" * 80)
    print("매물 가격 예측 및 평가 시작")
    print("=" * 80)

    # 1. 모델 로드
    print("\n[1/4] 모델 로드 중...")
    model = load_model(model_path)

    # 2. 데이터 전처리
    print("\n[2/4] 데이터 전처리 중...")
    df_original = pd.read_csv(data_path, encoding='utf-8')
    df_walse = preprocess_data(data_path)
    print(f"✓ 데이터 로드 완료: {len(df_walse)}행")

    # 3. 특성 엔지니어링
    print("\n[3/4] 특성 엔지니어링 중...")
    df_walse = create_all_features(df_walse)
    print("✓ 특성 엔지니어링 완료")

    # 4. 예측 및 평가
    print("\n[4/4] 가격 예측 및 평가 중...")
    results_df = predict_and_evaluate_properties(model, df_walse, df_original)
    print("✓ 예측 완료")

    # 분석 결과
    analysis = analyze_price_distribution(results_df)

    # 결과 출력
    print("\n" + "=" * 80)
    print("예측 결과 요약")
    print("=" * 80)
    print(f"전체 매물 수: {analysis['전체_매물수']:,}개")
    print(f"\n가격 평가 분포:")
    print(f"  - 싸다:  {analysis['싸다_개수']:,}개 ({analysis['싸다_비율(%)']:.1f}%)")
    print(f"  - 적정:  {analysis['적정_개수']:,}개 ({analysis['적정_비율(%)']:.1f}%)")
    print(f"  - 비싸다: {analysis['비싸다_개수']:,}개 ({analysis['비싸다_비율(%)']:.1f}%)")
    print(f"\n평균 차이:")
    print(f"  - 금액: {analysis['평균_차이_금액']:,.0f}만원")
    print(f"  - 비율: {analysis['평균_차이_비율(%)']:.1f}%")
    print("=" * 80)

    # 저렴한 매물 TOP 10
    print("\n[가장 저렴한 매물 TOP 10]")
    cheap_properties = get_cheap_properties(results_df, top_n=10)
    if len(cheap_properties) > 0:
        for idx, row in cheap_properties.iterrows():
            print(f"\n{idx+1}.")
            if "주소" in row:
                print(f"  주소: {row['주소']}")
            if "거래방식" in row:
                print(f"  거래방식: {row['거래방식']}")
            print(f"  실제 가격: {row['실제_환산보증금']:,.0f}만원")
            print(f"  예상 가격: {row['예상_환산보증금']:,.0f}만원")
            print(f"  차이: {row['차이_금액']:,.0f}만원 ({row['차이_비율(%)']:.1f}%)")

    # 비싼 매물 TOP 10
    print("\n[가장 비싼 매물 TOP 10]")
    expensive_properties = get_expensive_properties(results_df, top_n=10)
    if len(expensive_properties) > 0:
        for idx, row in expensive_properties.iterrows():
            print(f"\n{idx+1}.")
            if "주소" in row:
                print(f"  주소: {row['주소']}")
            if "거래방식" in row:
                print(f"  거래방식: {row['거래방식']}")
            print(f"  실제 가격: {row['실제_환산보증금']:,.0f}만원")
            print(f"  예상 가격: {row['예상_환산보증금']:,.0f}만원")
            print(f"  차이: {row['차이_금액']:,.0f}만원 ({row['차이_비율(%)']:.1f}%)")

    # 결과 저장
    if save_results:
        print("\n[결과 저장]")
        save_prediction_results(results_df)

    print("\n" + "=" * 80)
    print("예측 및 평가 완료!")
    print("=" * 80)

    return results_df, analysis


if __name__ == "__main__":
    # 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 모델 경로 (가장 최근 모델 사용)
    models_dir = os.path.join(current_dir, "models")
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
    if model_files:
        # 파일명으로 정렬하여 가장 최근 모델 선택
        model_files.sort(reverse=True)
        model_path = os.path.join(models_dir, model_files[0])
    else:
        print("모델 파일을 찾을 수 없습니다. 먼저 main.py를 실행하여 모델을 학습하세요.")
        exit(1)

    # 데이터 경로
    data_path = os.path.join(r"C:\dev\SKN18-FINAL-1TEAM\data\통합.csv")

    # 실행
    results_df, analysis = main(
        model_path=model_path,
        data_path=data_path,
        save_results=True
    )

    # 결과 확인
    print(f"\n결과 데이터프레임 크기: {results_df.shape}")
    print("\n첫 10개 매물:")
    print(results_df.head(10).to_string())
