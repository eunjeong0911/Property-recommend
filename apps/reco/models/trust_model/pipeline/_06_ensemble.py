# _06_ensemble.py
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, f1_score


def ensemble(df):
    print("\n🎯 [5단계] 앙상블 & 최종 등급")

    df = df.copy()

    # rule_score를 0~1로 정규화
    rule_norm = (df["rule_score"] - df["rule_score"].min()) / (df["rule_score"].max() - df["rule_score"].min())
    
    # 앙상블 계산
    df["final_temperature"] = (
        rule_norm * 0.5 +
        df["clf_score"] * 0.5
    )

    # 최종 등급
    df["final_grade"] = pd.qcut(
        df["final_temperature"], 
        q=5, 
        labels=["D", "C", "B", "A", "S"],
        duplicates='drop'
    )
    
    print(f"   ✅ 최종 신뢰도 온도 생성 (Rule 50% + ML 50%)")
    print(f"   ✅ 최종 등급 분류 완료 (각 등급 20%씩)")

    return df


if __name__ == "__main__":
    df = pd.read_csv("results/temp.csv")
    df = ensemble(df)
