"""
VWorld API 중개사 정보와 크롤링한 중개사 정보를 매칭하는 모듈
"""
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import re


class BrokerMatcher:
    """중개사 정보 매칭 클래스"""
    
    def __init__(self):
        self.vworld_brokers = []
        self.land_brokers = []
        self.matched_brokers = []
        self.unmatched_vworld = []
        self.unmatched_land = []
    
    def load_vworld_data(self, filepath: str) -> List[Dict[str, Any]]:
        """
        VWorld API 중개사 데이터 로드
        
        Args:
            filepath: JSON 또는 CSV 파일 경로
            
        Returns:
            중개사 정보 리스트
        """
        filepath = Path(filepath)
        
        if filepath.suffix == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif filepath.suffix == '.csv':
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        else:
            raise ValueError("지원하지 않는 파일 형식입니다. JSON 또는 CSV 파일을 사용하세요.")
        
        self.vworld_brokers = data
        print(f"VWorld 데이터 로드: {len(data)}건")
        return data
    
    def load_land_data(self, filepath: str) -> List[Dict[str, Any]]:
        """
        크롤링한 중개사 데이터 로드
        
        Args:
            filepath: JSON 또는 CSV 파일 경로
            
        Returns:
            중개사 정보 리스트
        """
        filepath = Path(filepath)
        
        if filepath.suffix == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif filepath.suffix == '.csv':
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        else:
            raise ValueError("지원하지 않는 파일 형식입니다. JSON 또는 CSV 파일을 사용하세요.")
        
        self.land_brokers = data
        print(f"크롤링 데이터 로드: {len(data)}건")
        return data
    
    def normalize_registration_number(self, reg_num: Optional[str]) -> Optional[str]:
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
    
    def normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """
        전화번호 정규화 (공백, 하이픈 제거)
        
        Args:
            phone: 전화번호
            
        Returns:
            정규화된 전화번호
        """
        if not phone:
            return None
        return re.sub(r'[\s\-]', '', str(phone))
    
    def normalize_name(self, name: Optional[str]) -> Optional[str]:
        """
        중개사명 정규화 (공백 제거, 소문자 변환)
        
        Args:
            name: 중개사명
            
        Returns:
            정규화된 중개사명
        """
        if not name:
            return None
        return re.sub(r'\s', '', str(name)).lower()
    
    def match_brokers(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        중개사 정보 매칭
        
        Returns:
            (매칭된 중개사, 매칭 안된 VWorld 중개사, 매칭 안된 크롤링 중개사)
        """
        print("\n=== 중개사 정보 매칭 시작 ===\n")
        
        # VWorld 데이터를 등록번호로 인덱싱
        vworld_by_reg = {}
        vworld_by_phone = {}
        vworld_by_name = {}
        
        for broker in self.vworld_brokers:
            # 등록번호 인덱싱 (jurirno: 법인등록번호)
            reg_num = self.normalize_registration_number(broker.get('jurirno'))
            if reg_num:
                vworld_by_reg[reg_num] = broker
            
            # 중개사명 인덱싱
            name = self.normalize_name(broker.get('bsnmCmpnm'))
            if name:
                if name not in vworld_by_name:
                    vworld_by_name[name] = []
                vworld_by_name[name].append(broker)
        
        matched_land_indices = set()
        matched_vworld_indices = set()
        
        # 크롤링 데이터와 매칭
        for idx, land_broker in enumerate(self.land_brokers):
            matched = False
            vworld_match = None
            
            # 등록번호가 일치하는 경우 매칭
            land_reg = self.normalize_registration_number(land_broker.get('등록번호'))
            
            if land_reg:
                # 등록번호로 매칭
                if land_reg in vworld_by_reg:
                    vworld_match = vworld_by_reg[land_reg]
                    matched = True
            
            if matched and vworld_match:
                # 매칭된 정보 병합
                matched_broker = {
                    # VWorld 정보
                    "vworld_중개사명": vworld_match.get('bsnmCmpnm'),
                    "vworld_대표자": vworld_match.get('brkrNm'),
                    "vworld_등록번호": vworld_match.get('jurirno'),
                    "vworld_중개업자구분": vworld_match.get('brkrAsortCodeNm'),
                    "vworld_대표자구분": vworld_match.get('ofcpsSeCodeNm'),
                    "vworld_자격증번호": vworld_match.get('crqfcNo'),
                    "vworld_자격취득일": vworld_match.get('crqfcAcqdt'),
                    "vworld_최종수정일": vworld_match.get('lastUpdtDt'),
                    "vworld_시군구코드": vworld_match.get('ldCode'),
                    "vworld_시군구명": vworld_match.get('ldCodeNm'),
                    "vworld_구명": vworld_match.get('district_name'),
                    # 크롤링 정보
                    "land_중개사명": land_broker.get('중개사명'),
                    "land_대표자": land_broker.get('대표자'),
                    "land_전화번호": land_broker.get('전화번호'),
                    "land_주소": land_broker.get('주소'),
                    "land_등록번호": land_broker.get('등록번호'),
                    "land_거래완료": land_broker.get('거래완료'),
                    "land_등록매물": land_broker.get('등록매물'),
                    "land_매물번호": land_broker.get('매물번호'),
                    "land_매물_URL": land_broker.get('매물_URL'),
                    "land_매물주소": land_broker.get('주소'),
                    "land_출처파일": land_broker.get('출처파일'),
                }
                
                self.matched_brokers.append(matched_broker)
                matched_land_indices.add(idx)
                
                # VWorld 매칭 인덱스 추가
                vworld_idx = self.vworld_brokers.index(vworld_match)
                matched_vworld_indices.add(vworld_idx)
        
        # 매칭 안된 데이터 수집
        self.unmatched_land = [
            broker for idx, broker in enumerate(self.land_brokers)
            if idx not in matched_land_indices
        ]
        
        self.unmatched_vworld = [
            broker for idx, broker in enumerate(self.vworld_brokers)
            if idx not in matched_vworld_indices
        ]
        
        print(f"매칭 완료: {len(self.matched_brokers)}건")
        print(f"매칭 안된 크롤링 데이터: {len(self.unmatched_land)}건")
        print(f"매칭 안된 VWorld 데이터: {len(self.unmatched_vworld)}건")
        
        return self.matched_brokers, self.unmatched_vworld, self.unmatched_land
    
    def save_results(self, output_dir: str = "data") -> None:
        """
        매칭 결과 저장
        
        Args:
            output_dir: 출력 디렉토리
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 매칭된 데이터 저장
        if self.matched_brokers:
            matched_csv = output_dir / "matched_brokers.csv"
            
            headers = sorted(self.matched_brokers[0].keys())
            with open(matched_csv, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.matched_brokers)
            
            print(f"\n매칭된 데이터 저장:")
            print(f"  - CSV: {matched_csv}")
        
        # 매칭 안된 크롤링 데이터 저장
        if self.unmatched_land:
            unmatched_land_csv = output_dir / "unmatched_land_brokers.csv"
            
            headers = sorted(self.unmatched_land[0].keys())
            with open(unmatched_land_csv, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.unmatched_land)
            
            print(f"\n매칭 안된 크롤링 데이터 저장:")
            print(f"  - CSV: {unmatched_land_csv}")
        
        # 매칭 안된 VWorld 데이터 저장
        if self.unmatched_vworld:
            unmatched_vworld_csv = output_dir / "unmatched_vworld_brokers.csv"
            
            headers = sorted(self.unmatched_vworld[0].keys())
            with open(unmatched_vworld_csv, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.unmatched_vworld)
            
            print(f"\n매칭 안된 VWorld 데이터 저장:")
            print(f"  - CSV: {unmatched_vworld_csv}")


def main():
    """메인 실행 함수"""
    try:
        matcher = BrokerMatcher()
        
        # 데이터 로드 (가장 최근 파일 자동 선택)
        data_dir = Path("data")
        
        # VWorld 데이터 찾기
        vworld_file = data_dir / "seoul_brokers.csv"
        if not vworld_file.exists():
            print("오류: VWorld 중개사 데이터 파일을 찾을 수 없습니다.")
            print("먼저 load_broker.py를 실행하여 데이터를 수집하세요.")
            return
        
        # 크롤링 데이터 찾기
        land_file = data_dir / "land_brokers.csv"
        if not land_file.exists():
            print("오류: 크롤링 중개사 데이터 파일을 찾을 수 없습니다.")
            print("먼저 load_Landbroker.py를 실행하여 데이터를 추출하세요.")
            return
        
        print(f"VWorld 데이터: {vworld_file.name}")
        print(f"크롤링 데이터: {land_file.name}\n")
        
        # 데이터 로드
        matcher.load_vworld_data(str(vworld_file))
        matcher.load_land_data(str(land_file))
        
        # 매칭 수행
        matched, unmatched_vworld, unmatched_land = matcher.match_brokers()
        
        # 결과 저장
        matcher.save_results()
        
        # 요약 통계
        total_land = len(matcher.land_brokers)
        total_vworld = len(matcher.vworld_brokers)
        matched_count = len(matched)
        
        print("\n=== 매칭 요약 ===")
        print(f"크롤링 중개사: {total_land}건")
        print(f"VWorld 중개사: {total_vworld}건")
        print(f"매칭 성공: {matched_count}건 ({matched_count/total_land*100:.1f}%)")
        print(f"매칭 실패 (크롤링): {len(unmatched_land)}건")
        print(f"매칭 실패 (VWorld): {len(unmatched_vworld)}건")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
