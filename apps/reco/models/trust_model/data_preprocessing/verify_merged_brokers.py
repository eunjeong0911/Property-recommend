"""
merged_brokers.csv 파일에서 검증용 컬럼만 추출하는 모듈
"""
import csv
from pathlib import Path
from typing import Dict, Any, List


class BrokerVerifier:
    """중개사 데이터 검증용 컬럼 추출 클래스"""
    
    def __init__(self):
        self.merged_data = []
        self.verification_results = []
    
    def load_merged_data(self, filepath: str) -> List[Dict[str, Any]]:
        """
        merged_brokers.csv 데이터 로드
        
        Args:
            filepath: CSV 파일 경로
            
        Returns:
            중개사 정보 리스트
        """
        filepath = Path(filepath)
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        self.merged_data = data
        print(f"merged_brokers.csv 로드: {len(data)}건")
        return data
    
    def extract_verification_columns(self) -> List[Dict[str, Any]]:
        """
        검증에 필요한 컬럼만 추출
        
        Returns:
            검증용 컬럼 리스트
        """
        print("\n=== 검증용 컬럼 추출 시작 ===\n")
        
        for idx, broker in enumerate(self.merged_data, 1):
            result = {
                'row_number': idx,
                'land_등록번호': broker.get('land_등록번호', ''),
                'land_중개사명': broker.get('land_중개사명', ''),
                'seoul_bsnmCmpnm': broker.get('seoul_bsnmCmpnm', ''),
                'land_주소': broker.get('land_주소', ''),
                'office_ldCodeNm': broker.get('office_ldCodeNm', ''),
                'office_mnnmadr': broker.get('office_mnnmadr', ''),
                'office_rdnmadr': broker.get('office_rdnmadr', ''),
                'seoul_ldCodeNm': broker.get('seoul_ldCodeNm', ''),
                'land_대표자': broker.get('land_대표자', ''),
                'office_brkrNm': broker.get('office_brkrNm', ''),
                'seoul_brkrNm': broker.get('seoul_brkrNm', ''),
            }
            
            self.verification_results.append(result)
        
        print(f"추출 완료: {len(self.verification_results)}건")
        return self.verification_results
    

    
    def save_results(self, output_filepath: str = None) -> None:
        """
        검증용 컬럼 저장
        
        Args:
            output_filepath: 출력 파일 경로 (기본값: data/verification_results.csv)
        """
        if output_filepath is None:
            output_filepath = Path("data") / "verification_results.csv"
        else:
            output_filepath = Path(output_filepath)
        
        # 디렉토리 생성
        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if self.verification_results:
            headers = list(self.verification_results[0].keys())
            
            with open(output_filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.verification_results)
            
            print(f"\n검증용 컬럼 저장:")
            print(f"  - 파일: {output_filepath}")
            print(f"  - 총 {len(self.verification_results)}건")


def main():
    """메인 실행 함수"""
    try:
        verifier = BrokerVerifier()
        
        # 데이터 파일 경로
        data_file = Path("data") / "merged_brokers.csv"
        
        if not data_file.exists():
            print(f"오류: {data_file} 파일을 찾을 수 없습니다.")
            print("먼저 merge_all_brokers.py를 실행하여 데이터를 병합하세요.")
            return
        
        print("=== merged_brokers.csv 검증용 컬럼 추출 프로그램 ===\n")
        print(f"입력 파일: {data_file.name}\n")
        
        # 데이터 로드
        verifier.load_merged_data(str(data_file))
        
        # 검증용 컬럼 추출
        verifier.extract_verification_columns()
        
        # 결과 저장
        verifier.save_results()
        
        print("\n=== 추출 완료 ===")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
