#!/usr/bin/env python
"""
Elasticsearch 단독 검색 테스트 스크립트

ES만의 검색 성능을 테스트합니다 (Neo4j 없이).

사용법:
    python test_es_search.py "강남역 원룸"
    python test_es_search.py "역세권 풀옵션" --max-deposit 5000
    python test_es_search.py "신축 오피스텔" --tags 풀옵션,역세권
"""
import argparse
import json
import time
import sys
import requests


class SimpleESClient:
    """requests 기반 간단한 ES 클라이언트 (버전 호환성 문제 회피)"""
    
    def __init__(self, host: str = "localhost"):
        if not host.startswith("http"):
            host = f"http://{host}:9200"
        self.base_url = host
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def info(self) -> dict:
        """ES 정보 조회"""
        resp = requests.get(self.base_url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    
    def count(self, index: str) -> dict:
        """문서 수 조회"""
        resp = requests.get(
            f"{self.base_url}/{index}/_count",
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    
    def search(self, index: str, query: dict, size: int = 10, source: list = None) -> dict:
        """검색 실행"""
        body = {"query": query, "size": size}
        if source:
            body["_source"] = source
        
        resp = requests.post(
            f"{self.base_url}/{index}/_search",
            headers=self.headers,
            json=body,
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()


def get_es_client(host: str = "localhost") -> SimpleESClient:
    """ES 클라이언트 생성"""
    return SimpleESClient(host)


def search_es(
    es: SimpleESClient,
    keyword: str = None,
    style_tags: list = None,
    min_deposit: int = None,
    max_deposit: int = None,
    deal_type: str = None,
    size: int = 10
) -> dict:
    """ES 검색 실행"""
    
    query = {"bool": {"must": [], "filter": [], "should": []}}
    
    # 키워드 검색
    if keyword:
        query["bool"]["must"].append({
            "match": {
                "search_text": {
                    "query": keyword,
                    "analyzer": "nori_analyzer"
                }
            }
        })
    
    # 스타일 태그 필터
    if style_tags:
        query["bool"]["filter"].append({
            "terms": {"style_tags": style_tags}
        })
    
    # 보증금 범위 필터
    if min_deposit is not None or max_deposit is not None:
        range_query = {"range": {"deposit": {}}}
        if min_deposit is not None:
            range_query["range"]["deposit"]["gte"] = min_deposit
        if max_deposit is not None:
            range_query["range"]["deposit"]["lte"] = max_deposit
        query["bool"]["filter"].append(range_query)
    
    # 거래 유형 필터
    if deal_type:
        query["bool"]["filter"].append({
            "term": {"deal_type": deal_type}
        })
    
    # 검색 실행
    start_time = time.time()
    response = es.search(
        index="realestate_listings",
        query=query,
        size=size,
        source=["land_num", "address", "search_text", "style_tags", 
                "deal_type", "deposit", "monthly_rent", "building_type"]
    )
    elapsed_ms = (time.time() - start_time) * 1000
    
    return {
        "total": response["hits"]["total"]["value"],
        "took_ms": response["took"],
        "client_ms": round(elapsed_ms, 2),
        "hits": response["hits"]["hits"]
    }


def print_results(results: dict, keyword: str):
    """결과 출력"""
    print("\n" + "=" * 70)
    print(f"🔍 ES 검색 결과: '{keyword}'")
    print("=" * 70)
    print(f"📊 총 {results['total']}건 검색됨")
    print(f"⏱️  ES 처리 시간: {results['took_ms']}ms")
    print(f"⏱️  클라이언트 시간: {results['client_ms']}ms")
    print("-" * 70)
    
    if not results["hits"]:
        print("❌ 검색 결과가 없습니다.")
        return
    
    for i, hit in enumerate(results["hits"], 1):
        source = hit["_source"]
        score = hit["_score"]
        
        print(f"\n[{i}] 점수: {score:.2f}")
        print(f"    매물번호: {source.get('land_num', 'N/A')}")
        print(f"    주소: {source.get('address', 'N/A')}")
        print(f"    건물유형: {source.get('building_type', 'N/A')}")
        print(f"    거래유형: {source.get('deal_type', 'N/A')}")
        
        deposit = source.get('deposit', 0)
        monthly = source.get('monthly_rent', 0)
        if deposit or monthly:
            print(f"    가격: 보증금 {deposit}만원 / 월세 {monthly}만원")
        
        tags = source.get('style_tags', [])
        if tags:
            print(f"    태그: {', '.join(tags[:5])}")
        
        search_text = source.get('search_text', '')
        if search_text:
            print(f"    검색텍스트: {search_text[:100]}...")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="ES 단독 검색 테스트")
    parser.add_argument("keyword", nargs="?", help="검색 키워드")
    parser.add_argument("--es-host", default="localhost", help="ES 호스트")
    parser.add_argument("--min-deposit", type=int, help="최소 보증금 (만원)")
    parser.add_argument("--max-deposit", type=int, help="최대 보증금 (만원)")
    parser.add_argument("--tags", help="스타일 태그 (쉼표 구분)")
    parser.add_argument("--deal-type", help="거래유형 (월세/전세/매매)")
    parser.add_argument("--size", type=int, default=10, help="결과 개수")
    parser.add_argument("--interactive", "-i", action="store_true", help="대화형 모드")
    
    args = parser.parse_args()
    
    # ES 연결
    print(f"🔌 ES 연결 중... ({args.es_host})")
    try:
        es = get_es_client(args.es_host)
        info = es.info()
        print(f"✅ ES 연결 성공 (버전: {info['version']['number']})")
        
        # 인덱스 문서 수 확인
        count = es.count(index="realestate_listings")["count"]
        print(f"📦 인덱스 문서 수: {count}건")
    except Exception as e:
        print(f"❌ ES 연결 실패: {e}")
        sys.exit(1)
    
    # 대화형 모드
    if args.interactive or not args.keyword:
        print("\n💬 대화형 모드 (종료: quit 또는 Ctrl+C)")
        print("   예시: 강남역 원룸")
        print("   예시: 역세권 풀옵션 --max-deposit 5000")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n🔍 검색어: ").strip()
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 종료합니다.")
                    break
                
                if not user_input:
                    continue
                
                # 간단한 파싱
                parts = user_input.split("--")
                keyword = parts[0].strip()
                
                max_deposit = None
                tags = None
                
                for part in parts[1:]:
                    if part.startswith("max-deposit"):
                        try:
                            max_deposit = int(part.split()[1])
                        except:
                            pass
                    elif part.startswith("tags"):
                        try:
                            tags = part.split()[1].split(",")
                        except:
                            pass
                
                results = search_es(
                    es, 
                    keyword=keyword,
                    max_deposit=max_deposit,
                    style_tags=tags,
                    size=args.size
                )
                print_results(results, keyword)
                
            except KeyboardInterrupt:
                print("\n👋 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 오류: {e}")
    else:
        # 단일 검색
        tags = args.tags.split(",") if args.tags else None
        
        results = search_es(
            es,
            keyword=args.keyword,
            style_tags=tags,
            min_deposit=args.min_deposit,
            max_deposit=args.max_deposit,
            deal_type=args.deal_type,
            size=args.size
        )
        print_results(results, args.keyword)


if __name__ == "__main__":
    main()
