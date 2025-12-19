#!/usr/bin/env python
"""
ES 문서에 임베딩 추가 스크립트

Requirements:
- 2.1: ES의 기존 listings 인덱스에서 매물 조회
- 2.2: search_text와 style_tags를 결합하여 임베딩 텍스트 생성
- 2.4: ES bulk API를 사용하여 배치 단위(100개)로 업데이트
"""
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Generator

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# .env 파일 로드
from dotenv import load_dotenv
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ .env 파일 로드됨: {env_path}")

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from libs.clients.embedding_service import EmbeddingService

BATCH_SIZE = 100
INDEX_NAME = os.getenv("ES_INDEX_NAME", "realestate_listings")


def get_es_client() -> Elasticsearch:
    """OpenSearch 클라이언트 반환 (AWS OpenSearch Service 호환)"""
    # OpenSearch 환경변수 우선, ES 환경변수 fallback
    os_host = os.getenv("OPENSEARCH_HOST") or os.getenv("ELASTICSEARCH_HOST", "localhost")
    os_port = os.getenv("OPENSEARCH_PORT") or os.getenv("ELASTICSEARCH_PORT", "9200")
    os_url = f"http://{os_host}:{os_port}"
    
    return Elasticsearch(
        hosts=[os_url],
        request_timeout=30,
        max_retries=3,
        retry_on_timeout=True
    )


def get_documents_without_embedding(es: Elasticsearch, batch_size: int) -> List[Dict]:
    """임베딩이 없는 문서 조회 (Requirements 2.6: 중복 방지)"""
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
    """임베딩용 텍스트 생성 (Requirements 2.2)
    
    search_text와 style_tags를 공백으로 결합하여 임베딩 텍스트 생성
    """
    source = doc.get("_source", {})
    parts = []
    
    # search_text 추가
    if source.get("search_text"):
        parts.append(str(source["search_text"]))
    
    # style_tags 추가
    if source.get("style_tags"):
        tags = source["style_tags"]
        if isinstance(tags, list):
            parts.append(" ".join(str(tag) for tag in tags))
        else:
            parts.append(str(tags))
    
    return " ".join(parts)


def generate_bulk_actions(
    docs: List[Dict], 
    embeddings: List[List[float]]
) -> Generator[Dict, None, None]:
    """bulk 업데이트 액션 생성 (Requirements 1.4: 부분 업데이트)"""
    for doc, embedding in zip(docs, embeddings):
        yield {
            "_op_type": "update",
            "_index": INDEX_NAME,
            "_id": doc["_id"],
            "doc": {"embedding": embedding}
        }


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("ES 임베딩 생성 스크립트")
    print("=" * 60)
    
    start_time = time.time()
    
    # 클라이언트 초기화
    es = get_es_client()
    embedding_service = EmbeddingService.get_instance()
    
    # 연결 확인
    try:
        info = es.info()
        print(f"✅ OpenSearch 연결 성공 (버전: {info['version']['number']})")
        print(f"📌 인덱스: {INDEX_NAME}")
    except Exception as e:
        print(f"❌ OpenSearch 연결 실패: {e}")
        sys.exit(1)
    
    total_success = 0
    total_failed = 0
    
    while True:
        # 임베딩 없는 문서 조회
        docs = get_documents_without_embedding(es, BATCH_SIZE)
        if not docs:
            break
        
        # 텍스트 추출 (빈 텍스트 방지)
        texts = []
        for doc in docs:
            text = create_embedding_text(doc)
            texts.append(text if text.strip() else "부동산 매물")
        
        try:
            # 임베딩 생성
            embeddings = embedding_service.embed_batch(texts)
            
            # bulk 업데이트
            actions = list(generate_bulk_actions(docs, embeddings))
            success, failed = bulk(es, actions, raise_on_error=False)
            
            total_success += success
            if failed:
                total_failed += len(failed)
            
            print(f"진행: {total_success}건 완료, {total_failed}건 실패")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            total_failed += len(docs)
            # 잠시 대기 후 계속 (rate limit 대응)
            time.sleep(1)
    
    elapsed_time = time.time() - start_time
    
    print("=" * 60)
    print(f"완료: 총 {total_success}건 임베딩 생성")
    print(f"실패: {total_failed}건")
    print(f"소요 시간: {elapsed_time:.2f}초")
    print("=" * 60)


if __name__ == "__main__":
    main()
