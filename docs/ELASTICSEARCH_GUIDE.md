# Elasticsearch 및 Kibana 실행 가이드

## 개요

이 가이드는 부동산 매물 검색 서비스의 Elasticsearch와 Kibana를 설정하고 사용하는 방법을 설명합니다.

## 서비스 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Elasticsearch | 9200 | 검색 엔진 |
| Kibana | 5601 | ES 데이터 시각화 대시보드 |

## 1. 서비스 시작

### 1.1 Docker Compose로 시작

```bash
# 전체 서비스 시작 (ES, Kibana 포함)
docker-compose up -d

# ES와 Kibana만 시작
docker-compose up -d elasticsearch kibana
```

### 1.2 서비스 상태 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# ES 헬스체크
curl http://localhost:9200/_cluster/health

# Kibana 상태 확인
curl http://localhost:5601/api/status
```

### 1.3 예상 출력

```json
// ES 헬스체크 응답
{
  "cluster_name": "docker-cluster",
  "status": "green",
  "number_of_nodes": 1,
  "number_of_data_nodes": 1
}
```

## 2. 매물 데이터 인덱싱

### 2.1 Bulk 인덱싱 스크립트 실행

```bash
# Docker 환경에서 실행
docker-compose --profile scripts run --rm scripts python es_bulk_index.py

# 로컬 환경에서 실행 (가상환경 활성화 필요)
cd scripts
python es_bulk_index.py --es-host localhost
```

### 2.2 인덱싱 옵션

```bash
# 인덱스 재생성 후 인덱싱
python es_bulk_index.py --recreate

# 문서 수만 확인 (실제 인덱싱 안함)
python es_bulk_index.py --dry-run

# 배치 크기 조정
python es_bulk_index.py --batch-size 500

# 데이터 디렉토리 지정
python es_bulk_index.py --data-dir /path/to/data
```

### 2.3 인덱싱 결과 예시

```
============================================================
Elasticsearch Bulk Indexing Script
============================================================

Connecting to Elasticsearch...
  Connected to ES version 8.11.0

Loading data from data/RDB/land...
  Loading 00_통합_원투룸.json...
  Loading 00_통합_빌라주택.json...
  Loading 00_통합_아파트.json...
  Loading 00_통합_오피스텔.json...
  Batch 1: 1000 succeeded, 0 failed
  Batch 2: 1000 succeeded, 0 failed
  ...

============================================================
Indexing Complete
============================================================
  Total Success: 15234
  Total Failed:  0
  Elapsed Time:  45.32 seconds
  Index Count:   15234
============================================================
```

## 3. Kibana 사용

### 3.1 Kibana 접속

브라우저에서 http://localhost:5601 접속

### 3.2 인덱스 패턴 생성

1. 좌측 메뉴 → Stack Management → Index Patterns
2. "Create index pattern" 클릭
3. Index pattern: `realestate_listings` 입력
4. "Create index pattern" 클릭

### 3.3 Dev Tools에서 쿼리 실행

좌측 메뉴 → Dev Tools 접속 후 다음 쿼리 실행:

```json
// 인덱스 문서 수 확인
GET realestate_listings/_count

// 샘플 문서 조회
GET realestate_listings/_search
{
  "size": 5
}

// 키워드 검색 (한국어)
GET realestate_listings/_search
{
  "query": {
    "match": {
      "search_text": {
        "query": "강남역 원룸",
        "analyzer": "nori_analyzer"
      }
    }
  }
}

// 가격 범위 필터
GET realestate_listings/_search
{
  "query": {
    "bool": {
      "filter": [
        { "range": { "deposit": { "gte": 1000, "lte": 5000 } } },
        { "term": { "deal_type": "월세" } }
      ]
    }
  }
}

// 스타일 태그 검색
GET realestate_listings/_search
{
  "query": {
    "terms": {
      "style_tags": ["풀옵션", "역세권"]
    }
  }
}

// 위치 기반 검색 (강남역 주변 1km)
GET realestate_listings/_search
{
  "query": {
    "geo_distance": {
      "distance": "1km",
      "location": {
        "lat": 37.4979,
        "lon": 127.0276
      }
    }
  }
}
```

## 4. 인덱스 매핑 정보

### 4.1 필드 구조

| 필드 | 타입 | 설명 |
|------|------|------|
| land_num | keyword | 매물 번호 (고유 ID) |
| address | text (nori) | 전체 주소 |
| search_text | text (nori) | 검색용 전처리 텍스트 |
| style_tags | keyword[] | 스타일 태그 배열 |
| building_type | keyword | 건물 형태 |
| deal_type | keyword | 거래 유형 (월세/전세/매매) |
| deposit | integer | 보증금 (만원) |
| monthly_rent | integer | 월세 (만원) |
| jeonse_price | integer | 전세가 (만원) |
| sale_price | integer | 매매가 (만원) |
| location | geo_point | 좌표 (lat, lon) |
| url | keyword | 매물 URL |

### 4.2 매핑 파일 위치

```
infra/elasticsearch/mappings/listings.json
```

## 5. 검색 테스트

### 5.1 터미널 테스트 스크립트

```bash
# 검색 파이프라인 테스트
cd scripts
python test_search_pipeline.py
```

### 5.2 Python에서 직접 검색

```python
from apps.backend.apps.search.services import search_listings_with_es

# 키워드 검색
results = search_listings_with_es(keyword="강남역 원룸")
print(f"검색 결과: {len(results['ids'])}건")

# 복합 조건 검색
results = search_listings_with_es(
    keyword="역세권",
    min_deposit=1000,
    max_deposit=5000,
    style_tags=["풀옵션"]
)
```

## 6. 문제 해결

### 6.1 ES 연결 실패

```bash
# ES 컨테이너 상태 확인
docker-compose ps elasticsearch

# ES 로그 확인
docker-compose logs elasticsearch

# ES 재시작
docker-compose restart elasticsearch
```

### 6.2 인덱스 생성 실패

```bash
# 인덱스 삭제 후 재생성
curl -X DELETE http://localhost:9200/realestate_listings
python es_bulk_index.py --recreate
```

### 6.3 Kibana 연결 실패

```bash
# Kibana 로그 확인
docker-compose logs kibana

# ES가 먼저 실행되어야 함
docker-compose restart kibana
```

### 6.4 한국어 검색 안됨

nori 분석기가 제대로 설정되었는지 확인:

```json
// Dev Tools에서 실행
GET realestate_listings/_analyze
{
  "analyzer": "nori_analyzer",
  "text": "강남역 원룸"
}
```

### 6.5 메모리 부족

docker-compose.yml에서 ES 메모리 설정 조정:

```yaml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # 기본 512m에서 증가
```

## 7. 유용한 명령어

```bash
# 인덱스 목록 확인
curl http://localhost:9200/_cat/indices?v

# 인덱스 매핑 확인
curl http://localhost:9200/realestate_listings/_mapping

# 인덱스 설정 확인
curl http://localhost:9200/realestate_listings/_settings

# 인덱스 삭제
curl -X DELETE http://localhost:9200/realestate_listings

# 클러스터 상태 확인
curl http://localhost:9200/_cluster/health?pretty

# 노드 정보 확인
curl http://localhost:9200/_nodes?pretty
```

## 8. 접속 정보 요약

| 서비스 | URL | 용도 |
|--------|-----|------|
| Elasticsearch | http://localhost:9200 | REST API |
| Kibana | http://localhost:5601 | 웹 대시보드 |
| Dev Tools | http://localhost:5601/app/dev_tools | 쿼리 테스트 |

## 9. 관련 파일

| 파일 | 설명 |
|------|------|
| `docker-compose.yml` | ES/Kibana 서비스 정의 |
| `infra/elasticsearch/elasticsearch.yml` | ES 설정 파일 |
| `infra/elasticsearch/mappings/listings.json` | 인덱스 매핑 |
| `scripts/es_bulk_index.py` | Bulk 인덱싱 스크립트 |
| `apps/backend/apps/search/es_client.py` | ES 클라이언트 |
| `apps/backend/apps/search/services.py` | 검색 서비스 |
