"""
모델 학습 및 평가 모듈
"""
import warnings
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from typing import Dict, Tuple, Any
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error,
)
from lightgbm import early_stopping, log_evaluation

warnings.filterwarnings("ignore")


class ModelTrainer:
    """모델 학습 및 평가 클래스"""

    def __init__(self):
        self.results = []
        self.best_model_name = None
        self.best_model = None
        self.models = None
        self.X_train = None
        self.X_val = None
        self.X_test = None
        self.feature_names = None

    @staticmethod
    def eval_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float, float]:
        """
        평가 지표 계산

        Args:
            y_true: 실제값
            y_pred: 예측값

        Returns:
            (MAE, RMSE, MAPE, R2)
        """
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = mse ** 0.5
        mape = mean_absolute_percentage_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        return mae, rmse, mape, r2

    def train_models(
        self,
        models: Dict[str, Any],
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: list = None,
    ) -> pd.DataFrame:
        """
        모델 학습 및 평가

        Args:
            models: 모델 딕셔너리
            X_train: 학습 데이터 (전처리 완료)
            y_train: 학습 타깃 (로그 스케일)
            X_val: 검증 데이터
            y_val: 검증 타깃 (로그 스케일)
            X_test: 테스트 데이터
            y_test: 테스트 타깃 (로그 스케일)
            feature_names: 피처 이름 리스트 (SHAP 분석용)

        Returns:
            결과 데이터프레임
        """
        self.results = []
        self.models = models
        self.X_train = X_train
        self.X_val = X_val
        self.X_test = X_test
        self.feature_names = feature_names

        for name, reg in models.items():
            print(f"\n{'=' * 60}")
            print(f"🚀 학습 중: {name}")
            print(f"{'=' * 60}")

            # 1) 학습 (TARGET_LOG 기준, early_stopping 사용)
            if name == "XGBoost":
                reg.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    verbose=200,
                )
            else:  # LightGBM
                reg.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    callbacks=[
                        early_stopping(stopping_rounds=50, verbose=True),
                        log_evaluation(period=200)
                    ],
                )

            # 2) 로그 스케일 예측값
            pred_tr_log = reg.predict(X_train)
            pred_val_log = reg.predict(X_val)
            pred_test_log = reg.predict(X_test)

            # 3) 로그 역변환
            y_tr_real = np.expm1(y_train)
            y_val_real = np.expm1(y_val)
            y_test_real = np.expm1(y_test)

            pred_tr_real = np.expm1(pred_tr_log)
            pred_val_real = np.expm1(pred_val_log)
            pred_test_real = np.expm1(pred_test_log)

            # 4) 원 스케일에서 지표 계산
            mae_tr, rmse_tr, mape_tr, r2_tr = self.eval_metrics(y_tr_real, pred_tr_real)
            mae_val, rmse_val, mape_val, r2_val = self.eval_metrics(y_val_real, pred_val_real)
            mae_te, rmse_te, mape_te, r2_te = self.eval_metrics(y_test_real, pred_test_real)

            # 5) 결과 저장
            self.results.append({
                "model": name,
                "R2_train": r2_tr,
                "MAE_train": mae_tr,
                "RMSE_train": rmse_tr,
                "MAPE_train": mape_tr,
                "R2_val": r2_val,
                "MAE_val": mae_val,
                "RMSE_val": rmse_val,
                "MAPE_val": mape_val,
                "R2_test": r2_te,
                "MAE_test": mae_te,
                "RMSE_test": rmse_te,
                "MAPE_test": mape_te,
            })

            # 6) 결과 출력
            print(f"\n📈 [{name}] 성능 지표 (원 스케일):")
            print(f"   [Train] R²: {r2_tr:.4f} | MAE: {mae_tr:.3f} | RMSE: {rmse_tr:.3f} | MAPE: {mape_tr * 100:.2f}%")
            print(f"   [Val]   R²: {r2_val:.4f} | MAE: {mae_val:.3f} | RMSE: {rmse_val:.3f} | MAPE: {mape_val * 100:.2f}%")
            print(f"   [Test]  R²: {r2_te:.4f} | MAE: {mae_te:.3f} | RMSE: {rmse_te:.3f} | MAPE: {mape_te * 100:.2f}%")

        # 결과 정리
        results_df = pd.DataFrame(self.results)
        results_df = results_df.sort_values("R2_test", ascending=False)

        # 최고 성능 모델 저장
        self.best_model_name = results_df.iloc[0]["model"]
        self.best_model = models[self.best_model_name]
        best_r2 = results_df.iloc[0]["R2_test"]

        print(f"\n{'=' * 60}")
        print(f"📊 전체 모델 비교 (Test R² 기준)")
        print(f"{'=' * 60}")
        print(results_df.to_string(index=False))
        print(f"\n🏆 최고 성능 모델: {self.best_model_name} (Test R² = {best_r2:.4f})")

        return results_df

    def save_model(
        self,
        preprocessor: Any,
        output_dir: str = "./models",
        model_filename: str = None
    ) -> str:
        """
        학습된 모델과 전처리기를 pkl 파일로 저장

        Args:
            preprocessor: 전처리 파이프라인
            output_dir: 저장 디렉토리
            model_filename: 저장할 파일명 (None이면 자동 생성)

        Returns:
            저장된 파일 경로
        """
        if self.best_model is None:
            raise ValueError("학습된 모델이 없습니다. train_models()를 먼저 실행하세요.")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if model_filename is None:
            model_filename = f"price_model_{self.best_model_name.lower()}.pkl"

        full_path = output_path / model_filename

        # 모델과 전처리기를 함께 저장
        model_bundle = {
            "model": self.best_model,
            "preprocessor": preprocessor,
            "model_name": self.best_model_name,
        }

        with open(full_path, "wb") as f:
            pickle.dump(model_bundle, f)

        print(f"\n✅ 모델 저장 완료: {full_path}")
        print(f"   - 모델: {self.best_model_name}")
        print(f"   - 파일 크기: {full_path.stat().st_size / 1024 / 1024:.2f} MB")

        return str(full_path)

    @staticmethod
    def load_model(model_path: str) -> Dict[str, Any]:
        """
        저장된 모델 로드

        Args:
            model_path: 모델 파일 경로

        Returns:
            모델 번들 딕셔너리
        """
        with open(model_path, "rb") as f:
            model_bundle = pickle.load(f)

        print(f"✅ 모델 로드 완료: {model_path}")
        print(f"   - 모델: {model_bundle['model_name']}")

        return model_bundle

    def create_shap_explainer(
        self,
        model_name: str = None,
        background_size: int = 100
    ):
        """
        SHAP Explainer 생성

        Args:
            model_name: 분석할 모델 이름 (None이면 best_model 사용)
            background_size: 배경 데이터 크기

        Returns:
            ModelExplainer 객체
        """
        from explainer import ModelExplainer

        if model_name is None:
            if self.best_model is None:
                raise ValueError("학습된 모델이 없습니다. train_models()를 먼저 실행하세요.")
            model = self.best_model
            model_name = self.best_model_name
        else:
            if self.models is None or model_name not in self.models:
                raise ValueError(f"모델 '{model_name}'을 찾을 수 없습니다.")
            model = self.models[model_name]

        if self.X_train is None:
            raise ValueError("학습 데이터가 저장되지 않았습니다. train_models()를 먼저 실행하세요.")

        # Explainer 생성
        explainer = ModelExplainer(
            model=model,
            model_name=model_name,
            feature_names=self.feature_names
        )

        # TreeExplainer 생성
        explainer.create_explainer(
            X_background=self.X_train,
            background_size=background_size
        )

        return explainer

    def analyze_shap(
        self,
        model_name: str = None,
        data_type: str = "test",
        max_samples: int = 1000,
        output_dir: str = "./shap_plots",
        save_plots: bool = True
    ):
        """
        SHAP 분석 실행

        Args:
            model_name: 분석할 모델 이름 (None이면 best_model 사용)
            data_type: 분석할 데이터 ("train", "val", "test")
            max_samples: 분석할 최대 샘플 수
            output_dir: 플롯 저장 디렉토리
            save_plots: 플롯 저장 여부

        Returns:
            ModelExplainer 객체
        """
        print(f"\n{'=' * 70}")
        print(f"🔍 SHAP 분석 시작")
        print(f"{'=' * 70}")

        # Explainer 생성
        explainer = self.create_shap_explainer(model_name=model_name)

        # 분석할 데이터 선택
        if data_type == "train":
            X = self.X_train
        elif data_type == "val":
            X = self.X_val
        elif data_type == "test":
            X = self.X_test
        else:
            raise ValueError(f"data_type은 'train', 'val', 'test' 중 하나여야 합니다. 입력값: {data_type}")

        print(f"   - 분석 데이터: {data_type}")
        print(f"   - 데이터 크기: {X.shape}")
        print(f"   - 최대 샘플 수: {max_samples}")

        # SHAP values 계산
        shap_values, X_sample = explainer.compute_shap_values(
            X=X,
            max_samples=max_samples
        )

        # 플롯 저장
        if save_plots:
            explainer.save_all_plots(
                X=X_sample,
                output_dir=output_dir,
                max_display=20,
                sample_indices=[0, 1, 2]
            )

        print(f"\n{'=' * 70}")
        print(f"✅ SHAP 분석 완료!")
        print(f"{'=' * 70}")

        return explainer
