#!/usr/bin/env python
"""
벡터 검색 테스트 스크립트

시맨틱 벡터 검색 기능을 테스트합니다.

Requirements:
- 6.1: 사용자 질문을 입력받아 벡터 검색 실행
- 6.2: 유사도 점수, 매칭된 청크, 매물 정보 출력
- 6.3: 대화형 모드로 여러 질문 연속 테스트
- 6.4: 임베딩 통계 출력 (총 임베딩 수, 매물 수)

사용법:
    python test_vector_search.py "햇살 좋은 집"
    python test_vector_search.py --stats
    python test_vector_search.py --interactive
    python test_vector_search.py "조용한 동네" --top-k 5
"""
import argparse
import os
import sys
import time
from pathlib import Path

import requests

# 프로젝트 루트 경로 추가 (scripts/ES답변테스트 -> scripts -> 프로젝트루트)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env 파일 로드
from dotenv import load_dotenv
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ .env 파일 로드됨: {env_path}")
else:
    print(f"⚠️ .env 파일 없음: {env_path}")

# ES 인덱스 이름 (환경변수 또는 기본값)
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "realestate_listings")


class SimpleESClient:
    """requests 기반 간단한 ES 클라이언트"""
    
    def __init__(self, host: str = "localhost", port: str = "9200"):
        if not host.startswith("http"):
            self.base_url = f"http://{host}:{port}"
        else:
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
    
    def count(self, index: str, query: dict = None) -> int:
        """문서 수 조회"""
        url = f"{self.base_url}/{index}/_count"
        if query:
            resp = requests.post(url, headers=self.headers, json={"query": query}, timeout=10)
        else:
            resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()["count"]
    
    def knn_search(
        self, 
        index: str, 
        query_vector: list, 
        k: int = 10, 
        min_score: float = 0.3,
        source: list = None
    ) -> dict:
        """kNN 벡터 검색"""
        body = {
            "knn": {
                "field": "embedding",
                "query_vector": query_vector,
                "k": k,
                "num_candidates": k * 2
            },
            "min_score": min_score,
            "size": k
        }
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
    
    def hybrid_search(
        self,
        index: str,
        query: str,
        query_vector: list,
        k: int = 10,
        keyword_boost: float = 0.4,
        vector_boost: float = 0.6,
        source: list = None
    ) -> dict:
        """하이브리드 검색 (키워드 + 벡터)"""
        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["search_text^2", "style_tags"],
                                "boost": keyword_boost
                            }
                        }
                    ]
                }
            },
            "knn": {
                "field": "embedding",
                "query_vector": query_vector,
                "k": k,
                "num_candidates": k * 2,
                "boost": vector_boost
            },
            "size": k
        }
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
    
    def keyword_search(
        self,
        index: str,
        query: str,
        k: int = 10,
        source: list = None
    ) -> dict:
        """키워드 검색만"""
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["search_text^2", "style_tags"]
                }
            },
            "size": k
        }
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


def get_es_client() -> SimpleESClient:
    """ES 클라이언트 생성"""
    host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    port = os.getenv("ELASTICSEARCH_PORT", "9200")
    return SimpleESClient(host, port)


def get_embedding(text: str) -> list:
    """OpenAI 임베딩 생성"""
    from openai import OpenAI
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding


def show_stats():
    """임베딩 통계 출력 (Requirements 6.4)"""
    print("\n" + "=" * 60)
    print("📊 임베딩 통계")
    print("=" * 60)
    
    try:
        es = get_es_client()
        
        # ES 연결 확인
        info = es.info()
        print(f"✅ ES 연결 성공 (버전: {info['version']['number']})")
        
        # 전체 문서 수
        print(f"📌 인덱스: {ES_INDEX_NAME}")
        total = es.count(index=ES_INDEX_NAME)
        print(f"\n📦 전체 매물: {total:,}건")
        
        # 임베딩 있는 문서 수
        with_embedding = es.count(
            index=ES_INDEX_NAME,
            query={"exists": {"field": "embedding"}}
        )
        print(f"✅ 임베딩 완료: {with_embedding:,}건")
        
        # 미완료 문서 수
        without_embedding = total - with_embedding
        print(f"⏳ 미완료: {without_embedding:,}건")
        
        # 완료율
        if total > 0:
            completion_rate = (with_embedding / total) * 100
            print(f"\n📈 완료율: {completion_rate:.1f}%")
        
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ ES 연결 실패: Elasticsearch에 연결할 수 없습니다.")
        print("   ELASTICSEARCH_HOST, ELASTICSEARCH_PORT 환경변수를 확인하세요.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)


def search_and_print(query: str, top_k: int = 10, min_score: float = 0.3, full_text: bool = False, mode: str = "vector"):
    """검색 실행 및 결과 출력 (Requirements 6.1, 6.2)
    
    Args:
        mode: "vector" (벡터만), "keyword" (키워드만), "hybrid" (하이브리드)
    """
    mode_names = {"vector": "🔮 벡터", "keyword": "🔤 키워드", "hybrid": "🔀 하이브리드"}
    print(f"\n{mode_names.get(mode, '🔍')} 검색어: '{query}'")
    print("-" * 60)
    
    try:
        es = get_es_client()
        embed_time = 0
        query_embedding = None
        
        # 임베딩 생성 (벡터/하이브리드 모드)
        if mode in ["vector", "hybrid"]:
            print("⏳ 쿼리 임베딩 생성 중...")
            start_embed = time.time()
            query_embedding = get_embedding(query)
            embed_time = (time.time() - start_embed) * 1000
            print(f"✅ 임베딩 완료 ({embed_time:.0f}ms)")
        
        # 검색 실행
        print(f"⏳ {mode} 검색 중...")
        start_search = time.time()
        
        if mode == "vector":
            result = es.knn_search(
                index=ES_INDEX_NAME,
                query_vector=query_embedding,
                k=top_k,
                min_score=min_score,
                source=["search_text", "land_num", "주소_정보", "style_tags"]
            )
        elif mode == "keyword":
            result = es.keyword_search(
                index=ES_INDEX_NAME,
                query=query,
                k=top_k,
                source=["search_text", "land_num", "주소_정보", "style_tags"]
            )
        else:  # hybrid
            result = es.hybrid_search(
                index=ES_INDEX_NAME,
                query=query,
                query_vector=query_embedding,
                k=top_k,
                keyword_boost=0.6,
                vector_boost=0.4,
                source=["search_text", "land_num", "주소_정보", "style_tags"]
            )
        
        search_time = (time.time() - start_search) * 1000
        
        hits = result["hits"]["hits"]
        total_time = embed_time + search_time
        
        print(f"✅ 검색 완료 ({search_time:.0f}ms)")
        print(f"⏱️  총 소요 시간: {total_time:.0f}ms")
        print("-" * 60)
        
        if not hits:
            print("❌ 검색 결과가 없습니다.")
            print(f"   (min_score: {min_score} 이상의 결과가 없음)")
            return
        
        print(f"📋 검색 결과: {len(hits)}건")
        if full_text:
            print("📝 전문 보기 모드 활성화")
        print("=" * 60)
        
        for i, hit in enumerate(hits, 1):
            source = hit["_source"]
            score = hit["_score"]
            
            print(f"\n[{i}] 유사도 점수: {score:.4f}")
            print(f"    매물번호: {source.get('land_num', hit['_id'])}")
            
            # 주소 정보
            addr_info = source.get("주소_정보", {})
            if isinstance(addr_info, dict):
                full_addr = addr_info.get("전체주소", "")
                if full_addr:
                    print(f"    주소: {full_addr}")
            
            # 스타일 태그
            tags = source.get("style_tags", [])
            if tags:
                tag_str = ", ".join(tags[:5])
                if len(tags) > 5:
                    tag_str += f" 외 {len(tags) - 5}개"
                print(f"    태그: {tag_str}")
            
            # 검색 텍스트 (매칭된 청크)
            search_text = source.get("search_text", "")
            if search_text:
                if full_text:
                    # 전문 출력
                    print(f"\n    ┌{'─' * 56}┐")
                    print(f"    │ 📄 청크 전문 ({len(search_text)}자)")
                    print(f"    ├{'─' * 56}┤")
                    # 줄바꿈 처리하여 출력
                    lines = search_text.split('\n')
                    for line in lines:
                        # 긴 줄은 54자씩 나눠서 출력
                        while len(line) > 54:
                            print(f"    │ {line[:54]} │")
                            line = line[54:]
                        print(f"    │ {line.ljust(54)} │")
                    print(f"    └{'─' * 56}┘")
                else:
                    # 100자로 제한
                    display_text = search_text[:100]
                    if len(search_text) > 100:
                        display_text += "..."
                    print(f"    내용: {display_text}")
        
        print("\n" + "=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ ES 연결 실패: Elasticsearch에 연결할 수 없습니다.")
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()


def interactive_mode(top_k: int = 10, min_score: float = 0.3, full_text: bool = False, mode: str = "vector"):
    """대화형 모드 (Requirements 6.3)"""
    print("\n" + "=" * 60)
    print("💬 대화형 검색 모드")
    print("=" * 60)
    print("   예시: 햇살 좋은 집")
    print("   예시: 조용한 동네 원룸")
    print("   예시: 역세권 신축 오피스텔")
    print("-" * 60)
    print("   명령어:")
    print("   /full    - 전문 보기 모드 토글")
    print("   /top N   - 결과 개수 변경 (예: /top 5)")
    print("   /score N - 최소 점수 변경 (예: /score 0.5)")
    print("   /mode    - 검색 모드 변경 (vector/keyword/hybrid)")
    print("   종료: quit, exit, q 또는 Ctrl+C")
    print("-" * 60)
    
    current_full_text = full_text
    current_top_k = top_k
    current_min_score = min_score
    current_mode = mode
    
    mode_icons = {"vector": "🔮", "keyword": "🔤", "hybrid": "🔀"}
    
    while True:
        try:
            full_indicator = "📝" if current_full_text else "📋"
            mode_icon = mode_icons.get(current_mode, "🔍")
            query = input(f"\n{full_indicator}{mode_icon} 검색어 ({current_mode}, top_k={current_top_k}): ").strip()
            
            if query.lower() in ["quit", "exit", "q"]:
                print("👋 종료합니다.")
                break
            
            if not query:
                continue
            
            # 명령어 처리
            if query.startswith("/"):
                if query == "/full":
                    current_full_text = not current_full_text
                    status = "활성화" if current_full_text else "비활성화"
                    print(f"✅ 전문 보기 모드 {status}")
                    continue
                elif query.startswith("/top "):
                    try:
                        current_top_k = int(query.split()[1])
                        print(f"✅ 결과 개수: {current_top_k}개")
                    except (ValueError, IndexError):
                        print("❌ 사용법: /top N (예: /top 5)")
                    continue
                elif query.startswith("/score "):
                    try:
                        current_min_score = float(query.split()[1])
                        print(f"✅ 최소 점수: {current_min_score}")
                    except (ValueError, IndexError):
                        print("❌ 사용법: /score N (예: /score 0.5)")
                    continue
                elif query.startswith("/mode"):
                    parts = query.split()
                    if len(parts) == 1:
                        # 순환: vector -> keyword -> hybrid -> vector
                        modes = ["vector", "keyword", "hybrid"]
                        idx = modes.index(current_mode)
                        current_mode = modes[(idx + 1) % 3]
                    elif parts[1] in ["vector", "keyword", "hybrid"]:
                        current_mode = parts[1]
                    else:
                        print("❌ 사용법: /mode [vector|keyword|hybrid]")
                        continue
                    print(f"✅ 검색 모드: {current_mode} {mode_icons.get(current_mode, '')}")
                    continue
                else:
                    print("❌ 알 수 없는 명령어입니다.")
                    print("   /full, /top N, /score N, /mode [vector|keyword|hybrid]")
                    continue
            
            search_and_print(query, top_k=current_top_k, min_score=current_min_score, full_text=current_full_text, mode=current_mode)
            
        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            break
        except EOFError:
            print("\n👋 종료합니다.")
            break


def main():
    parser = argparse.ArgumentParser(
        description="벡터 검색 테스트 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python test_vector_search.py "햇살 좋은 집"                    # 벡터 검색
  python test_vector_search.py "역삼동 원룸" -m keyword          # 키워드 검색
  python test_vector_search.py "조용한 동네" -m hybrid           # 하이브리드 검색
  python test_vector_search.py "햇살 좋은 집" --full             # 청크 전문 보기
  python test_vector_search.py --stats
  python test_vector_search.py -i                               # 대화형 모드
  python test_vector_search.py -i -m hybrid --full              # 하이브리드 + 전문

대화형 모드 명령어:
  /full    - 전문 보기 모드 토글
  /top N   - 결과 개수 변경
  /score N - 최소 점수 변경
  /mode    - 검색 모드 변경 (vector/keyword/hybrid)
        """
    )
    parser.add_argument("query", nargs="?", help="검색 쿼리")
    parser.add_argument("--stats", action="store_true", help="임베딩 통계 출력")
    parser.add_argument("--top-k", type=int, default=3, help="결과 개수 (기본값: 3)")
    parser.add_argument("--min-score", type=float, default=0.3, help="최소 유사도 점수 (기본값: 0.3)")
    parser.add_argument("-i", "--interactive", action="store_true", help="대화형 모드")
    parser.add_argument("--full", "-f", action="store_true", default=True, help="청크 전문 보기 (기본값: True)")
    parser.add_argument("--mode", "-m", choices=["vector", "keyword", "hybrid"], default="hybrid",
                       help="검색 모드: vector(벡터), keyword(키워드), hybrid(하이브리드) (기본값: hybrid)")
    
    args = parser.parse_args()
    
    # 통계 모드
    if args.stats:
        show_stats()
        return
    
    # 대화형 모드
    if args.interactive or not args.query:
        interactive_mode(top_k=args.top_k, min_score=args.min_score, full_text=args.full, mode=args.mode)
        return
    
    # 단일 검색
    search_and_print(args.query, top_k=args.top_k, min_score=args.min_score, full_text=args.full, mode=args.mode)


if __name__ == "__main__":
    main()
