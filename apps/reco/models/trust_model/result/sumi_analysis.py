"""
sumi 폴더 파이프라인 실행 및 결과 분석
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import sys
import os

# 프로젝트 루트 설정
project_root = Path("c:/dev/study/eunjeong/SKN18-FINAL-1TEAM")
os.chdir(project_root)

# sumi 폴더 경로 추가
sumi_dir = project_root / "apps/reco/models/trust_model/pipeline/sumi"
sys.path.insert(0, str(sumi_dir))

RESULT_DIR = project_root / "apps/reco/models/trust_model/result/1회차"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# sumi 모듈 import
from _00_load_data import load_processed_office_data
import _01_targer_engineering as target_eng
from _02_feature_engineering import main as feature_eng


def main():
    print("="*70)
    print(" sumi 파이프라인 분석")
    print("="*70)
    
    # 1. 데이터 로드
    print("\n[1] 데이터 로드...")
    df = load_processed_office_data()
    print(f"   로드: {len(df)}개")
    
    # 2. 타겟 생성
    print("\n[2] 타겟 생성 (베이지안)...")
    df = target_eng.main(df)
    
    # 3. 피처 생성
    print("\n[3] 피처 생성...")
    df_enriched, X, feature_names = feature_eng(df)
    y = df_enriched["신뢰등급"].astype(int)
    
    print(f"\n데이터: {len(df_enriched)}개, 피처: {len(feature_names)}개")
    print(f"등급 분포: {dict(y.value_counts().sort_index())}")
    
    # 보고서 작성
    report = ["# sumi 파이프라인 분석\n\n"]
    report.append(f"- 데이터: {len(df_enriched)}개\n")
    report.append(f"- 피처: {len(feature_names)}개\n")
    report.append(f"- 등급 분포: {dict(y.value_counts().sort_index())}\n\n")
    
    # 타겟 분포
    report.append("## 타겟 분포\n\n")
    dist = y.value_counts().sort_index()
    report.append("| 등급 | 개수 | 비율 |\n|------|------|------|\n")
    for g in dist.index:
        report.append(f"| {g} | {dist[g]} | {dist[g]/len(y)*100:.1f}% |\n")
    
    # 피처 목록
    report.append("\n## 피처 목록\n\n")
    for i, f in enumerate(feature_names, 1):
        report.append(f"{i}. {f}\n")
    
    # 저장
    with open(RESULT_DIR / "sumi_분석결과.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n저장 완료: {RESULT_DIR / 'sumi_분석결과.md'}")


if __name__ == "__main__":
    main()
