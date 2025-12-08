"""
매칭된 데이터에서 특정 컬럼만 추출하는 스크립트
"""
import csv
from pathlib import Path


def extract_columns():
    """매칭된 데이터에서 필요한 컬럼만 추출"""
    
    input_file = Path("data/matched_brokers.csv")
    output_file = Path("data/matched_brokers_selected.csv")
    
    if not input_file.exists():
        print("오류: matched_brokers.csv 파일이 없습니다.")
        return
    
    # 추출할 컬럼 목록
    selected_columns = [
        'land_중개사명',
        'land_대표자',
        'land_주소',
        'vworld_중개사명',
        'vworld_대표자',
        'vworld_대표자구분',
        'vworld_시군구명',
        'vworld_중개업자구분',
    ]
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    print(f"원본 데이터: {len(data)}건")
    print(f"추출할 컬럼: {len(selected_columns)}개\n")
    
    # 선택된 컬럼만 추출
    extracted_data = []
    for row in data:
        extracted_row = {col: row.get(col, '') for col in selected_columns}
        extracted_data.append(extracted_row)
    
    # CSV로 저장
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=selected_columns)
        writer.writeheader()
        writer.writerows(extracted_data)
    
    print(f"추출 완료: {output_file}")
    print(f"저장된 데이터: {len(extracted_data)}건")
    
    # 샘플 출력
    print("\n=== 샘플 데이터 (처음 5건) ===")
    for idx, row in enumerate(extracted_data[:5], 1):
        print(f"\n[{idx}]")
        for col in selected_columns:
            print(f"  {col}: {row[col]}")


if __name__ == "__main__":
    extract_columns()
