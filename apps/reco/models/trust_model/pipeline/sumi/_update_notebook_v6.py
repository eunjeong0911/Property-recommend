import nbformat
from nbformat.v4 import new_markdown_cell, new_code_cell
import os

# Define file paths
notebook_path = r"c:/dev/study/eunjeong/SKN18-FINAL-1TEAM/apps/reco/models/trust_model/pipeline/sumi/pre_ml_no_nowon.ipynb"
data_path = r"c:/dev/study/eunjeong/SKN18-FINAL-1TEAM/data/processed_office_data.csv"

def create_regional_stats_cells():
    cells = []
    
    # Header - UNFILTERED
    cells.append(new_markdown_cell("""# 6. Detailed Regional Statistics (All Regions / Unfiltered)
**노원구 및 소규모 지역(매물 500건 미만)을 모두 포함**한 전체 지역별 상세 통계(평균 성사율 및 표준편차)를 확인합니다.
필터링 전 데이터의 변동성과 이상치(Outlier) 현황을 파악할 수 있습니다.
- **Mean (Average Rate)**: 해당 지역의 전체적인 거래 성과
- **Std (Standard Deviation)**: 해당 지역 내 중개사 별 성과의 편차 (일관성)"""))

    # Logic Implementation & Visualization
    code_content = f"""# 1. 전체 데이터 준비 및 지역별 통계 계산

# 원본 데이터 로드 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

try:
    if 'df_raw' not in locals():
        df_raw = pd.read_csv(r"{data_path}")
except:
    df_raw = pd.read_csv(r"{data_path}")

# [Safety] 총매물수 계산
df_raw['거래완료'] = df_raw['거래완료'].fillna(0)
if '등록매물' in df_raw.columns:
    df_raw['등록매물'] = df_raw['등록매물'].fillna(0)
    df_raw['총매물수'] = df_raw['거래완료'] + df_raw['등록매물']
df_raw['총매물수'] = df_raw['총매물수'].replace(0, 1)

# 지역명 추출
if 'ldCodeNm' in df_raw.columns:
    df_raw['region'] = df_raw['ldCodeNm']
elif '주소' in df_raw.columns:
    df_raw['region'] = df_raw['주소'].str.split().str[1]

# ---------------------------------------------------------
# Use All Data (No Filtering)
# ---------------------------------------------------------
df_target = df_raw.copy()

# ---------------------------------------------------------
# Calculate Stats per Region
# ---------------------------------------------------------

# 개별 중개사 성사율 계산
df_target['agent_success_rate'] = df_target['거래완료'] / df_target['총매물수']

# 지역별 통계 집계
regional_stats = df_target.groupby('region')['agent_success_rate'].agg(
    Mean='mean',
    Std='std',
    Count='count'  # 중개사 수
).reset_index()

# 성사율 높은 순으로 정렬
regional_stats = regional_stats.sort_values(by='Mean', ascending=False)

print("=== [결과] 전체 지역별 상세 통계 (상위 10곳) ===")
print(regional_stats.head(10))
# Escape braces for f-string in generated code
print(f"\\n✅ 총 {{len(regional_stats)}}개 지역 분석 완료")
"""
    cells.append(new_code_cell(code_content))

    cells.append(new_code_cell("""# 2. 지역별 평균 성사율 및 표준편차 그래프 (Bar Chart with Error Bars)

import matplotlib.pyplot as plt

plt.figure(figsize=(15, 8))

# x: 지역명, y: 평균 성사율, error: 표준편차
# 막대 그래프 그리기
bars = plt.bar(regional_stats['region'], regional_stats['Mean'], 
               yerr=regional_stats['Std'], capsize=5, 
               color='lightcoral', edgecolor='black', alpha=0.8) # Color changed to distinguish from filtered

plt.title('Regional Average Success Rate & Std Dev (All Regions / Unfiltered)', fontsize=15)
plt.xlabel('Region', fontsize=12)
plt.ylabel('Average Success Rate (Agent Level)', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.ylim(0, 1.1)

# 값 표시 (막대 위에 평균값)
for bar in bars:
    height = bar.get_height()
    if height > 0:
         plt.text(bar.get_x() + bar.get_width()/2., height + 0.02, 
                 f'{height:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.show()

print("💡 해석:")
print("1. **높은 편차 (Long Error Bars)**: 노원구 등 일부 지역의 표준편차가 매우 클 수 있습니다. 이는 지역 내 중개사 간 편차가 심함을 의미합니다.")
print("2. **극단적 평균 (High/Low Mean)**: 소규모 지역(매물 수 적음)은 평균 성사율이 극단적으로 0% 또는 100%에 가까울 수 있습니다.")
"""))

    return cells

def update_notebook():
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    try:
        nb = nbformat.read(notebook_path, as_version=4)
        print(f"Notebook loaded. Current cell count: {len(nb.cells)}")
        
        # Check if Regional Stats section already exists
        start_idx = -1
        for i, cell in enumerate(nb.cells):
            if cell.cell_type == 'markdown' and "# 6. Detailed Regional Statistics" in cell.source:
                start_idx = i
                break
        
        if start_idx != -1:
            print(f"Replacing existing Regional Statistics section starting at cell {start_idx}...")
            nb.cells = nb.cells[:start_idx]
        
        new_cells = create_regional_stats_cells()
        nb.cells.extend(new_cells)
        
        nbformat.write(nb, notebook_path)
        print(f"Notebook updated successfully. New cell count: {len(nb.cells)}")
        
    except Exception as e:
        print(f"Failed to update notebook: {e}")

if __name__ == "__main__":
    update_notebook()
