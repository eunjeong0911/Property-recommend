import nbformat
from nbformat.v4 import new_markdown_cell, new_code_cell
import os

# Define file paths
notebook_path = r"c:/dev/study/eunjeong/SKN18-FINAL-1TEAM/apps/reco/models/trust_model/pipeline/sumi/pre_ml_no_nowon.ipynb"
data_path = r"c:/dev/study/eunjeong/SKN18-FINAL-1TEAM/data/processed_office_data.csv"

def create_regional_stats_cells():
    cells = []
    
    # Header - FILTERED
    cells.append(new_markdown_cell("""# 7. Detailed Regional Statistics (Filtered Only)
**"노원구 제거" 및 "총매물수 500건 미만 제거" 후**, 남은 지역들에 대한 상세 통계(평균 성사율 및 표준편차)를 확인합니다.
앞선 6번 섹션(Unfiltered)과 비교하여 **이상치 제거 효과** 및 **표준편차 감소(안정성)**를 직접 확인할 수 있습니다.
- **Mean (Average Rate)**: 정제된 데이터 기반의 지역 성과
- **Std (Standard Deviation)**: 정제된 데이터 기반의 중개사 성과 편차"""))

    # Logic Implementation & Visualization
    code_content = f"""# 1. 필터링된 데이터 기반 지역별 통계 계산

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
# Filter Data (노원구 제외 + 500건 미만 제외)
# ---------------------------------------------------------
# 지역별 총매물수 먼저 합산
region_sums = df_raw.groupby('region')['총매물수'].sum()
valid_regions = region_sums[region_sums >= 500].index.tolist()

df_filtered = df_raw[
    (df_raw['region'] != '서울특별시 노원구') & 
    (df_raw['region'] != '노원구') &
    (df_raw['region'].isin(valid_regions))
].copy()

# ---------------------------------------------------------
# Calculate Stats per Region
# ---------------------------------------------------------

# 개별 중개사 성사율 계산
df_filtered['agent_success_rate'] = df_filtered['거래완료'] / df_filtered['총매물수']

# 지역별 통계 집계
regional_stats_filtered = df_filtered.groupby('region')['agent_success_rate'].agg(
    Mean='mean',
    Std='std',
    Count='count'  # 중개사 수
).reset_index()

# 성사율 높은 순으로 정렬
regional_stats_filtered = regional_stats_filtered.sort_values(by='Mean', ascending=False)

print("=== [결과] 필터링 후 지역별 상세 통계 (상위 10곳) ===")
print(regional_stats_filtered.head(10))
# Escape braces for f-string in generated code
print(f"\\n✅ 총 {{len(regional_stats_filtered)}}개 지역 분석 완료")
"""
    cells.append(new_code_cell(code_content))

    cells.append(new_code_cell("""# 2. 지역별 평균 성사율 및 표준편차 그래프 (Filtered)

plt.figure(figsize=(15, 8))

# x: 지역명, y: 평균 성사율, error: 표준편차
# 막대 그래프 그리기 (파란색 계열)
bars = plt.bar(regional_stats_filtered['region'], regional_stats_filtered['Mean'], 
               yerr=regional_stats_filtered['Std'], capsize=5, 
               color='cornflowerblue', edgecolor='black', alpha=0.9) 

plt.title('Regional Average Success Rate & Std Dev (Filtered Data Only)', fontsize=15)
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
print("1. **안정적인 편차**: 필터링 전(Section 6)과 비교하여 오차 막대(Std)의 길이가 전반적으로 줄어들었는지 확인하세요.")
print("2. **이상치 제거**: 극단적으로 높거나 낮은 평균값을 가진 지역들이 사라지고, 전반적으로 신뢰할 수 있는 구간에 위치합니다.")
"""))

    return cells

def update_notebook():
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    try:
        nb = nbformat.read(notebook_path, as_version=4)
        print(f"Notebook loaded. Current cell count: {len(nb.cells)}")
        
        # Check if Section 7 already exists so we replace/append correctly
        start_idx = -1
        for i, cell in enumerate(nb.cells):
            if cell.cell_type == 'markdown' and "# 7. Detailed Regional Statistics" in cell.source:
                start_idx = i
                break
        
        if start_idx != -1:
            print(f"Replacing existing Section 7 starting at cell {start_idx}...")
            nb.cells = nb.cells[:start_idx]
        
        new_cells = create_regional_stats_cells()
        nb.cells.extend(new_cells)
        
        nbformat.write(nb, notebook_path)
        print(f"Notebook updated successfully. New cell count: {len(nb.cells)}")
        
    except Exception as e:
        print(f"Failed to update notebook: {e}")

if __name__ == "__main__":
    update_notebook()
