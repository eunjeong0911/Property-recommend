"""
land_brokers.csv를 기준으로 broker_offices.csv와 seoul_brokers.csv를 매칭하는 모듈
등록번호를 기준으로 세 파일을 병합합니다.
"""
import csv
from pathlib import Path
from typing import List, Dict, Any
import re


class BrokerMerger:
    """중개사 정보 병합 클래스"""
    
    def __init__(self):
        self.land_brokers = []
        self.broker_offices = {}
        self.seoul_brokers = {}
        self.merged_brokers = []
    
    def normalize_registration_number(self, reg_num: str) -> str:
        """
        등록번호 정규화 (숫자만 추출)
        
        Args:
            reg_num: 등록번호
            
        Returns:
            정규화된 등록번호 (숫자만)
        """
        if not reg_num:
            return None
        # 숫자만 추출
        numbers_only = re.sub(r'[^\d]', '', str(reg_num))
        return numbers_only if numbers_only else None
    
    def load_land_brokers(self, filepath: str) -> List[Dict[str, Any]]:
        """
        land_brokers.csv 데이터 로드
        
        Args:
            filepath: CSV 파일 경로
            
        Returns:
            중개사 정보 리스트
        """
        filepath = Path(filepath)
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        self.land_brokers = data
        print(f"land_brokers.csv 로드: {len(data)}건")
        return data
    
    def load_broker_offices(self, filepath: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        broker_offices.csv 데이터 로드 (jurirno를 키로 하는 딕셔너리, 리스트로 저장)
        
        Args:
            filepath: CSV 파일 경로
            
        Returns:
            등록번호를 키로 하는 중개사 정보 딕셔너리 (값은 리스트)
        """
        filepath = Path(filepath)
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        # jurirno를 키로 하는 딕셔너리 생성 (리스트로 저장)
        for broker in data:
            reg_num = self.normalize_registration_number(broker.get('jurirno'))
            if reg_num:
                if reg_num not in self.broker_offices:
                    self.broker_offices[reg_num] = []
                self.broker_offices[reg_num].append(broker)
        
        print(f"broker_offices.csv 로드: {len(data)}건")
        print(f"  - 유효한 등록번호: {len(self.broker_offices)}건")
        return self.broker_offices
    
    def load_seoul_brokers(self, filepath: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        seoul_brokers.csv 데이터 로드 (jurirno를 키로 하는 딕셔너리, 리스트로 저장)
        
        Args:
            filepath: CSV 파일 경로
            
        Returns:
            등록번호를 키로 하는 중개사 정보 딕셔너리 (값은 리스트)
        """
        filepath = Path(filepath)
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        # jurirno를 키로 하는 딕셔너리 생성 (리스트로 저장)
        for broker in data:
            reg_num = self.normalize_registration_number(broker.get('jurirno'))
            if reg_num:
                if reg_num not in self.seoul_brokers:
                    self.seoul_brokers[reg_num] = []
                self.seoul_brokers[reg_num].append(broker)
        
        print(f"seoul_brokers.csv 로드: {len(data)}건")
        print(f"  - 유효한 등록번호: {len(self.seoul_brokers)}건")
        return self.seoul_brokers
    
    def merge_brokers(self) -> List[Dict[str, Any]]:
        """
        land_brokers를 기준으로 broker_offices와 seoul_brokers 병합
        중개보조원이 여러 명인 경우 각각 별도 행으로 생성
        
        Returns:
            병합된 중개사 정보 리스트
        """
        print("\n=== 중개사 정보 병합 시작 ===\n")
        
        matched_with_offices = 0
        matched_with_seoul = 0
        matched_with_both = 0
        total_office_records = 0
        total_seoul_records = 0
        
        for land_broker in self.land_brokers:
            # land_brokers의 등록번호 정규화
            land_reg = self.normalize_registration_number(land_broker.get('등록번호'))
            
            # 매칭된 office와 seoul 데이터 가져오기
            office_list = self.broker_offices.get(land_reg, []) if land_reg else []
            seoul_list = self.seoul_brokers.get(land_reg, []) if land_reg else []
            
            # 매칭된 데이터가 있는지 확인
            has_office = len(office_list) > 0
            has_seoul = len(seoul_list) > 0
            
            if has_office:
                matched_with_offices += 1
                total_office_records += len(office_list)
            if has_seoul:
                matched_with_seoul += 1
                total_seoul_records += len(seoul_list)
            if has_office and has_seoul:
                matched_with_both += 1
            
            # 매칭된 데이터가 없으면 land 데이터만 추가
            if not has_office and not has_seoul:
                merged_broker = {}
                for key, value in land_broker.items():
                    merged_broker[f'land_{key}'] = value
                self.merged_brokers.append(merged_broker)
                continue
            
            # office와 seoul 데이터의 모든 조합에 대해 행 생성
            # 둘 다 있으면 카르테시안 곱, 하나만 있으면 그것만 사용
            if has_office and has_seoul:
                # 둘 다 있는 경우: 모든 조합 생성
                for office_data in office_list:
                    for seoul_data in seoul_list:
                        merged_broker = {}
                        
                        # land 데이터 추가
                        for key, value in land_broker.items():
                            merged_broker[f'land_{key}'] = value
                        
                        # office 데이터 추가
                        for key, value in office_data.items():
                            merged_broker[f'office_{key}'] = value
                        
                        # seoul 데이터 추가
                        for key, value in seoul_data.items():
                            merged_broker[f'seoul_{key}'] = value
                        
                        self.merged_brokers.append(merged_broker)
            
            elif has_office:
                # office만 있는 경우
                for office_data in office_list:
                    merged_broker = {}
                    
                    # land 데이터 추가
                    for key, value in land_broker.items():
                        merged_broker[f'land_{key}'] = value
                    
                    # office 데이터 추가
                    for key, value in office_data.items():
                        merged_broker[f'office_{key}'] = value
                    
                    self.merged_brokers.append(merged_broker)
            
            else:  # has_seoul
                # seoul만 있는 경우
                for seoul_data in seoul_list:
                    merged_broker = {}
                    
                    # land 데이터 추가
                    for key, value in land_broker.items():
                        merged_broker[f'land_{key}'] = value
                    
                    # seoul 데이터 추가
                    for key, value in seoul_data.items():
                        merged_broker[f'seoul_{key}'] = value
                    
                    self.merged_brokers.append(merged_broker)
        
        print(f"병합 완료: {len(self.merged_brokers)}건")
        print(f"  - broker_offices와 매칭: {matched_with_offices}건 (총 {total_office_records}개 레코드)")
        print(f"  - seoul_brokers와 매칭: {matched_with_seoul}건 (총 {total_seoul_records}개 레코드)")
        print(f"  - 둘 다 매칭: {matched_with_both}건")
        
        return self.merged_brokers
    
    def save_results(self, output_filepath: str = None) -> None:
        """
        병합 결과 저장
        
        Args:
            output_filepath: 출력 파일 경로 (기본값: data/merged_brokers.csv)
        """
        if output_filepath is None:
            output_filepath = Path("data") / "merged_brokers.csv"
        else:
            output_filepath = Path(output_filepath)
        
        # 디렉토리 생성
        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if self.merged_brokers:
            # 모든 키를 수집하여 헤더 생성
            all_keys = set()
            for broker in self.merged_brokers:
                all_keys.update(broker.keys())
            
            # 헤더 정렬 (land_ -> office_ -> seoul_ 순서)
            land_keys = sorted([k for k in all_keys if k.startswith('land_')])
            office_keys = sorted([k for k in all_keys if k.startswith('office_')])
            seoul_keys = sorted([k for k in all_keys if k.startswith('seoul_')])
            headers = land_keys + office_keys + seoul_keys
            
            with open(output_filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.merged_brokers)
            
            print(f"\n병합된 데이터 저장:")
            print(f"  - 파일: {output_filepath}")
            print(f"  - 총 컬럼 수: {len(headers)}개")
            print(f"    * land_ 컬럼: {len(land_keys)}개")
            print(f"    * office_ 컬럼: {len(office_keys)}개")
            print(f"    * seoul_ 컬럼: {len(seoul_keys)}개")


def main():
    """메인 실행 함수"""
    try:
        merger = BrokerMerger()
        
        # 데이터 디렉토리
        data_dir = Path("data")
        
        # 파일 경로 설정
        land_file = data_dir / "land_brokers.csv"
        office_file = data_dir / "broker_offices.csv"
        seoul_file = data_dir / "seoul_brokers.csv"
        
        # 파일 존재 확인
        if not land_file.exists():
            print(f"오류: {land_file} 파일을 찾을 수 없습니다.")
            return
        
        if not office_file.exists():
            print(f"오류: {office_file} 파일을 찾을 수 없습니다.")
            return
        
        if not seoul_file.exists():
            print(f"오류: {seoul_file} 파일을 찾을 수 없습니다.")
            return
        
        print("=== 중개사 데이터 병합 프로그램 ===\n")
        print(f"land_brokers: {land_file.name}")
        print(f"broker_offices: {office_file.name}")
        print(f"seoul_brokers: {seoul_file.name}\n")
        
        # 데이터 로드
        merger.load_land_brokers(str(land_file))
        merger.load_broker_offices(str(office_file))
        merger.load_seoul_brokers(str(seoul_file))
        
        # 병합 수행
        merged = merger.merge_brokers()
        
        # 결과 저장
        merger.save_results()
        
        print("\n=== 병합 완료 ===")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
