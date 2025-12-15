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

        # 0. 학습에 사용했던 train_df 다시 로드 (main.py와 동일)
        loader = DataLoader(base_dir=str(INTEREST_RATE_PATH.parent))
        train_df_raw, _ = loader.load_train_test()

        # 1. (총합)시장금리_및_대출금리 CSV 로드
        macro = pd.read_csv(INTEREST_RATE_PATH, encoding="utf-8-sig")
        # 현재 형태: 행 = 구분(CD/KORIBOR/기업대출/...), 열 = 2024.08, 2024.09 ...

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

        # 2. JSON df 에 연월 컬럼 만들기
        #    (JSON에는 계약 연월 정보가 없으므로, 일단 최신 연월로 통일)
        latest_month = macro_pivot["연월"].max()   # 예: '2025.10'
        df["연월"] = latest_month.replace(".", "-")  # 학습 CSV는 '2025-10' 형식

        # 3. 연월 기준으로 금리 컬럼 조인
        df = df.merge(macro_pivot, on="연월", how="left")

        # 4. 이후는 기존 로직 그대로: 타깃 생성 + 고급 FE
        train_df_raw = self.preprocessor.create_target(train_df_raw)
        df = self.preprocessor.create_target(
            df,
            train_stats={"gu_quantiles": self.preprocessor.train_gu_quantiles}
        )

        print("   - 타깃/가격지표 생성 완료")

        train_fe, df_fe = self.preprocessor.advanced_feature_engineering(
            train_df_raw,
            df
        )

        print(f"   - 고급 피처 생성 완료: {len(self.preprocessor.candidate_features)}개")
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

        # (후처리) 확률이 애매하면 적정(1)으로 강제
        max_proba = np.max(y_pred_proba, axis=1)
        threshold = 0.55

        uncertain = max_proba < threshold
        y_pred[uncertain] = 1

        n_total = len(y_pred)
        n_uncertain = uncertain.sum()
        print(f"[DEBUG] uncertain 개수: {n_uncertain} / {n_total} ({n_uncertain / n_total:.1%})")


        # 4) 결과 컬럼 추가
        df['예측_클래스'] = y_pred
        df['예측_영문'] = [CLASS_LABELS[c]['label'] for c in y_pred]
        df['예측_한글'] = [CLASS_LABELS[c]['label_kr'] for c in y_pred]
        
        # 확률 추가
        df['저렴_확률'] = y_pred_proba[:, 0]
        df['적정_확률'] = y_pred_proba[:, 1]
        df['비쌈_확률'] = y_pred_proba[:, 2]
        
        print(f"✅ 예측 완료: {len(df)}개 매물")
        
        # 예측 결과 요약
        print("\n📊 예측 결과 요약:")
        class_counts = df['예측_한글'].value_counts()
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
