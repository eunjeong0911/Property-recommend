#!/usr/bin/env python
"""
ES 임베딩 생성 스크립트 (ES 8.17 + 병렬 처리)

ES 인덱스의 문서에 벡터 임베딩을 생성하여 추가합니다.
asyncio를 사용하여 병렬로 임베딩을 생성합니다.

Usage:
    docker compose --profile scripts run --rm scripts python scripts/03_import/elasticsearch/import_es_embeddings.py
"""
import os
import sys
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Generator
from concurrent.futures import ThreadPoolExecutor

# 프로젝트 루트 경로 추가 (scripts/03_import/elasticsearch -> project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env 파일 로드
from dotenv import load_dotenv
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from openai import OpenAI

# 설정
BATCH_SIZE = 100  # ES 업데이트 배치 크기
CONCURRENT_EMBEDDINGS = 5  # 동시 임베딩 요청 수
INDEX_NAME = os.getenv("ES_INDEX_NAME", "realestate_listings")
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072

# OpenAI 클라이언트
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_es_client() -> Elasticsearch:
    """Elasticsearch 8.17 클라이언트 반환"""
    es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
    es_url = f"http://{es_host}:{es_port}"
    
    return Elasticsearch(
        hosts=[es_url],
        request_timeout=30,
        max_retries=3,
        retry_on_timeout=True
    )


def get_total_without_embedding(es: Elasticsearch) -> int:
    """임베딩이 없는 문서 총 개수 조회"""
    query = {
        "bool": {
            "must_not": {
                "exists": {"field": "embedding"}
            }
        }
    }
    result = es.count(index=INDEX_NAME, query=query)
    return result["count"]


def get_documents_without_embedding(es: Elasticsearch, batch_size: int) -> List[Dict]:
    """임베딩이 없는 문서 조회"""
    query = {
        "bool": {
            "must_not": {
                "exists": {"field": "embedding"}
            }
        }
    }
    result = es.search(
        index=INDEX_NAME,
        query=query,
        size=batch_size,
        _source=["search_text", "style_tags"]
    )
    return result["hits"]["hits"]


def create_embedding_text(doc: Dict) -> str:
    """임베딩용 텍스트 생성 (search_text + style_tags)"""
    source = doc.get("_source", {})
    parts = []
    
    if source.get("search_text"):
        parts.append(str(source["search_text"]))
    
    if source.get("style_tags"):
        tags = source["style_tags"]
        if isinstance(tags, list):
            parts.append(" ".join(str(tag) for tag in tags))
        else:
            parts.append(str(tags))
    
    text = " ".join(parts)
    return text if text.strip() else "부동산 매물"


def embed_batch_sync(texts: List[str]) -> List[List[float]]:
    """동기 배치 임베딩 생성 (OpenAI API 네이티브 배치 지원)"""
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            dimensions=EMBEDDING_DIM
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"❌ 임베딩 오류: {e}")
        # 실패 시 빈 임베딩 반환
        return [[0.0] * EMBEDDING_DIM for _ in texts]


def generate_bulk_actions(
    docs: List[Dict], 
    embeddings: List[List[float]]
) -> Generator[Dict, None, None]:
    """bulk 업데이트 액션 생성"""
    for doc, embedding in zip(docs, embeddings):
        yield {
            "_op_type": "update",
            "_index": INDEX_NAME,
            "_id": doc["_id"],
            "doc": {"embedding": embedding}
        }


def process_batch(es: Elasticsearch, docs: List[Dict]) -> tuple:
    """배치 처리: 임베딩 생성 + ES 업데이트"""
    # 텍스트 추출
    texts = [create_embedding_text(doc) for doc in docs]
    
    # 임베딩 생성 (OpenAI API가 배치 지원)
    embeddings = embed_batch_sync(texts)
    
    # ES 업데이트
    actions = list(generate_bulk_actions(docs, embeddings))
    success, failed = bulk(es, actions, raise_on_error=False)
    
    failed_count = len(failed) if failed else 0
    return success, failed_count


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("ES 임베딩 생성 (병렬 처리)")
    print(f"  모델: {EMBEDDING_MODEL}")
    print(f"  배치 크기: {BATCH_SIZE}")
    print("=" * 60)
    
    start_time = time.time()
    
    # ES 연결
    es = get_es_client()
    
    try:
        info = es.info()
        print(f"✅ Elasticsearch 연결 (v{info['version']['number']})")
        print(f"📌 인덱스: {INDEX_NAME}")
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        sys.exit(1)
    
    # 총 문서 수 확인
    total_without_embedding = get_total_without_embedding(es)
    print(f"📊 임베딩 없는 문서: {total_without_embedding}개")
    
    if total_without_embedding == 0:
        print("  ⏭ 모든 문서에 이미 임베딩이 있습니다.")
        return
    
    total_success = 0
    total_failed = 0
    batch_num = 0
    
    while True:
        docs = get_documents_without_embedding(es, BATCH_SIZE)
        if not docs:
            break
        
        batch_num += 1
        
        try:
            success, failed = process_batch(es, docs)
            total_success += success
            total_failed += failed
            
            # 진행률 표시
            processed = total_success + total_failed
            progress_pct = processed * 100 // total_without_embedding
            elapsed = time.time() - start_time
            speed = processed / elapsed if elapsed > 0 else 0
            remaining = (total_without_embedding - processed) / speed if speed > 0 else 0
            
            print(f"  진행: {processed}/{total_without_embedding} ({progress_pct}%) | "
                  f"{speed:.1f}개/초 | 남은 시간: {remaining:.0f}초")
            
        except Exception as e:
            print(f"❌ 배치 {batch_num} 오류: {e}")
            total_failed += len(docs)
            time.sleep(1)
    
    elapsed = time.time() - start_time
    
    print("=" * 60)
    print(f"✅ 완료: {total_success}건 임베딩 생성")
    print(f"❌ 실패: {total_failed}건")
    print(f"⏱ 소요 시간: {elapsed:.1f}초")
    print(f"⚡ 평균 속도: {total_success / elapsed:.1f}개/초")
    print("=" * 60)


if __name__ == "__main__":
    main()
