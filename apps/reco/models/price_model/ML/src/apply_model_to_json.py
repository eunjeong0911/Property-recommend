"""
월세 매물 가격 분류 적용 스크립트
저장된 모델을 JSON 데이터에 적용하여 DB에 저장
"""
import argparse
import pickle
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

from json_data_parser import JSONDataParser
from db_manager import DatabaseManager
from preprocessor import PriceDataPreprocessor
from data_loader import DataLoader
from config import (
    JSON_DATA_DIR, 
    MODEL_PATH, 
    INTEREST_RATE_PATH,
    CLASS_LABELS
)

class PriceClassifier:
    
    """가격 분류 파이프라인"""
    
    def __init__(self, model_path: str):
        """
        Args:
            model_path: 저장된 모델 경로
        """
        self.model_path = Path(model_path)
        self.model = None
        self.preprocessor = None
        self.interest_rate_df = None
        
    def load_model(self):
        """저장된 모델 로드"""
        print(f"\n🚚 모델 로딩: {self.model_path}")

        with open(self.model_path, 'rb') as f:
            saved_data = pickle.load(f)

        # trainer.save_model() 구조에 맞게 'model' 키 사용
        if 'model' in saved_data:
            self.model = saved_data['model']
        elif 'best_model' in saved_data:  # 혹시 예전 포맷도 지원하고 싶다면
            self.model = saved_data['best_model']
        else:
            raise KeyError("저장된 파일에 'model' 키가 없습니다. 저장 로직을 확인하세요.")

        # 새로 전처리기 생성
        self.preprocessor = PriceDataPreprocessor()

        # (선택적) LabelEncoder 복원 – 현재 저장 구조에는 없지만, 추가되면 사용
        if 'label_encoders' in saved_data:
            self.preprocessor.label_encoders = saved_data['label_encoders']

        # (선택적) train 구간 분위수 복원 – 현재 저장 구조에는 없지만, 추가되면 사용
        if 'train_gu_quantiles' in saved_data:
            self.preprocessor.train_gu_quantiles = saved_data['train_gu_quantiles']

        print(f"✅ 모델 로드 완료: {saved_data.get('model_name', 'Unknown')}")

        
    def load_interest_rate(self):
        """금리 데이터 로드"""
        print(f"\n📊 금리 데이터 로딩: {INTEREST_RATE_PATH}")
        
        self.interest_rate_df = pd.read_csv(
            INTEREST_RATE_PATH, 
            encoding='utf-8-sig'
        )
        
        # 연월 형식으로 변환 (2024.08 -> 2024-08)
        columns = [col for col in self.interest_rate_df.columns if col != '구분']
        
        # 최신 금리 데이터 사용 (마지막 컬럼)
        latest_month = columns[-1]
        print(f"✅ 최신 금리 데이터: {latest_month}")
        
        # 금리 데이터를 딕셔너리로 변환
        rate_dict = {}
        for _, row in self.interest_rate_df.iterrows():
            rate_name = row['구분']
            rate_value = row[latest_month]
            if pd.notna(rate_value):
                rate_dict[rate_name] = float(rate_value)
        
        return rate_dict, latest_month
    
    from config import INTEREST_RATE_PATH  # 이미 있으면 재사용

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        print("\n[Step] 데이터 전처리 시작")

        # === (1) JSON 원본 컬럼 상태 점검 ===
        print("\n[DEBUG] 원본 JSON 컬럼 목록")
        print(df.columns.tolist())

        # create_target에서 price_column을 계산할 때 사용하는 핵심 컬럼들
        key_cols = [
            self.preprocessor.price_column,  # 평당 환산보증금(나중에 만들어질 컬럼)
            "보증금(만원)",
            "임대료(만원)",
            "임대면적",   
            "기준금리"                    # INTEREST_RATE와 merge 후 들어가는 컬럼
        ]

        existing = [c for c in key_cols if c in df.columns]

        print("\n[DEBUG] 핵심 컬럼 존재 여부")
        print("  필요:", key_cols)
        print("  실제 존재:", existing)

        if existing:
            print("\n[DEBUG] 핵심 컬럼 null 비율")
            print(df[existing].isna().mean())

            print("\n[DEBUG] 핵심 컬럼 상위 5개 예시")
            print(df[existing].head())
        else:
            print("\n[DEBUG] 핵심 컬럼이 하나도 없습니다. JSON 스키마를 먼저 확인하세요.")

        # 0. 학습에 사용했던 train_df 다시 로드 (main.py와 동일)
        loader = DataLoader(base_dir=str(INTEREST_RATE_PATH.parent))
        train_df_raw, _ = loader.load_train_test()

        # 1. (총합)시장금리_및_대출금리 CSV 로드
        macro = pd.read_csv(INTEREST_RATE_PATH, encoding="utf-8-sig")
        
        # 최신 기준금리 한 값을 가져와서 JSON 전체에 공통으로 사용
        rate_dict, latest_month = self.load_interest_rate()
        # rate_dict: {"CD": ..., "KORIBOR": ..., "기준금리": ..., ...} 이런 형태일 가능성이 큼
        if "기준금리" in rate_dict:
            base_rate = rate_dict["기준금리"]
        else:
            # 키 이름이 다를 수 있으므로, 첫 값 하나를 fallback으로 사용
            base_rate = list(rate_dict.values())[0]

        # JSON df 에 기준금리 / 적용이자율 채우기
        df["기준금리"] = base_rate
        df["적용이자율"] = (df["기준금리"] + 2.0) / 100.0

        # wide → long → 다시 pivot 해서
        # 연월별 한 줄 + 금리 컬럼들 형태로 만들기
        macro_long = macro.melt(
            id_vars="구분", var_name="연월", value_name="값"
        )
        macro_pivot = (
            macro_long
            .pivot(index="연월", columns="구분", values="값")
            .reset_index()
        )
        # macro_pivot.columns:
        # ['연월', 'CD', 'KORIBOR', '기업대출', '전세자금대출', '변동형주택담보대출',
        #  '무담보콜금리', '기준금리', '소비자물가']
        month_col = macro_pivot.columns[0] 
        # 2-1. JSON df 에 월 컬럼 만들기
        latest_month = macro_pivot[month_col].max()   # 예: '2025.10'
        df[month_col] = latest_month                  # 형식을 그대로 맞춰서 사용

        # 3. 월 기준으로 금리 컬럼 조인
        df = df.merge(macro_pivot, on=month_col, how="left")

        df["기준금리"] = 2.5
        # 4. 후처리 + 기존 로직 그대로 사용
                # 4. 글로벌 기준 가격_클래스 생성 (이미 있던 코드)
        train_df_raw = self.preprocessor.create_target(train_df_raw)
        df = self.preprocessor.create_target(
            df,
            train_stats={"gu_quantiles": self.preprocessor.train_gu_quantiles}
        )
        print("   - 가격_클래스(글로벌 기준) 생성 완료")

        # 4-1. JSON 내부 분포만 가지고 로컬 룰 기반 타깃 생성
        df_local = self.preprocessor.create_target(df.copy(), train_stats=None)

        # 디버그 코드 추가 
        print("\n[DEBUG] 로컬 타깃 원시 분포 (가격_클래스)")
        print(df_local[self.preprocessor.target_name].value_counts(dropna=False))

        print("\n[DEBUG] 로컬 타깃 price_column NaN 비율")
        print(df_local[self.preprocessor.price_column].isna().mean())

        # ===== 여기부터 추가 디버그 코드 =====
        # 환산보증금_평당가를 계산할 때 직접 쓰는 컬럼들 점검
        check_cols = [
            "보증금(만원)",
            "임대료(만원)",
            "적용이자율",         # (기준금리 + 2) / 100 으로 만들어지는 컬럼
            "환산보증금(만원)",   # 보증금 + 월세 환산
            "전용평수",           # 임대면적/전용면적에서 파생
            self.preprocessor.price_column,  # "환산보증금_평당가"
        ]
        existing = [c for c in check_cols if c in df_local.columns]

        print("\n[DEBUG] 로컬 타깃 - 가격 관련 컬럼 존재 여부")
        print("  필요:", check_cols)
        print("  실제 존재:", existing)

        if existing:
            print("\n[DEBUG] 로컬 타깃 - 가격 관련 컬럼 NaN 비율")
            print(df_local[existing].isna().mean())

            print("\n[DEBUG] 로컬 타깃 - 가격 관련 컬럼 상위 5개 예시")
            print(df_local[existing].head())
        else:
            print("\n[DEBUG] 로컬 타깃에 가격 관련 컬럼이 하나도 없습니다.")

        local_classes = df_local[self.preprocessor.target_name].to_numpy()
        local_label_en = [CLASS_LABELS[c]["label"] for c in local_classes]
        local_label_kr = [CLASS_LABELS[c]["label_kr"] for c in local_classes]


        train_fe, df_fe = self.preprocessor.advanced_feature_engineering(
            train_df_raw,
            df
        )

        print(f"   - 고급 피처 생성 완료: {len(self.preprocessor.candidate_features)}개")

        # 4-2. 로컬 룰 기반 레이블을 최종 DF에 붙이기 (모델 입력에는 사용하지 않음)
        df_fe["local_price_class"] = local_classes
        df_fe["local_price_label"] = local_label_en
        df_fe["local_price_label_kr"] = local_label_kr

        return df_fe


    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        모델 예측 수행
        
        Args:
            df: 전처리된 DataFrame
            
        Returns:
            예측 결과가 추가된 DataFrame
        """
        print("\n🔮 예측 수행 중...")
        
        # 1) 피처 선택
        X = df[self.preprocessor.candidate_features].copy()

        # 2) Tree용 전처리 (Label Encoding)
        empty_df = pd.DataFrame(columns=X.columns)
        _, _, X_transformed = self.preprocessor.prepare_tree_features(
            empty_df, empty_df, X
        )

        # 3) 모델이 기대하는 피처 수에 맞춰 정렬
        X_arr = X_transformed.values
        n_model_features = getattr(self.model, "n_features_in_", X_arr.shape[1])

        if X_arr.shape[1] != n_model_features:
            diff = n_model_features - X_arr.shape[1]
            if diff > 0:
                # 부족한 피처는 0으로 패딩 (새로운 dummy 피처)
                pad = np.zeros((X_arr.shape[0], diff))
                X_arr = np.hstack([X_arr, pad])
            else:
                # 피처가 더 많으면 앞의 n_model_features 개만 사용
                X_arr = X_arr[:, :n_model_features]

        # 3) 예측
        y_pred_proba = self.model.predict_proba(X_arr)

        # 기본 예측: 가장 확률이 큰 클래스
        y_pred = np.argmax(y_pred_proba, axis=1)

        # 애매한 확률이 있으면 적정(1)으로
        max_proba = np.max(y_pred_proba, axis=1)
        threshold = 0.7
        
        uncertain = max_proba < threshold
        y_pred[uncertain] = 1

        n_total = len(y_pred)
        n_uncertain = uncertain.sum()
        print(f"[DEBUG] uncertain 개수: {n_uncertain} / {n_total} ({n_uncertain / n_total:.1%})")

        # 4) 결과 컬럼 추가
        df['예측_클래스'] = y_pred
        df['예측_레이블'] = [CLASS_LABELS[c]['label'] for c in y_pred]
        df['예측_레이블_한글'] = [CLASS_LABELS[c]['label_kr'] for c in y_pred]
        
        # 확률 추가
        df['저렴_확률'] = y_pred_proba[:, 0]
        df['적정_확률'] = y_pred_proba[:, 1]
        df['비쌈_확률'] = y_pred_proba[:, 2]
        
        print(f"✅ 예측 완료: {len(df)}개 매물")
        
        # 예측 결과 요약
        print("\n📊 예측 결과 요약:")
        class_counts = df['예측_클래스'].value_counts()
        for label, count in class_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   - {label}: {count}개 ({percentage:.1f}%)")
        
        return df
    
    def run(self, json_dir: str, save_to_db: bool = True) -> pd.DataFrame:
        """
        전체 파이프라인 실행
        
        Args:
            json_dir: JSON 파일 디렉토리
            save_to_db: DB 저장 여부
            
        Returns:
            예측 결과 DataFrame
        """
        print("\n" + "=" * 60)
        print("🚀 월세 매물 가격 분류 시작")
        print("=" * 60)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 모델 로드
        self.load_model()
        
        # 2. JSON 데이터 로드 및 파싱
        parser = JSONDataParser()
        df = parser.load_and_parse(json_dir)
        
        if df.empty:
            print("⚠️  처리할 데이터가 없습니다.")
            return df
        
        # 3. 데이터 전처리
        df_processed = self.prepare_data(df)
        
        # 4. 예측
        df_result = self.predict(df_processed)

        # 4-1. 예측 vs 로컬 룰 분포 / 교차표 디버그
        if "local_price_label_kr" in df_result.columns and "예측_레이블_한글" in df_result.columns:
            print("\n[DEBUG] 로컬 룰 기준 클래스 분포")
            print(df_result["local_price_label_kr"].value_counts(normalize=True))

            print("\n[DEBUG] 모델 예측 기준 클래스 분포")
            print(df_result["예측_레이블_한글"].value_counts(normalize=True))

            print("\n[DEBUG] 로컬 룰 vs 모델 예측 교차표 (행 기준 정규화)")
            cross = pd.crosstab(
                df_result["local_price_label_kr"],
                df_result["예측_레이블_한글"],
                normalize="index"
            )
            print(cross)

        # 5. DB 저장
        if save_to_db:
            print("\n💾 데이터베이스 저장 중...")
            db = DatabaseManager()
            try:
                db.connect()
                db.create_table()
                db.save_results(df_result)
                
                # 통계 조회
                stats = db.get_statistics()
                if stats:
                    print("\n📈 데이터베이스 통계:")
                    print(f"   - 전체 레코드 수: {stats.get('total_count', 0)}개")
                    print(f"   - 클래스별 분포:")
                    for label, count in stats.get('class_distribution', {}).items():
                        print(f"     • {label}: {count}개")
                
            except Exception as e:
                print(f"❌ DB 저장 중 오류: {e}")
            finally:
                db.close()
        
        print("\n" + "=" * 60)
        print("✅ 모든 작업 완료!")
        print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")
        
        return df_result


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="월세 매물 가격 분류 (저렴/적정/비쌈)"
    )
    parser.add_argument(
        "--json_dir",
        type=str,
        default=str(JSON_DATA_DIR),
        help="JSON 파일 디렉토리"
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default=str(MODEL_PATH),
        help="저장된 모델 경로"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="DB 저장 없이 예측만 수행"
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default=None,
        help="결과를 CSV로 저장할 경로 (선택사항)"
    )
    
    args = parser.parse_args()
    
    # 분류기 실행
    classifier = PriceClassifier(args.model_path)
    results_df = classifier.run(
        json_dir=args.json_dir,
        save_to_db=not args.dry_run
    )
    
    # CSV 저장 (옵션)
    if args.output_csv and not results_df.empty:
        output_path = Path(args.output_csv)
        results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"📄 결과 CSV 저장: {output_path}")


if __name__ == "__main__":
    main()
