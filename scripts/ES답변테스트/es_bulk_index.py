#!/usr/bin/env python
"""
Elasticsearch Bulk Indexing Script

매물 데이터를 JSON 파일에서 읽어 Elasticsearch에 일괄 색인합니다.

Requirements:
- 4.1: data/RDB/land/ 폴더의 JSON 파일에서 매물 조회
- 4.2: search_text와 style_tags 필드를 활용하여 ES 문서 생성
- 4.3: 1000개 단위로 배치 처리
- 4.4: 성공/실패 건수와 소요 시간 출력
"""
import json
import os
import sys
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Generator, Tuple, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Elasticsearch imports - optional for testing
ES_AVAILABLE = False
try:
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk, BulkIndexError
    ES_AVAILABLE = True
except ImportError:
    Elasticsearch = None
    bulk = None
    BulkIndexError = None


# Constants
INDEX_NAME = "realestate_listings"
BATCH_SIZE = 1000
JSON_FILES = [
    "00_통합_원투룸.json",
    "00_통합_빌라주택.json",
    "00_통합_아파트.json",
    "00_통합_오피스텔.json",
]


def get_es_client(host: str = None) -> Elasticsearch:
    """
    Elasticsearch 클라이언트 생성
    
    Args:
        host: ES 호스트 URL (기본값: 환경변수 또는 localhost:9200)
    
    Returns:
        Elasticsearch 클라이언트
    """
    if host is None:
        host = os.environ.get("ELASTICSEARCH_HOST", "localhost")
    
    # Handle both hostname and full URL
    if not host.startswith("http"):
        host = f"http://{host}:9200"
    
    return Elasticsearch(hosts=[host], request_timeout=30)


def parse_price(price_str: str) -> int:
    """
    가격 문자열을 정수로 변환
    
    Args:
        price_str: 가격 문자열 (예: "3,000만원", "1억 5,000만원", "-")
    
    Returns:
        만원 단위 정수 (예: 3000, 15000)
    """
    if not price_str or price_str == "-" or price_str == "정보없음":
        return 0
    
    # Remove commas and whitespace
    price_str = price_str.replace(",", "").replace(" ", "")
    
    total = 0
    
    # Handle 억 (100 million won = 10000 만원)
    if "억" in price_str:
        match = re.search(r"(\d+)억", price_str)
        if match:
            total += int(match.group(1)) * 10000
    
    # Handle 만원
    match = re.search(r"(\d+)만원?", price_str)
    if match:
        total += int(match.group(1))
    
    return total


def transform_to_es_doc(listing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    매물 데이터를 ES 문서로 변환
    
    Args:
        listing: 원본 매물 데이터
    
    Returns:
        ES 문서 형식의 딕셔너리 또는 None (유효하지 않은 경우)
    """
    land_num = listing.get("매물번호")
    if not land_num:
        return None
    
    coords = listing.get("좌표_정보", {})
    trade_info = listing.get("거래_정보", {})
    address_info = listing.get("주소_정보", {})
    property_info = listing.get("매물_정보", {})
    
    # Extract coordinates
    lat = coords.get("위도", 0)
    lon = coords.get("경도", 0)
    
    # Build location field (only if valid coordinates)
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


def load_listings_from_json(data_dir: str) -> Generator[Dict[str, Any], None, None]:
    """
    JSON 파일에서 매물 데이터를 로드 (제너레이터)
    
    Args:
        data_dir: 데이터 디렉토리 경로
    
    Yields:
        매물 데이터 딕셔너리
    """
    data_path = Path(data_dir)
    
    for filename in JSON_FILES:
        filepath = data_path / filename
        if filepath.exists():
            print(f"  Loading {filename}...")
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for listing in data:
                    yield listing
        else:
            print(f"  Warning: {filename} not found, skipping...")


def create_index_if_not_exists(es: Elasticsearch, mapping_path: str = None) -> bool:
    """
    인덱스가 없으면 생성
    
    Args:
        es: Elasticsearch 클라이언트
        mapping_path: 매핑 파일 경로
    
    Returns:
        인덱스 생성 여부
    """
    if es.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists.")
        return False
    
    # Load mapping from file
    if mapping_path is None:
        mapping_path = Path(__file__).parent.parent / "infra" / "elasticsearch" / "mappings" / "listings.json"
    
    mapping_path = Path(mapping_path)
    if mapping_path.exists():
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        
        es.indices.create(index=INDEX_NAME, body=mapping)
        print(f"Index '{INDEX_NAME}' created with custom mapping.")
    else:
        # Create with default mapping
        es.indices.create(index=INDEX_NAME)
        print(f"Index '{INDEX_NAME}' created with default mapping.")
    
    return True


def delete_index(es: Elasticsearch) -> bool:
    """
    인덱스 삭제
    
    Args:
        es: Elasticsearch 클라이언트
    
    Returns:
        삭제 성공 여부
    """
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"Index '{INDEX_NAME}' deleted.")
        return True
    return False


def bulk_index(
    es: Elasticsearch,
    listings: Generator[Dict[str, Any], None, None],
    batch_size: int = BATCH_SIZE,
) -> Tuple[int, int]:
    """
    배치 단위로 ES에 색인
    
    Args:
        es: Elasticsearch 클라이언트
        listings: 매물 데이터 제너레이터
        batch_size: 배치 크기
    
    Returns:
        (성공 건수, 실패 건수) 튜플
    """
    total_success = 0
    total_failed = 0
    batch = []
    batch_num = 0
    
    for listing in listings:
        doc = transform_to_es_doc(listing)
        if doc:
            batch.append(doc)
        
        if len(batch) >= batch_size:
            batch_num += 1
            success, failed = _index_batch(es, batch, batch_num)
            total_success += success
            total_failed += failed
            batch = []
    
    # Process remaining documents
    if batch:
        batch_num += 1
        success, failed = _index_batch(es, batch, batch_num)
        total_success += success
        total_failed += failed
    
    return total_success, total_failed


def _index_batch(es: Elasticsearch, batch: List[Dict], batch_num: int) -> Tuple[int, int]:
    """
    단일 배치 색인
    
    Args:
        es: Elasticsearch 클라이언트
        batch: 문서 배치
        batch_num: 배치 번호
    
    Returns:
        (성공 건수, 실패 건수) 튜플
    """
    try:
        success, errors = bulk(es, batch, raise_on_error=False)
        failed = len(errors) if errors else 0
        print(f"  Batch {batch_num}: {success} succeeded, {failed} failed")
        return success, failed
    except BulkIndexError as e:
        print(f"  Batch {batch_num}: Bulk indexing error - {len(e.errors)} errors")
        return 0, len(batch)
    except Exception as e:
        print(f"  Batch {batch_num}: Error - {e}")
        return 0, len(batch)


def main():
    """메인 실행 함수"""
    if not ES_AVAILABLE:
        print("Error: elasticsearch package not installed.")
        print("Install with: pip install elasticsearch")
        sys.exit(1)
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Elasticsearch Bulk Indexing Script")
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).parent.parent / "data" / "RDB" / "land"),
        help="Data directory path (default: data/RDB/land)",
    )
    parser.add_argument(
        "--es-host",
        default=None,
        help="Elasticsearch host (default: ELASTICSEARCH_HOST env or localhost)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size for bulk indexing (default: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate index before indexing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only count documents without indexing",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Elasticsearch Bulk Indexing Script")
    print("=" * 60)
    
    # Connect to Elasticsearch
    print(f"\nConnecting to Elasticsearch...")
    try:
        es = get_es_client(args.es_host)
        info = es.info()
        print(f"  Connected to ES version {info['version']['number']}")
    except Exception as e:
        print(f"  Error: Failed to connect to Elasticsearch - {e}")
        sys.exit(1)
    
    # Dry run mode
    if args.dry_run:
        print(f"\n[DRY RUN] Counting documents in {args.data_dir}...")
        count = sum(1 for _ in load_listings_from_json(args.data_dir))
        print(f"  Total documents: {count}")
        return
    
    # Recreate index if requested
    if args.recreate:
        print(f"\nRecreating index '{INDEX_NAME}'...")
        delete_index(es)
        create_index_if_not_exists(es)
    else:
        create_index_if_not_exists(es)
    
    # Start indexing
    print(f"\nLoading data from {args.data_dir}...")
    start_time = time.time()
    
    listings = load_listings_from_json(args.data_dir)
    success, failed = bulk_index(es, listings, args.batch_size)
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 60)
    print("Indexing Complete")
    print("=" * 60)
    print(f"  Total Success: {success}")
    print(f"  Total Failed:  {failed}")
    print(f"  Elapsed Time:  {elapsed_time:.2f} seconds")
    
    # Verify index count
    es.indices.refresh(index=INDEX_NAME)
    count = es.count(index=INDEX_NAME)["count"]
    print(f"  Index Count:   {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
