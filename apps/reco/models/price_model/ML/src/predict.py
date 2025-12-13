"""
저장된 모델을 사용한 예측 스크립트
"""
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Union

from trainer import ModelTrainer


class PricePredictor:
    """월세 실거래가 예측 클래스"""

    def __init__(self, model_path: str):
        """
        Args:
            model_path: 저장된 모델 파일 경로 (.pkl)
        """
        self.model_bundle = ModelTrainer.load_model(model_path)
        self.model = self.model_bundle["model"]
        self.preprocessor = self.model_bundle["preprocessor"]
        self.model_name = self.model_bundle["model_name"]

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        예측 수행 (로그 스케일 역변환 포함)

        Args:
            X: 예측할 데이터 (피처 엔지니어링 완료된 상태)

        Returns:
            예측 평당가 (만원)
        """
        # 전처리 적용
        X_transformed = self.preprocessor.transform(X)

        # 예측 (로그 스케일)
        pred_log = self.model.predict(X_transformed)

        # 로그 역변환
        pred_real = np.expm1(pred_log)

        return pred_real

    def predict_from_csv(
        self,
        csv_path: str,
        output_path: str = None
    ) -> pd.DataFrame:
        """
        CSV 파일로부터 예측 수행

        Args:
            csv_path: 예측할 데이터 CSV 파일 경로
            output_path: 예측 결과 저장 경로 (None이면 저장하지 않음)

        Returns:
            예측 결과가 추가된 데이터프레임
        """
        # 데이터 로드
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        print(f"📂 데이터 로드 완료: {df.shape}")

        # 예측
        predictions = self.predict(df)

        # 결과 추가
        df["예측_평당가"] = predictions

        # 보증금, 월세가 있으면 예측 보증금/월세 계산
        if "전용평수" in df.columns:
            df["예측_환산보증금"] = df["예측_평당가"] * df["전용평수"]

        # 저장
        if output_path:
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"✅ 예측 결과 저장: {output_path}")

        return df


def main():
    """예측 스크립트 메인 함수"""
    parser = argparse.ArgumentParser(
        description="저장된 모델로 월세 실거래가 예측"
    )
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="저장된 모델 파일 경로 (.pkl)"
    )
    parser.add_argument(
        "--input_csv",
        type=str,
        required=True,
        help="예측할 데이터 CSV 파일 경로"
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default=None,
        help="예측 결과 저장 CSV 파일 경로"
    )

    args = parser.parse_args()

    # 예측기 초기화
    predictor = PricePredictor(args.model_path)

    # 예측 수행
    result_df = predictor.predict_from_csv(
        csv_path=args.input_csv,
        output_path=args.output_csv
    )

    # 결과 미리보기
    print("\n📊 예측 결과 미리보기:")
    print(result_df.head(10))

    if "예측_평당가" in result_df.columns:
        print(f"\n평균 예측 평당가: {result_df['예측_평당가'].mean():.2f} 만원")
        print(f"예측 범위: {result_df['예측_평당가'].min():.2f} ~ {result_df['예측_평당가'].max():.2f} 만원")


if __name__ == "__main__":
    main()
