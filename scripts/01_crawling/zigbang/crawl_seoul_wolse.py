"""
직방 서울 월세 원룸 크롤러 (병렬 처리 버전)
============================================
- 병렬 처리로 빠른 수집
- 300개마다 자동 저장
- API 차단 시 자동 대기 후 재시도
- 진행률 및 예상 시간 표시

사용법:
    python crawl_seoul_wolse.py          # 서울 전역
    python crawl_seoul_wolse.py --test   # 테스트 (100개만)
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 세션 설정 (연결 풀 + 재시도)
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=200, pool_maxsize=200)
session.mount("https://", adapter)

# ======================================================
# 1. 설정
# ======================================================

ZIGBANG_API = {
    "geohash": "https://apis.zigbang.com/v2/items/oneroom",
    "item_detail": "https://apis.zigbang.com/v3/items/{item_id}",
}

# 서울 전체 25개 구를 커버하는 geohash 목록
SEOUL_GEOHASHES = [
    # 기존
    "wydm6", "wydm7", "wydm4", "wydm5", "wydm1",
    "wydmd", "wydme", "wydmf", "wydmg", "wydm9",
    "wydmc", "wydm8", "wydjb", "wydjc",
    # 추가 (누락된 구 커버)
    "wydm2",  # 동작구
    "wydmb",  # 은평구
    "wydms",  # 강동구
    "wydq5",  # 노원구
    "wydq7",  # 도봉구
    "wydjp",  # 금천구
    "wydjq",  # 양천구
    "wydjr",  # 구로구, 영등포구
    "wydjw",  # 강서구
    "wydmt",  # 강동구 추가
    "wydmk",  # 송파구 추가
    "wydq4",  # 노원구 추가
    "wydq1",  # 도봉구 추가
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://www.zigbang.com",
    "Referer": "https://www.zigbang.com/",
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# 병렬 처리 설정
MAX_WORKERS = 50  # 동시 요청 수
SAVE_INTERVAL = 50  # 저장 간격
MAX_RETRIES = 3  # 최대 재시도 횟수
RETRY_DELAY = 30  # 재시도 대기 시간 (초)


# ======================================================
# 2. API 호출 함수
# ======================================================

def get_retry_after(response) -> int:
    """응답에서 Retry-After 헤더 읽기"""
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return int(retry_after)
        except ValueError:
            pass
    return RETRY_DELAY  # 기본값


def get_item_ids_by_geohash(geohash: str) -> List[int]:
    """geohash 기반으로 월세 매물 ID 목록 조회"""
    url = ZIGBANG_API["geohash"]
    params = {
        "geohash": geohash,
        "depositMin": 0,
        "depositMax": 50000,
        "rentMin": 1,
        "rentMax": 9999999,
        "salesTypes[0]": "월세",
        "domain": "zigbang",
        "checkAny498": "true",
    }
    
    for retry in range(MAX_RETRIES):
        try:
            response = session.get(url, params=params, headers=HEADERS, timeout=30)
            
            if response.status_code == 429:  # Too Many Requests
                wait_time = get_retry_after(response)
                print(f"  ⚠️ API 제한 감지, {wait_time}초 대기 중...")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            item_ids = [item["itemId"] for item in items if "itemId" in item]
            print(f"  [geohash: {geohash}] {len(item_ids)}개 매물 ID 발견")
            return item_ids
            
        except requests.exceptions.RequestException as e:
            if retry < MAX_RETRIES - 1:
                print(f"  ⚠️ 오류 발생, {RETRY_DELAY}초 후 재시도... ({retry + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  [오류] geohash {geohash}: {e}")
    return []


def get_item_detail(item_id: int) -> Optional[Dict[str, Any]]:
    """단일 매물 상세 정보 조회 (재시도 로직 포함)"""
    url = ZIGBANG_API["item_detail"].format(item_id=item_id)
    
    for retry in range(MAX_RETRIES):
        try:
            response = session.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code == 429:  # Too Many Requests
                wait_time = get_retry_after(response)
                print(f"\n⏳ API 제한! {wait_time}초 대기 중... (매물 {item_id}, 재시도 {retry+1}/{MAX_RETRIES})")
                time.sleep(wait_time)
                continue
                
            if response.status_code == 200:
                return response.json()
            return None
            
        except requests.exceptions.RequestException as e:
            if retry < MAX_RETRIES - 1:
                print(f"\n⚠️ 요청 오류 (매물 {item_id}): {e}, 5초 후 재시도 ({retry+1}/{MAX_RETRIES})")
                time.sleep(5)
            continue
    return None


def load_existing_ids(output_file: str) -> set:
    """기존 저장된 데이터에서 매물번호 로드"""
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_ids = {item["매물번호"] for item in data}
                return existing_ids
        except:
            pass
    return set()


# ======================================================
# 3. 데이터 변환 함수
# ======================================================

def transform_item(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """직방 API 응답을 통일된 형식으로 변환"""
    item = data.get("item", {})
    realtor = data.get("realtor", {})
    
    if not item:
        return None
    
    item_id = item.get("itemId")
    
    # 주소 정보
    address_origin = item.get("addressOrigin", {})
    jibun_address = item.get("jibunAddress", "")
    local = f"{address_origin.get('local1', '')} {address_origin.get('local2', '')} {address_origin.get('local3', '')}".strip()
    full_address = local if local else jibun_address
    
    if "서울" not in full_address:
        return None
    
    # 가격 정보
    price = item.get("price", {})
    deposit = price.get("deposit", 0)
    rent = price.get("rent", 0)
    
    # 면적 정보
    area = item.get("area", {})
    size_m2 = area.get("전용면적M2", 0)
    
    # 층 정보
    floor_info = item.get("floor", {})
    floor = floor_info.get("floor", "")
    floor_all = floor_info.get("allFloors", "")
    
    # 이미지
    images = item.get("images", [])
    
    # 관리비
    manage_cost = item.get("manageCost", {})
    manage_amount = manage_cost.get("amount", 0)
    
    # 중개사 정보
    broker_info = {}
    if realtor:
        broker_info = {
            "중개사명": realtor.get("officeTitle", ""),
            "대표자": realtor.get("name", ""),
            "전화번호": realtor.get("officePhone", ""),
            "주소": realtor.get("officeAddress", ""),
            "등록번호": realtor.get("officeRegNumber", ""),
        }
    
    return {
        "매물번호": str(item_id),
        "매물_URL": f"https://www.zigbang.com/home/oneroom/items/{item_id}",
        "매물_이미지": images[:10] if images else [],
        "주소_정보": {
            "전체주소": full_address,
            "지번주소": jibun_address,
        },
        "거래_정보": {
            "거래유형": "월세",
            "보증금": deposit,
            "월세": rent,
            "관리비": manage_amount,
            "입주가능일": item.get("moveinDate", ""),
        },
        "매물_정보": {
            "건물유형": item.get("serviceType", ""),
            "방타입": item.get("roomType", ""),
            "전용면적_m2": size_m2,
            "전용면적_평": round(size_m2 * 0.3025, 2) if size_m2 else 0,
            "층정보": f"{floor}/{floor_all}층" if floor and floor_all else "",
            "해당층": floor,
            "총층": floor_all,
            "방향": item.get("roomDirection", ""),
            "엘리베이터": item.get("elevator", False),
            "주차": item.get("parkingAvailableText", ""),
        },
        "추가_옵션": item.get("options", []),
        "위치": {
            "위도": item.get("location", {}).get("lat"),
            "경도": item.get("location", {}).get("lng"),
        },
        "중개사_정보": broker_info,
        "상세_설명": item.get("description", ""),
        "제목": item.get("title", ""),
        "수집일시": datetime.now().isoformat(),
        "출처": "직방",
    }


# ======================================================
# 4. 병렬 처리 함수
# ======================================================

def fetch_and_transform(item_id: int) -> Optional[Dict[str, Any]]:
    """단일 매물 조회 및 변환 (병렬 처리용)"""
    detail = get_item_detail(item_id)
    if detail:
        return transform_item(detail)
    return None


# ======================================================
# 5. 메인 크롤링 로직
# ======================================================

def crawl_seoul_wolse(max_items: int = None):
    """서울 전역 월세 원룸 크롤링 (병렬 처리)"""
    print("=" * 60)
    print("🏠 직방 서울 월세 원룸 크롤링 시작")
    print(f"   병렬: {MAX_WORKERS}개 | 저장간격: {SAVE_INTERVAL}개")
    print("=" * 60)
    print()
    
    start_time = time.time()
    
    # 1. 매물 ID 수집
    print("📍 Step 1: 매물 ID 수집 중...")
    all_item_ids = set()
    
    for geohash in SEOUL_GEOHASHES:
        ids = get_item_ids_by_geohash(geohash)
        all_item_ids.update(ids)
        time.sleep(0.2)
    
    print(f"\n✅ 총 {len(all_item_ids)}개 고유 매물 ID 수집 완료\n")
    
    if not all_item_ids:
        print("❌ 수집된 매물이 없습니다.")
        return []
    
    item_ids_list = list(all_item_ids)
    if max_items:
        item_ids_list = item_ids_list[:max_items]
        print(f"📌 최대 {max_items}개로 제한\n")
    
    total = len(item_ids_list)
    
    # 2. 병렬로 상세 정보 조회
    print(f"📋 Step 2: 매물 상세 정보 조회 중... (병렬 {MAX_WORKERS}개)")
    print("-" * 60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, "zigbang_seoul_wolse.json")
    
    # 기존 데이터 로드 (중복 방지)
    existing_ids = load_existing_ids(output_file)
    if existing_ids:
        print(f"📂 기존 데이터 {len(existing_ids)}개 로드됨")
        # 기존 데이터 유지
        with open(output_file, "r", encoding="utf-8") as f:
            transformed_items = json.load(f)
        # 이미 수집된 ID 제외
        item_ids_list = [id for id in item_ids_list if str(id) not in existing_ids]
        print(f"📌 새로 수집할 매물: {len(item_ids_list)}개 (중복 제외)")
    else:
        transformed_items = []
    
    if not item_ids_list:
        print("✅ 모든 매물이 이미 수집되어 있습니다.")
        return transformed_items
    
    total = len(item_ids_list)
    completed = 0
    failed = 0
    lock = threading.Lock()
    stop_flag = False
    
    def save_progress():
        """현재까지 데이터 저장"""
        with lock:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(transformed_items, f, ensure_ascii=False, indent=2)
    
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_and_transform, item_id): item_id 
                      for item_id in item_ids_list}
            
            for future in as_completed(futures):
                if stop_flag:
                    break
                    
                completed += 1
                result = future.result()
                
                if result:
                    with lock:
                        transformed_items.append(result)
                else:
                    failed += 1
                
                # 진행률 표시 (50개마다)
                if completed % 50 == 0 or completed == total:
                    elapsed = time.time() - start_time
                    speed = completed / elapsed if elapsed > 0 else 0
                    remaining = (total - completed) / speed if speed > 0 else 0
                    percent = (completed / total) * 100
                    
                    print(f"    [{completed:5d}/{total}] {percent:5.1f}% | "
                          f"성공: {len(transformed_items):5d} | "
                          f"속도: {speed:.1f}/초 | "
                          f"남은시간: {remaining/60:.1f}분")
                
                # 300개마다 중간 저장
                if completed % SAVE_INTERVAL == 0:
                    save_progress()
                    print(f"    💾 중간 저장 완료 ({len(transformed_items)}개)")
    
    except KeyboardInterrupt:
        stop_flag = True
        print(f"\n\n⚠️ 사용자 중단! 현재까지 {len(transformed_items)}개 저장 중...")
        save_progress()
        print(f"💾 저장 완료: {output_file}")
        return transformed_items
    
    # 최종 저장
    save_progress()
    
    elapsed = time.time() - start_time
    
    print()
    print("=" * 60)
    print("🎉 크롤링 완료!")
    print("=" * 60)
    print(f"📊 수집 통계:")
    print(f"   - 총 매물 수: {len(transformed_items)}개")
    print(f"   - 실패: {failed}개")
    print(f"   - 저장 파일: {output_file}")
    print(f"   - 소요 시간: {elapsed/60:.1f}분 ({elapsed:.0f}초)")
    print(f"   - 평균 속도: {len(transformed_items)/elapsed:.1f}개/초")
    
    if transformed_items:
        print()
        print("📝 샘플 데이터:")
        sample = transformed_items[0]
        print(f"   - 매물번호: {sample['매물번호']}")
        print(f"   - 주소: {sample['주소_정보']['전체주소']}")
        print(f"   - 보증금/월세: {sample['거래_정보']['보증금']}만원 / {sample['거래_정보']['월세']}만원")
    
    return transformed_items


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        crawl_seoul_wolse(max_items=100)
    else:
        crawl_seoul_wolse()
