#!/usr/bin/env python
"""
Geocoding Script - 매물 주소를 좌표로 변환

통합 JSON 파일에서 매물 주소를 읽어 geocoding하고,
전체 매물 데이터에 좌표를 추가하여 저장합니다.
위/경도가 null인 매물은 자동으로 제거됩니다.

사용법:
    python geocode_addresses.py

출력:
    data/preprocessing/00_통합_아파트.json
    data/preprocessing/00_통합_원투룸.json
    data/preprocessing/00_통합_빌라주택.json
    data/preprocessing/00_통합_오피스텔.json
"""

import json
import os
import sys
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ======================================================
# .env 파일 로드
# ======================================================

# 프로젝트 루트 경로 찾기 (SKN18-FINAL-1TEAM)
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent  # scripts/dataCrawling/피터팬 매물 데이터 → 프로젝트 루트

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ .env 파일 로드됨: {env_path}")
    else:
        print(f"⚠️ .env 파일을 찾을 수 없습니다: {env_path}")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않았습니다. pip install python-dotenv")

# ======================================================
# 설정
# ======================================================

# Kakao API 키 (.env 파일 또는 환경변수에서 로드)
KAKAO_API_KEY = os.environ.get("KAKAO_API_KEY", "")

# Geocoding API 선택: 'kakao' 또는 'naver'
GEOCODING_SERVICE = "kakao"

# API 호출 간격 (초) - Rate Limit 방지
API_DELAY = 0.1

# 재시도 횟수
MAX_RETRIES = 3

# 실패한 항목 재시도 횟수
MAX_RETRY_ATTEMPTS = 2

# 재시도 대기 시간 (초)
RETRY_DELAY = 2



# ======================================================
# Geocoding 함수들
# ======================================================

def geocode_kakao(address: str) -> Optional[Tuple[float, float]]:
    """
    카카오 API를 사용한 geocoding
    
    Returns:
        (latitude, longitude) 또는 None
    """
    if not KAKAO_API_KEY:
        print("❌ 카카오 API 키가 설정되지 않았습니다.")
        print("   .env 파일에 KAKAO_API_KEY를 설정하세요.")
        return None
    
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": address}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("documents"):
                    doc = data["documents"][0]
                    lat = float(doc.get("y", 0))
                    lng = float(doc.get("x", 0))
                    if lat and lng:
                        return (lat, lng)
            elif response.status_code == 401:
                print("❌ 카카오 API 키가 유효하지 않습니다.")
                return None
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            print(f"  [오류] geocoding 실패: {e}")
    
    return None


def geocode_naver(address: str, client_id: str, client_secret: str) -> Optional[Tuple[float, float]]:
    """
    네이버 API를 사용한 geocoding
    
    Returns:
        (latitude, longitude) 또는 None
    """
    url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret
    }
    params = {"query": address}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("addresses"):
                addr = data["addresses"][0]
                lat = float(addr.get("y", 0))
                lng = float(addr.get("x", 0))
                if lat and lng:
                    return (lat, lng)
    except Exception as e:
        print(f"  [오류] geocoding 실패: {e}")
    
    return None


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """주소를 좌표로 변환"""
    if not address:
        return None
    
    # 주소 정제 (불필요한 부분 제거)
    clean_address = address.strip()
    
    if GEOCODING_SERVICE == "kakao":
        return geocode_kakao(clean_address)
    else:
        print("❌ 지원되지 않는 geocoding 서비스입니다.")
        return None


# ======================================================
# 메인 처리 함수
# ======================================================

def process_category(input_dir: str, output_dir: str, filename: str) -> Dict:
    """
    카테고리별 매물 geocoding 처리
    
    Returns:
        처리 결과 통계
    """
    input_path = os.path.join(input_dir, filename)
    output_path = os.path.join(output_dir, filename)
    
    if not os.path.exists(input_path):
        print(f"  ⚠️ 파일 없음: {filename}")
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0, "removed": 0}
    
    # 기존 처리된 데이터 로드 (이어서 처리하기 위해)
    existing_listings = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                # 기존 데이터를 매물번호로 인덱싱
                for item in existing_data:
                    listing_id = item.get("매물번호")
                    if listing_id:
                        existing_listings[listing_id] = item
            print(f"  📂 기존 데이터 {len(existing_listings)}개 로드됨")
        except Exception as e:
            print(f"  ⚠️ 기존 데이터 로드 실패: {e}")
    
    # 매물 데이터 로드
    with open(input_path, 'r', encoding='utf-8') as f:
        listings = json.load(f)
    
    if not isinstance(listings, list):
        print(f"  ❌ 잘못된 파일 형식: {filename}")
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0, "removed": 0}
    
    print(f"  📊 총 {len(listings)}개 매물 처리 시작...")
    
    # 결과 저장용 리스트
    results = []
    failed_items = []  # 실패한 항목 추적
    stats = {"total": len(listings), "success": 0, "failed": 0, "skipped": 0, "removed": 0}
    
    for i, listing in enumerate(listings):
        listing_id = listing.get("매물번호")
        if not listing_id:
            stats["failed"] += 1
            continue
        
        # 1. 기존에 처리된 데이터가 있고 좌표가 유효한 경우 재사용
        if listing_id in existing_listings:
            existing_item = existing_listings[listing_id]
            coords_info = existing_item.get("좌표_정보", {})
            
            # 좌표가 유효한 경우에만 재사용
            if coords_info and coords_info.get("위도") and coords_info.get("경도"):
                results.append(existing_item)
                stats["skipped"] += 1
                continue
            # 좌표가 없으면 다시 시도
        
        # 2. 좌표가 없다면 Geocoding 수행
        address_info = listing.get("주소_정보", {})
        address = address_info.get("전체주소", "") if isinstance(address_info, dict) else ""
        
        if not address:
            stats["failed"] += 1
            failed_items.append({"listing": listing, "address": address})
            continue
        
        # API 호출
        coords = geocode_address(address)
        
        if coords:
            lat, lng = coords
            
            # 전체 매물 데이터에 좌표 추가
            listing_with_coords = listing.copy()
            listing_with_coords["좌표_정보"] = {
                "위도": lat,
                "경도": lng
            }
            results.append(listing_with_coords)
            stats["success"] += 1
        else:
            # 실패한 항목 기록
            stats["failed"] += 1
            failed_items.append({"listing": listing, "address": address})
        
        # 진행 상황 출력
        if (i + 1) % 100 == 0:
            print(f"    진행: {i + 1}/{len(listings)} ({stats['success']} 성공, {stats['failed']} 실패)")
        
        # API Rate Limit
        if coords:  # API 호출했을 때만 딜레이
            time.sleep(API_DELAY)
    
    # 3. 실패한 항목 재시도
    if failed_items:
        print(f"\n  🔄 실패한 {len(failed_items)}개 항목 재시도 중...")
        retry_success = 0
        
        for attempt in range(MAX_RETRY_ATTEMPTS):
            if not failed_items:
                break
                
            print(f"    재시도 {attempt + 1}/{MAX_RETRY_ATTEMPTS}회차...")
            time.sleep(RETRY_DELAY)  # 재시도 전 대기
            
            still_failed = []
            
            for item_data in failed_items:
                listing = item_data["listing"]
                address = item_data["address"]
                
                if not address:
                    still_failed.append(item_data)
                    continue
                
                coords = geocode_address(address)
                
                if coords:
                    lat, lng = coords
                    listing_with_coords = listing.copy()
                    listing_with_coords["좌표_정보"] = {
                        "위도": lat,
                        "경도": lng
                    }
                    results.append(listing_with_coords)
                    retry_success += 1
                    stats["success"] += 1
                    stats["failed"] -= 1
                    time.sleep(API_DELAY)
                else:
                    still_failed.append(item_data)
            
            failed_items = still_failed
            
            if retry_success > 0:
                print(f"    재시도 성공: {retry_success}개")
        
        if failed_items:
            print(f"    최종 실패: {len(failed_items)}개 (좌표 없이 제거됨)")
            stats["removed"] = len(failed_items)
    
    # 4. 결과 저장 (좌표가 있는 매물만)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ 저장 완료: {filename}")
    print(f"     성공: {stats['success']}, 실패(제거): {stats['removed']}, 스킵: {stats['skipped']}")
    
    return stats


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🌍 매물 주소 Geocoding 시작")
    print("=" * 60)
    
    # 입력 경로: /data/crawling
    input_dir = project_root / "data" / "crawling"
    
    # 출력 경로: data/preprocessing
    output_dir = project_root / "data" / "preprocessing"
    
    if not input_dir.exists():
        print(f"❌ 오류: 입력 폴더를 찾을 수 없습니다: {input_dir}")
        return
    
    # 출력 폴더가 없으면 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 출력 폴더 준비 완료: {output_dir}")
    
    print(f"📂 입력: {input_dir}")
    print(f"📂 출력: {output_dir}")
    
    input_dir = str(input_dir)
    output_dir = str(output_dir)
    
    # API 키 확인
    if not KAKAO_API_KEY:
        print("\n⚠️ 카카오 API 키가 설정되지 않았습니다.")
        print("   프로젝트 루트의 .env 파일에 KAKAO_API_KEY를 설정하세요.")
        print("   예: KAKAO_API_KEY=발급받은REST_API_키\n")
        return
    
    category_map = {
        "아파트": "00_통합_아파트.json",
        # "원투룸": "00_통합_원투룸.json",
        # "빌라주택": "00_통합_빌라주택.json",
        # "오피스텔": "00_통합_오피스텔.json"
    }
    
    total_stats = {"total": 0, "success": 0, "failed": 0, "skipped": 0, "removed": 0}
    
    for category, filename in category_map.items():
        print(f"\n>> 카테고리: {category}")
        stats = process_category(input_dir, output_dir, filename)
        
        for key in total_stats:
            total_stats[key] += stats[key]
    
    print("\n" + "=" * 60)
    print("🎉 Geocoding 완료!")
    print("=" * 60)
    print(f"📊 전체 통계:")
    print(f"   총 매물: {total_stats['total']}개")
    print(f"   성공 (좌표 추가): {total_stats['success']}개")
    print(f"   제거 (좌표 없음): {total_stats['removed']}개")
    print(f"   스킵 (기존): {total_stats['skipped']}개")
    print(f"\n💡 최종 저장된 매물: {total_stats['success'] + total_stats['skipped']}개")


if __name__ == "__main__":
    main()
