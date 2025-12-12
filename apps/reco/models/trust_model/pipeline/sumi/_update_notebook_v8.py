import nbformat
from nbformat.v4 import new_markdown_cell, new_code_cell
import os

# Define file paths
notebook_path = r"c:/dev/study/eunjeong/SKN18-FINAL-1TEAM/apps/reco/models/trust_model/pipeline/sumi/pre_ml_no_nowon.ipynb"
data_path = r"c:/dev/study/eunjeong/SKN18-FINAL-1TEAM/data/processed_office_data.csv"

def update_comparison_section_logic():
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    try:
        nb = nbformat.read(notebook_path, as_version=4)
        print(f"Notebook loaded. Current cell count: {len(nb.cells)}")
        
        # Locate the specific cell in "3. Comparative Analysis" that contains the filtering logic
        # We look for the code snippet "filtered_stats ="
        
        found_cell_index = -1
        for i, cell in enumerate(nb.cells):
            if cell.cell_type == 'code' and "filtered_stats =" in cell.source and "서울특별시 노원구" in cell.source:
                found_cell_index = i
                break
        
        if found_cell_index != -1:
            print(f"Found target cell at index {found_cell_index}. content: {nb.cells[found_cell_index].source[:50]}...")
            
            # The corrected code logic
            new_code = f"""# 2. 지역별 통계 비교 (Raw vs Filtered)

# Raw Data 통계 계산
raw_stats = df_raw.groupby('region').agg({{
    '총매물수': 'sum',
    '거래완료': 'sum'
}}).reset_index()
raw_stats['거래성사율'] = raw_stats['거래완료'] / raw_stats['총매물수']

# Filtered Data (노원구 및 500건 미만 제거 기준)
# 노원구 제거 (데이터 상 이름: '노원구')
filtered_stats = raw_stats[
    (raw_stats['region'] != '서울특별시 노원구') & 
    (raw_stats['region'] != '노원구') 
].copy()

# 500건 미만 제거
filtered_stats = filtered_stats[filtered_stats['총매물수'] >= 500].copy()

# 제거된 지역 식별
removed_regions = set(raw_stats['region']) - set(filtered_stats['region'])
print(f"🚫 제거된 지역 ({{len(removed_regions)}}개): {{removed_regions}}")

removed_df = raw_stats[raw_stats['region'].isin(removed_regions)]
kept_df = raw_stats[~raw_stats['region'].isin(removed_regions)]
"""
            # Update the cell content
            nb.cells[found_cell_index] = new_code_cell(new_code)
            print("Successfully updated the filtering logic in Section 3.")
            
        else:
            print("Could not find the specific cell to update in Section 3.")
            # Option: If not found, maybe append? But that would duplicate. Ideally we fix in place.
        
        nbformat.write(nb, notebook_path)
        print(f"Notebook saved.")
        
    except Exception as e:
        print(f"Failed to update notebook: {e}")

if __name__ == "__main__":
    update_comparison_section_logic()
