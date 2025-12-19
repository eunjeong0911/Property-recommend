# OpenSearch Configuration

AWS OpenSearch Service 호환 설정입니다.

## 로컬 개발 환경

Docker Compose에서 OpenSearch 2.11.0을 사용합니다:

```yaml
opensearch:
  image: opensearchproject/opensearch:2.11.0
  environment:
    - discovery.type=single-node
    - plugins.security.disabled=true
```

## 인덱스 매핑

`mappings/listings.json` 파일에 매물 인덱스 매핑이 정의되어 있습니다.

### k-NN 벡터 검색

OpenSearch k-NN 플러그인을 사용하여 벡터 검색을 지원합니다:

- **벡터 타입**: `knn_vector`
- **차원**: 3072 (text-embedding-3-large)
- **알고리즘**: HNSW
- **엔진**: nmslib
- **거리 함수**: cosinesimil

### 인덱스 생성

```bash
# 인덱스 생성
curl -X PUT "http://localhost:9200/listings" \
  -H "Content-Type: application/json" \
  -d @infra/opensearch/mappings/listings.json

# 인덱스 확인
curl -X GET "http://localhost:9200/listings/_mapping?pretty"
```

## AWS OpenSearch Service

프로덕션 환경에서는 AWS OpenSearch Service를 사용합니다.

### 환경 변수

```bash
OPENSEARCH_HOST=search-xxxxx.region.es.amazonaws.com
OPENSEARCH_PORT=443
```

### 주의사항

- AWS OpenSearch Service는 HTTPS를 사용합니다
- IAM 인증 또는 Fine-grained access control 설정 필요
- k-NN 플러그인이 기본 활성화되어 있음
