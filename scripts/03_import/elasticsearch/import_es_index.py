#!/usr/bin/env python
"""
Elasticsearch 인덱싱 스크립트 (ES 8.17)

매물 데이터를 JSON 파일에서 읽어 Elasticsearch에 일괄 색인합니다.

Usage:
    docker compose --profile scripts run --rm scripts python scripts/03_import/elasticsearch/import_es_index.py
    docker compose --profile scripts run --rm scripts python scripts/03_import/elasticsearch/import_es_index.py --recreate
"""
import json
import os
import sys
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add project root to path (scripts/03_import/elasticsearch -> project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Elasticsearch imports
try:
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk, BulkIndexError
except ImportError:
    print("Error: elasticsearch package not installed.")
    print("Install with: pip install elasticsearch")
    sys.exit(1)


# Constants
INDEX_NAME = os.getenv("ES_INDEX_NAME", "realestate_listings")
BATCH_SIZE = 500
JSON_FILES = [
    "00_통합_원투룸.json",
    "00_통합_빌라주택.json",
    "00_통합_아파트.json",
    "00_통합_오피스텔.json",
]


def get_es_client(host: str = None) -> Elasticsearch:
    """Elasticsearch 8.17 클라이언트 생성"""
    if host is None:
        host = os.environ.get("ELASTICSEARCH_HOST", "localhost")
    
    if not host.startswith("http"):
        port = os.environ.get("ELASTICSEARCH_PORT", "9200")
        host = f"http://{host}:{port}"
    
    return Elasticsearch(hosts=[host], request_timeout=30)


def parse_price(price_str: str) -> int:
    """가격 문자열을 만원 단위 정수로 변환"""
    if not price_str or price_str == "-" or price_str == "정보없음":
        return 0
    
    price_str = price_str.replace(",", "").replace(" ", "")
    total = 0
    
    if "억" in price_str:
        match = re.search(r"(\d+)억", price_str)
        if match:
            total += int(match.group(1)) * 10000
    
    match = re.search(r"(\d+)만원?", price_str)
    if match:
        total += int(match.group(1))
    
    return total


def transform_to_es_doc(listing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """매물 데이터를 ES 문서로 변환"""
    land_num = listing.get("매물번호")
    if not land_num:
        return None
    
    coords = listing.get("좌표_정보", {})
    trade_info = listing.get("거래_정보", {})
    address_info = listing.get("주소_정보", {})
    property_info = listing.get("매물_정보", {})
    
    lat = coords.get("위도", 0)
    lon = coords.get("경도", 0)
    
    location = None
    if lat and lon and lat != 0 and lon != 0:
        location = {"lat": float(lat), "lon": float(lon)}
    
    return {
        "_index": INDEX_NAME,
        "_id": str(land_num),
        "_source": {
            "land_num": str(land_num),
            "address": address_info.get("전체주소", ""),
            "search_text": listing.get("search_text", ""),
            "style_tags": listing.get("style_tags", []),
            "building_type": property_info.get("건물형태", ""),
            "deal_type": trade_info.get("거래유형", ""),
            "deposit": parse_price(trade_info.get("보증금", "0")),
            "monthly_rent": parse_price(trade_info.get("월세", "0")),
            "jeonse_price": parse_price(trade_info.get("전세", "0")),
            "sale_price": parse_price(trade_info.get("매매가", "0")),
            "location": location,
            "url": listing.get("매물_URL", ""),
        },
    }


def load_listings_from_json(data_dir: str) -> Tuple[List[Dict[str, Any]], int]:
    """JSON 파일에서 매물 데이터를 로드"""
    data_path = Path(data_dir)
    all_listings = []
    
    for filename in JSON_FILES:
        filepath = data_path / filename
        if filepath.exists():
            print(f"  Loading {filename}...")
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_listings.extend(data)
                print(f"    ✓ {len(data)} listings")
        else:
            print(f"  ⚠ {filename} not found")
    
    return all_listings, len(all_listings)


def create_index_if_not_exists(es: Elasticsearch) -> bool:
    """인덱스가 없으면 생성 (ES 8.17 네이티브 API)"""
    if es.indices.exists(index=INDEX_NAME):
        print(f"  ⏭ Index '{INDEX_NAME}' already exists")
        return False
    
    # 매핑 파일 경로
    mapping_path = Path(__file__).parent.parent.parent / "infra" / "elasticsearch" / "mappings" / "listings.json"
    
    if mapping_path.exists():
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping_config = json.load(f)
        
        es.indices.create(
            index=INDEX_NAME, 
            settings=mapping_config.get("settings", {}),
            mappings=mapping_config.get("mappings", {})
        )
        print(f"  ✓ Index '{INDEX_NAME}' created (ES 8.17 dense_vector + HNSW)")
    else:
        es.indices.create(index=INDEX_NAME)
        print(f"  ✓ Index '{INDEX_NAME}' created (default mapping)")
    
    return True


def delete_index(es: Elasticsearch) -> bool:
    """인덱스 삭제"""
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"  ✓ Index '{INDEX_NAME}' deleted")
        return True
    return False


def check_existing_count(es: Elasticsearch) -> int:
    """기존 인덱싱된 문서 수 확인"""
    try:
        if not es.indices.exists(index=INDEX_NAME):
            return 0
        return es.count(index=INDEX_NAME)["count"]
    except Exception:
        return 0


def bulk_index_with_progress(
    es: Elasticsearch,
    listings: List[Dict[str, Any]],
    batch_size: int = BATCH_SIZE,
) -> Tuple[int, int]:
    """배치 단위로 ES에 색인 (진행률 표시)"""
    total_success = 0
    total_failed = 0
    total_listings = len(listings)
    batch = []
    processed = 0
    
    for listing in listings:
        doc = transform_to_es_doc(listing)
        if doc:
            batch.append(doc)
        processed += 1
        
        if len(batch) >= batch_size:
            success, failed = _index_batch(es, batch)
            total_success += success
            total_failed += failed
            progress_pct = processed * 100 // total_listings
            print(f"  Progress: {processed}/{total_listings} ({progress_pct}%) - {total_success} indexed")
            batch = []
    
    if batch:
        success, failed = _index_batch(es, batch)
        total_success += success
        total_failed += failed
        print(f"  Progress: {total_listings}/{total_listings} (100%) - {total_success} indexed")
    
    return total_success, total_failed


def _index_batch(es: Elasticsearch, batch: List[Dict]) -> Tuple[int, int]:
    """단일 배치 색인"""
    try:
        success, errors = bulk(es, batch, raise_on_error=False)
        failed = len(errors) if errors else 0
        return success, failed
    except BulkIndexError:
        return 0, len(batch)
    except Exception as e:
        print(f"    Batch error: {e}")
        return 0, len(batch)


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ES 인덱싱 스크립트")
    parser.add_argument("--recreate", action="store_true", help="인덱스 재생성")
    parser.add_argument("--force", action="store_true", help="기존 데이터 있어도 강제 실행")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()
    
    print("=" * 60)
    print("Elasticsearch 인덱싱 (ES 8.17)")
    print("=" * 60)
    
    # 데이터 디렉토리 자동 감지
    if os.path.exists("/app/data/RDB/land"):
        data_dir = "/app/data/RDB/land"
        print("Docker 환경: /app/data/RDB/land")
    else:
        data_dir = str(Path(__file__).parent.parent.parent / "data" / "RDB" / "land")
        print(f"로컬 환경: {data_dir}")
    
    # ES 연결
    print("\n[1/3] Elasticsearch 연결...")
    try:
        es = get_es_client()
        info = es.info()
        print(f"  ✓ Connected (v{info['version']['number']})")
    except Exception as e:
        print(f"  ✗ 연결 실패: {e}")
        sys.exit(1)
    
    # 기존 데이터 확인
    existing_count = check_existing_count(es)
    if existing_count > 0 and not args.force and not args.recreate:
        print(f"\n  ⏭ 이미 {existing_count}개 문서 존재. 스킵합니다.")
        print("  (--recreate 또는 --force 옵션 사용)")
        return
    
    # 인덱스 생성/재생성
    print("\n[2/3] 인덱스 준비...")
    if args.recreate:
        delete_index(es)
    create_index_if_not_exists(es)
    
    # 데이터 로드 및 인덱싱
    print(f"\n[3/3] 데이터 인덱싱...")
    listings, total_count = load_listings_from_json(data_dir)
    print(f"  총 {total_count}개 매물")
    
    start_time = time.time()
    success, failed = bulk_index_with_progress(es, listings, args.batch_size)
    elapsed = time.time() - start_time
    
    # 결과 출력
    es.indices.refresh(index=INDEX_NAME)
    count = es.count(index=INDEX_NAME)["count"]
    
    print("\n" + "=" * 60)
    print(f"✓ 완료: {success}개 성공, {failed}개 실패")
    print(f"  인덱스 문서 수: {count}")
    print(f"  소요 시간: {elapsed:.1f}초")
    print("=" * 60)


if __name__ == "__main__":
    main()
