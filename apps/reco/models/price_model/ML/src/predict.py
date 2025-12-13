"""
저장된 모델을 사용한 예측 스크립트 - 3중 분류 (저렴/적정/비쌈)
"""
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Union, Dict, List

from trainer import ModelTrainer


class PricePredictor:
    """월세 가격 분류 예측 클래스 (저렴/적정/비쌈)"""

    # 클래스 레이블 정의
    CLASS_LABELS = {
        0: {"label": "UNDERPRICED", "label_kr": "저렴"},
        1: {"label": "FAIR", "label_kr": "적정"},
        2: {"label": "OVERPRICED", "label_kr": "비쌈"}
    }

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
        클래스 예측 수행

        Args:
            X: 예측할 데이터 (피처 엔지니어링 완료된 상태)

        Returns:
            예측 클래스 레이블 (0: 저렴, 1: 적정, 2: 비쌈)
        """
        # 전처리 적용 (Tree 모델은 preprocessor가 None일 수 있음)
        if self.preprocessor is not None:
            X_transformed = self.preprocessor.transform(X)
        else:
            X_transformed = X.values if hasattr(X, 'values') else X

        # 예측
        pred_class = self.model.predict(X_transformed)

        return pred_class

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        클래스별 확률 예측

        Args:
            X: 예측할 데이터 (피처 엔지니어링 완료된 상태)

        Returns:
            예측 확률 배열 (shape: [n_samples, 3])
        """
        # 전처리 적용
        if self.preprocessor is not None:
            X_transformed = self.preprocessor.transform(X)
        else:
            X_transformed = X.values if hasattr(X, 'values') else X

        # 확률 예측
        pred_proba = self.model.predict_proba(X_transformed)

        return pred_proba

    def predict_with_details(self, X: pd.DataFrame, listing_ids: List[str] = None) -> List[Dict]:
        """
        상세 예측 결과 반환 (JSON 형태)

        Args:
            X: 예측할 데이터
            listing_ids: 매물 ID 리스트 (optional)

        Returns:
            예측 결과 리스트 (각 항목은 딕셔너리)
        """
        # 예측
        pred_class = self.predict(X)
        pred_proba = self.predict_proba(X)

        # 결과 생성
        results = []
        for i in range(len(pred_class)):
            class_id = int(pred_class[i])
            class_info = self.CLASS_LABELS[class_id]

            # 최대 확률 (confidence)
            confidence = float(pred_proba[i][class_id])

            # 예측 결과 딕셔너리
            result = {
                "listing_id": listing_ids[i] if listing_ids else f"listing_{i}",
                "price_class": class_info["label"],
                "class_label_kr": class_info["label_kr"],
                "class_score": round(confidence, 4),
                "confidence": round(confidence, 4),
                "reference_period": "최근 6개월",
                "explain": {
                    "main_factors": self._get_explanation(class_id, X.iloc[i] if hasattr(X, 'iloc') else None)
                }
            }

            results.append(result)

        return results

    def _get_explanation(self, class_id: int, features: pd.Series = None) -> List[str]:
        """
        예측 결과에 대한 간단한 설명 생성

        Args:
            class_id: 예측 클래스 ID
            features: 피처 값

        Returns:
            설명 리스트
        """
        # 기본 설명
        if class_id == 0:  # 저렴
            return [
                "동일 면적 대비 월세 낮음",
                "최근 금리 상승기 대비 보증금 안정",
                "자치구 내 하위 33% 구간"
            ]
        elif class_id == 1:  # 적정
            return [
                "동일 면적 대비 월세 적정",
                "자치구 내 중간 구간 (33~67%)",
                "시장 평균 범위 내"
            ]
        else:  # 비쌈
            return [
                "동일 면적 대비 월세 높음",
                "자치구 내 상위 33% 구간",
                "시장 평균 대비 높은 수준"
            ]

    def predict_from_json(
        self,
        json_path: str,
        output_path: str = None,
        output_json: str = None
    ) -> pd.DataFrame:
        """
        json 파일로부터 예측 수행

        Args:
            json_path: 예측할 데이터 json 파일 경로
            output_path: 예측 결과 CSV 저장 경로 (None이면 저장하지 않음)
            output_json: 예측 결과 JSON 저장 경로 (None이면 저장하지 않음)

        Returns:
            예측 결과가 추가된 데이터프레임
        """
        # 데이터 로드
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.json_normalize(data)

        print(f"📂 데이터 로드 완료: {df.shape}")

        # 예측
        predictions = self.predict(df)
        predictions_proba = self.predict_proba(df)

        # 결과 추가
        df["예측_클래스"] = predictions
        df["예측_레이블"] = df["예측_클래스"].map(lambda x: self.CLASS_LABELS[x]["label"])
        df["예측_레이블_한글"] = df["예측_클래스"].map(lambda x: self.CLASS_LABELS[x]["label_kr"])

        # 각 클래스별 확률
        df["확률_저렴"] = predictions_proba[:, 0]
        df["확률_적정"] = predictions_proba[:, 1]
        df["확률_비쌈"] = predictions_proba[:, 2]

        # confidence (예측 클래스의 확률)
        df["confidence"] = [predictions_proba[i, pred] for i, pred in enumerate(predictions)]

        # CSV 저장
        if output_path:
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"✅ 예측 결과 CSV 저장: {output_path}")

        # JSON 저장 (상세 결과)
        if output_json:
            listing_ids = df.get("listing_id", [f"listing_{i}" for i in range(len(df))]).tolist()
            detailed_results = self.predict_with_details(df, listing_ids)

            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(detailed_results, f, ensure_ascii=False, indent=2)
            print(f"✅ 예측 결과 JSON 저장: {output_json}")

        return df


def main():
    """예측 스크립트 메인 함수"""
    parser = argparse.ArgumentParser(
        description="저장된 모델로 월세 가격 분류 예측 (저렴/적정/비쌈)"
    )
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="저장된 모델 파일 경로 (.pkl)"
    )
    parser.add_argument(
        "--input_json",
        type=str,
         default="C:/dev/SKN18-FINAL-1TEAM/data/RDB/land/00_통합_빌라주택.json",
        help="예측할 데이터 json 파일 경로"
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default=None,
        help="예측 결과 저장 CSV 파일 경로"
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default=None,
        help="예측 결과 저장 JSON 파일 경로"
    )

    args = parser.parse_args()

    # 예측기 초기화
    predictor = PricePredictor(args.model_path)
    

    # 예측 수행
    result_df = predictor.predict_from_json(
        json_path=args.input_json, 
        output_json=args.output_json
    )

    # 결과 미리보기
    print("\n📊 예측 결과 미리보기:")
    print(result_df.head(10))

    # 클래스 분포 출력
    if "예측_레이블_한글" in result_df.columns:
        print("\n📈 예측 클래스 분포:")
        class_counts = result_df["예측_레이블_한글"].value_counts()
        for class_name, count in class_counts.items():
            pct = count / len(result_df) * 100
            print(f"   - {class_name}: {count:,}개 ({pct:.1f}%)")

        print(f"\n평균 confidence: {result_df['confidence'].mean():.4f}")


if __name__ == "__main__":
    main()
