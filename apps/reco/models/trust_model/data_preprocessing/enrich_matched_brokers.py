"""
matched_brokers.csv에 API 중개사무소 정보를 추가하는 모듈
"""
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional


def normalize_registration_number(reg_num: Optional[str]) -> Optional[str]:
    """
    등록번호 정규화 (숫자와 하이픈만 유지)
    
    Args:
        reg_num: 등록번호
        
    Returns:
        정규화된 등록번호
    """
    if not reg_num:
        return None
    # 공백 제거, 대소문자 통일
    normalized = str(reg_num).strip().upper()
    # 특수문자 중 하이픈만 유지
    normalized = re.sub(r'[^\w\-가-힣]', '', normalized)
    return normalized if normalized else None


def load_csv(filepath: str) -> List[Dict[str, str]]:
    """CSV 파일 로드"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv(filepath: str, data: List[Dict[str, str]], fieldnames: List[str]) -> None:
    """CSV 파일 저장"""
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def enrich_matched_brokers(
    matched_brokers_path: str,
    api_brokers_path: str,
    output_path: str
) -> None:
    """
    matched_brokers.csv에 API 중개사무소 정보를 추가
    
    Args:
        matched_brokers_path: matched_brokers.csv 파일 경로
        api_brokers_path: broker_offices.csv 파일 경로 (API에서 가져온 데이터)
        output_path: 출력 파일 경로
    """
    print("=== matched_brokers.csv 정보 보강 시작 ===\n")
    
    # 데이터 로드
    print(f"매칭된 중개사 데이터 로드: {matched_brokers_path}")
    matched_brokers = load_csv(matched_brokers_path)
    print(f"  - {len(matched_brokers)}건 로드 완료")
    
    print(f"\nAPI 중개사무소 데이터 로드: {api_brokers_path}")
    api_brokers = load_csv(api_brokers_path)
    print(f"  - {len(api_brokers)}건 로드 완료")
    
    # API 데이터를 등록번호로 인덱싱 (하나의 등록번호에 여러 명이 있을 수 있음)
    api_by_reg = {}
    for broker in api_brokers:
        reg_num = normalize_registration_number(broker.get('jurirno'))
        if reg_num:
            if reg_num not in api_by_reg:
                api_by_reg[reg_num] = []
            api_by_reg[reg_num].append(broker)
    
    print(f"\nAPI 데이터 인덱싱 완료: {len(api_by_reg)}개의 고유 등록번호")
    
    # 새로운 필드 정의 (API 데이터에서 추가할 필드)
    api_fields = [
        'api_중개사명',
        'api_대표자명',
        'api_등록번호',
        'api_등록일',
        'api_상태',
        'api_도로명주소',
        'api_지번주소',
        'api_개설시작일',
        'api_개설종료일',
        'api_최종수정일',
        'api_시군구코드',
        'api_시군구명',
        'api_도로명주소코드',
    ]
    
    # 기존 필드 + 새로운 필드
    existing_fields = list(matched_brokers[0].keys()) if matched_brokers else []
    all_fields = existing_fields + api_fields
    
    # 매칭 및 정보 추가
    enriched_brokers = []
    matched_count = 0
    multiple_match_count = 0
    
    for matched_broker in matched_brokers:
        # land_등록번호로 API 데이터 찾기
        land_reg = normalize_registration_number(matched_broker.get('land_등록번호'))
        
        # 기존 데이터 복사
        enriched = matched_broker.copy()
        
        # API 필드 초기화
        for field in api_fields:
            enriched[field] = ''
        
        if land_reg and land_reg in api_by_reg:
            api_matches = api_by_reg[land_reg]
            matched_count += 1
            
            if len(api_matches) > 1:
                multiple_match_count += 1
            
            # 첫 번째 매칭 데이터 사용 (대표자 우선)
            # 대표자구분이 '대표'인 것을 우선 선택
            api_broker = None
            for match in api_matches:
                if match.get('ofcpsSeCodeNm') == '대표':
                    api_broker = match
                    break
            
            # 대표가 없으면 첫 번째 것 사용
            if not api_broker:
                api_broker = api_matches[0]
            
            # API 정보 추가
            enriched['api_중개사명'] = api_broker.get('bsnmCmpnm', '')
            enriched['api_대표자명'] = api_broker.get('brkrNm', '')
            enriched['api_등록번호'] = api_broker.get('jurirno', '')
            enriched['api_등록일'] = api_broker.get('registDe', '')
            enriched['api_상태'] = api_broker.get('sttusSeCodeNm', '')
            enriched['api_도로명주소'] = api_broker.get('rdnmadr', '')
            enriched['api_지번주소'] = api_broker.get('mnnmadr', '')
            enriched['api_개설시작일'] = api_broker.get('estbsBeginDe', '')
            enriched['api_개설종료일'] = api_broker.get('estbsEndDe', '')
            enriched['api_최종수정일'] = api_broker.get('lastUpdtDt', '')
            enriched['api_시군구코드'] = api_broker.get('ldCode', '')
            enriched['api_시군구명'] = api_broker.get('ldCodeNm', '')
            enriched['api_도로명주소코드'] = api_broker.get('rdnmadrcode', '')
        
        enriched_brokers.append(enriched)
    
    # 결과 저장
    print(f"\n정보 보강 완료:")
    print(f"  - 전체: {len(enriched_brokers)}건")
    print(f"  - API 매칭 성공: {matched_count}건 ({matched_count/len(enriched_brokers)*100:.1f}%)")
    print(f"  - 복수 매칭 (같은 등록번호에 여러 명): {multiple_match_count}건")
    
    save_csv(output_path, enriched_brokers, all_fields)
    print(f"\n결과 저장: {output_path}")


def main():
    """메인 실행 함수"""
    try:
        # 파일 경로 설정
        data_dir = Path("data")
        matched_brokers_path = data_dir / "matched_brokers.csv"
        api_brokers_path = data_dir / "broker_offices.csv"  # load_brokerOffice.py 실행 결과
        output_path = data_dir / "matched_brokers_enriched.csv"
        
        # 파일 존재 확인
        if not matched_brokers_path.exists():
            print(f"오류: {matched_brokers_path} 파일을 찾을 수 없습니다.")
            return
        
        if not api_brokers_path.exists():
            print(f"오류: {api_brokers_path} 파일을 찾을 수 없습니다.")
            print("먼저 load_brokerOffice.py를 실행하여 API 데이터를 수집하세요.")
            return
        
        # 정보 보강 실행
        enrich_matched_brokers(
            str(matched_brokers_path),
            str(api_brokers_path),
            str(output_path)
        )
        
        print("\n=== 완료 ===")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
