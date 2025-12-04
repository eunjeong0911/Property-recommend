"""
JSON 매물 데이터를 이용해 전세 가격을 예측하는 예제 스크립트

요구 사항
---------
1. data/ 디렉토리에 있는 여러 JSON 파일(빌라/주택, 아파트, 오피스텔, 원투룸)을 사용
2. 모듈화된 전처리/특성 엔지니어링/모델 모듈을 그대로 재사용
3. models 폴더에는 *.pkl 파일만 존재해야 함
4. results 폴더에는
   - images/ 에 PNG 결과를 저장
   - predictions_*.csv 와 summary.json 등 모델 결과물을 저장
"""
import json
import os
from datetime import datetime
from typing import Dict, List

import pandas as pd
import numpy as np

from data_preprocessing import (
    filter_jeonse_data,
    parse_korean_money,
    extract_area,
    extract_management_fee,
    extract_floor,
    extract_gu_dong,
    remove_outliers_iqr,
)
from feature_engineering import (
    create_all_features,
    prepare_ml_features,
)
from model import (
    load_model,
    predict_model,
)
from visualization import (
    setup_matplotlib_korean,
    plot_target_distribution,
    plot_gu_average_price,
)


# =====================================================================
# 데이터 전처리 Helper
# =====================================================================

def preprocess_from_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    JSON에서 로드한 DataFrame을 전처리합니다.
    (preprocess_data 함수와 동일한 파이프라인이지만, 파일 대신 DataFrame을 입력으로 받습니다.)
    """
    df = df_raw.copy()

    # 1. 전세 데이터만 필터링
    df = filter_jeonse_data(df)

    if df.empty:
        return df

    # 2. 전세금 추출
    df["전세금"] = df["거래_정보.거래방식"].apply(parse_korean_money)

    # 3. 전용면적 추출
    df["전용면적_m2"] = df["매물_정보.전용/공급면적"].apply(extract_area)
    df["전용면적_평"] = df["전용면적_m2"] / 3.3

    # 4. 평당 전세금 계산 (타겟 변수)
    df["평당가"] = df["전세금"] / df["전용면적_평"].replace(0, np.nan)

    # 5. 결측치 제거
    df = df.dropna(subset=["전용면적_평", "평당가"])

    # 6. 음수 및 0 제거
    df = df[df["평당가"] > 0]

    if df.empty:
        return df

    # 7. 이상치 제거 (IQR 방법)
    df = remove_outliers_iqr(df, "평당가")

    # 8. 관리비 추출
    df["관리비"] = df["거래_정보.관리비"].apply(extract_management_fee)

    # 9. 층 정보 추출
    df["층"] = df["매물_정보.해당층/전체층"].apply(extract_floor)

    # 10. 방/욕실 개수 추출
    room_info = df["매물_정보.방/욕실개수"].str.extract(
        r"(?P<방수>\d+)개/(?P<욕실수>\d+)개"
    )
    df["방수"] = room_info["방수"].astype(float)
    df["욕실수"] = room_info["욕실수"].astype(float)

    # 11. 구/동 추출
    df["구"], df["동"] = zip(*df["주소_정보.전체주소"].apply(extract_gu_dong))

    # 12. 결측치 제거
    df = df.dropna(subset=["구", "동", "층", "방수", "욕실수"])

    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    전처리된 DataFrame에 대해 특성 엔지니어링 + ML 특성 구성을 수행합니다.
    """
    if df.empty:
        return df

    df_features = create_all_features(df, use_oof_target_encoding=False)
    df_ml = prepare_ml_features(df_features)

    return df_ml


# =====================================================================
# 예측/저장 Helper
# =====================================================================

def load_latest_model(models_dir: str) -> str:
    """
    models 디렉토리에서 가장 최근 모델 파일을 찾습니다.
    """
    if not os.path.isdir(models_dir):
        raise FileNotFoundError(f"모델 디렉토리를 찾을 수 없습니다: {models_dir}")

    pkl_files = [
        f for f in os.listdir(models_dir)
        if f.endswith(".pkl") and os.path.isfile(os.path.join(models_dir, f))
    ]
    if not pkl_files:
        raise FileNotFoundError("models 디렉토리에 .pkl 모델 파일이 없습니다.")

    latest = max(pkl_files)
    return os.path.join(models_dir, latest)


def normalize_json_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    중첩된 JSON 구조를 평탄화합니다.
    예: {'거래_정보': {'거래방식': '전세'}} -> '거래_정보.거래방식': '전세'
    """
    normalized_data = []
    
    for _, row in df.iterrows():
        flat_row = {}
        for col, value in row.items():
            if isinstance(value, dict):
                # 중첩된 딕셔너리를 평탄화
                for sub_key, sub_value in value.items():
                    flat_row[f"{col}.{sub_key}"] = sub_value
            else:
                flat_row[col] = value
        normalized_data.append(flat_row)
    
    return pd.DataFrame(normalized_data)


def run_prediction_on_file(model, json_path: str) -> pd.DataFrame:
    """
    단일 JSON 파일에 대해 예측을 수행하고 DataFrame으로 반환합니다.
    """
    if not os.path.exists(json_path):
        print(f"[WARN] JSON 파일을 찾을 수 없습니다: {json_path}")
        return pd.DataFrame()

    try:
        df_raw = pd.read_json(json_path)
    except ValueError:
        # 일부 JSON은 line-delimited 형태일 수 있음
        df_raw = pd.read_json(json_path, lines=True)

    # JSON 데이터 정규화 (중첩된 구조 평탄화)
    df_raw = normalize_json_data(df_raw)

    df_prepared = preprocess_from_dataframe(df_raw)
    if df_prepared.empty:
        print(f"[INFO] 전처리 후 남은 데이터가 없습니다: {json_path}")
        return pd.DataFrame()

    df_ml = build_features(df_prepared)
    if df_ml.empty:
        print(f"[INFO] 특성 생성 후 남은 데이터가 없습니다: {json_path}")
        return pd.DataFrame()

    # 예측
    X = df_ml.drop(columns=["평당가"])
    predictions = predict_model(model, X)

    result_df = df_prepared.copy()
    result_df["예측_평당_전세금"] = predictions
    result_df["예상_전세금"] = result_df["예측_평당_전세금"] * result_df["전용면적_평"]
    result_df["예상_전세금_억"] = result_df["예상_전세금"] / 10000
    result_df["출처파일"] = os.path.basename(json_path)

    return result_df


def save_prediction_outputs(result_df: pd.DataFrame, category: str, output_dir: str) -> Dict[str, str]:
    """
    예측 결과를 CSV/JSON/이미지로 저장하고 경로를 반환합니다.
    """
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    saved_paths = {}

    if result_df.empty:
        return saved_paths

    # CSV 저장
    csv_path = os.path.join(output_dir, f"predictions_{category}.csv")
    result_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    saved_paths["csv"] = csv_path

    # 요약 통계 JSON
    summary = {
        "category": category,
        "total_properties": int(len(result_df)),
        "avg_prediction_per_pyeong": float(result_df["예측_평당_전세금"].mean()),
        "avg_total_prediction_eok": float(result_df["예상_전세금_억"].mean()),
        "min_total_prediction_eok": float(result_df["예상_전세금_억"].min()),
        "max_total_prediction_eok": float(result_df["예상_전세금_억"].max()),
    }
    json_path = os.path.join(output_dir, f"summary_{category}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    saved_paths["summary_json"] = json_path

    # EDA용 간단한 그래프 저장 (타겟 분포, 구별 평균)
    setup_matplotlib_korean()
    plot_target_distribution(
        result_df,
        target="예측_평당_전세금",
        output_path=os.path.join(images_dir, f"{category}_01_평당가분포.png"),
        show=False,
    )
    plot_gu_average_price(
        result_df,
        target="예측_평당_전세금",
        output_path=os.path.join(images_dir, f"{category}_02_구별평균.png"),
        show=False,
    )

    return saved_paths


# =====================================================================
# 메인 실행부
# =====================================================================

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "..", "..", "..", "..", "data", "landData")

    json_files = {
        "빌라주택": os.path.join(data_dir, "00_통합_빌라주택.json"),
        "아파트": os.path.join(data_dir, "00_통합_아파트.json"),
        "오피스텔": os.path.join(data_dir, "00_통합_오피스텔.json"),
        "원투룸": os.path.join(data_dir, "00_통합_원투룸.json"),
    }

    models_dir = os.path.join(current_dir, "models")
    latest_model_path = load_latest_model(models_dir)
    model = load_model(latest_model_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_root = os.path.join(current_dir, "results", f"predict_run_{timestamp}")
    os.makedirs(results_root, exist_ok=True)

    all_results = []
    saved_summary = {}

    print("=" * 80)
    print("JSON 기반 전세 가격 예측 시작")
    print("=" * 80)

    for category, json_path in json_files.items():
        print(f"\n[{category}] {os.path.basename(json_path)} 처리 중...")
        result_df = run_prediction_on_file(model, json_path)

        if result_df.empty:
            print(f"  → 유효한 데이터가 없어 건너뜁니다.")
            continue

        saved_paths = save_prediction_outputs(
            result_df,
            category=category,
            output_dir=results_root,
        )

        all_results.append(result_df)
        saved_summary[category] = saved_paths

        print(f"  → 예측 완료 (총 {len(result_df)}건)")
        print(f"     CSV : {saved_paths.get('csv', '-')}")
        print(f"     JSON: {saved_paths.get('summary_json', '-')}")

    if not all_results:
        print("\n⚠️ 처리 가능한 데이터가 없었습니다. 스크립트를 종료합니다.")
        return

    # 전체 통합 결과 저장
    merged_df = pd.concat(all_results, ignore_index=True)
    merged_csv_path = os.path.join(results_root, "predictions_all_categories.csv")
    merged_df.to_csv(merged_csv_path, index=False, encoding="utf-8-sig")
    saved_summary["전체"] = {"csv": merged_csv_path}

    print("\n" + "=" * 80)
    print("✅ 모든 JSON 파일 예측 완료!")
    print("=" * 80)
    print(f"결과 폴더: {results_root}")
    for category, paths in saved_summary.items():
        print(f"  - {category}:")
        for key, path in paths.items():
            print(f"      • {key}: {path}")


if __name__ == "__main__":
    main()
