"""
matched_brokers_enriched.csv의 각 행에서 주소의 구(district)가 일치하는지 확인하는 스크립트
"""
import csv
import re
from pathlib import Path
from typing import Optional


def extract_district(address: Optional[str]) -> Optional[str]:
    """
    주소에서 구(district) 추출
    예: "서울특별시 강남구 역삼동 123" -> "강남구"
    
    Args:
        address: 주소 문자열
        
    Returns:
        구 이름 (예: "강남구", "서초구" 등)
    """
    if not address:
        return None
    
    # 서울특별시 다음에 오는 구 추출
    match = re.search(r'서울특별시\s+(\S+구)', address)
    if match:
        return match.group(1)
    
    # 서울시 다음에 오는 구 추출
    match = re.search(r'서울시\s+(\S+구)', address)
    if match:
        return match.group(1)
    
    # 그냥 구만 추출
    match = re.search(r'(\S+구)', address)
    if match:
        return match.group(1)
    
    return None


def verify_district_consistency(csv_path: str, output_path: str = None):
    """
    CSV 파일의 각 행에서 주소 구가 일치하는지 확인
    
    Args:
        csv_path: 입력 CSV 파일 경로
        output_path: 불일치 결과를 저장할 CSV 파일 경로 (선택)
    """
    print(f"=== 주소 구(district) 일치 여부 확인 ===\n")
    print(f"파일 로드: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"총 {len(rows)}건 로드 완료\n")
    
    # 확인할 주소 필드들
    address_fields = [
        ('land_주소', 'land'),
        ('vworld_시군구명', 'vworld'),
        ('api_시군구명', 'api'),
        ('api_도로명주소', 'api_road'),
        ('api_지번주소', 'api_jibun')
    ]
    
    mismatches = []
    match_count = 0
    mismatch_count = 0
    
    for idx, row in enumerate(rows, 1):
        # 각 필드에서 구 추출
        districts = {}
        for field, label in address_fields:
            if field in row and row[field]:
                district = extract_district(row[field])
                if district:
                    districts[label] = district
        
        # 구가 모두 일치하는지 확인
        if districts:
            unique_districts = set(districts.values())
            
            if len(unique_districts) > 1:
                # 불일치 발견
                mismatch_count += 1
                mismatch_info = {
                    '행번호': idx,
                    'land_중개사명': row.get('land_중개사명', ''),
                    'land_등록번호': row.get('land_등록번호', ''),
                    **{f'{label}_구': districts.get(label, '') for _, label in address_fields}
                }
                mismatches.append(mismatch_info)
                
                if mismatch_count <= 10:  # 처음 10개만 출력
                    print(f"[불일치 {mismatch_count}] 행 {idx}: {row.get('land_중개사명', '')}")
                    for label, district in districts.items():
                        print(f"  - {label}: {district}")
                    print()
            else:
                match_count += 1
    
    # 결과 요약
    print(f"\n{'='*50}")
    print(f"검증 완료")
    print(f"{'='*50}")
    print(f"총 검증: {len(rows)}건")
    print(f"일치: {match_count}건 ({match_count/len(rows)*100:.1f}%)")
    print(f"불일치: {mismatch_count}건 ({mismatch_count/len(rows)*100:.1f}%)")
    
    # 불일치 결과를 파일로 저장
    if mismatches and output_path:
        fieldnames = list(mismatches[0].keys())
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(mismatches)
        print(f"\n불일치 데이터 저장: {output_path}")
    
    return match_count, mismatch_count, mismatches


def main():
    """메인 실행 함수"""
    try:
        # 파일 경로 설정
        data_dir = Path("data")
        input_path = data_dir / "matched_brokers_enriched.csv"
        output_path = data_dir / "district_mismatches.csv"
        
        # 파일 존재 확인
        if not input_path.exists():
            print(f"오류: {input_path} 파일을 찾을 수 없습니다.")
            return
        
        # 검증 실행
        match_count, mismatch_count, mismatches = verify_district_consistency(
            str(input_path),
            str(output_path)
        )
        
        print("\n=== 완료 ===")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
