# 🗃️ Data Import Scripts

Docker 환경에서 데이터베이스(PostgreSQL, Neo4j)와 Elasticsearch에 데이터를 import하는 스크립트 모음입니다.

## 🚀 실행 방법

```bash
# 전체 데이터 Import (PostgreSQL + Neo4j + Linking)
docker compose --profile scripts run --rm scripts python data_import/main.py

# ES 인덱싱 (매물 데이터)
docker compose --profile scripts run --rm scripts python data_import/import_es_index.py --recreate

# ES 임베딩 생성 (벡터 검색용)
docker compose --profile scripts run --rm scripts python data_import/import_es_embeddings.py
```

---

## 📁 파일 구조

| 파일 | 용도 |
|------|------|
| `main.py` | **전체 import 파이프라인** - PostgreSQL, Neo4j, Linking 순차 실행 |
| `import_es_index.py` | **ES 인덱싱** - JSON 매물 데이터를 ES에 벌크 색인 |
| `import_es_embeddings.py` | **ES 임베딩 생성** - search_text 기반 벡터 임베딩 추가 |
| `import_neo4j_only.py` | Neo4j만 import (부분 실행용) |
| `import_postgres_only.py` | PostgreSQL만 import (부분 실행용) |
| `config.py` | 환경 변수 및 데이터 경로 설정 |
| `database.py` | DB 연결 유틸리티 |
| `db_health_check.py` | DB 연결 상태 확인 |
| `reimport_brokers.py` | 중개사 데이터 재import |
| `update_broker_stats.py` | 중개사 통계 업데이트 |

### importers/ 폴더

| 파일 | 용도 |
|------|------|
| `property_importer.py` | 매물(Property) 노드 import |
| `transport_importer.py` | 지하철/버스 노드 import + Linking |
| `safety_importer.py` | CCTV/경찰서 노드 import + Linking |
| `amenity_importer.py` | 병원/약국/편의점 노드 import + Linking |
| `postgres_importer.py` | PostgreSQL 매물 데이터 import |

---

## ⚙️ 환경 변수

`.env` 파일에서 설정:

```env
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=realestate
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpassword

# Elasticsearch
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200
ES_INDEX_NAME=realestate_listings

# OpenAI (임베딩용)
OPENAI_API_KEY=sk-xxx
```

---

## 📊 실행 순서

일반적인 초기 세팅 순서:

1. **DB 초기화**: `main.py` (PostgreSQL + Neo4j)
2. **ES 인덱싱**: `import_es_index.py --recreate`
3. **임베딩 생성**: `import_es_embeddings.py`

---

## 🔄 재실행 옵션

```bash
# ES 인덱스 재생성 (기존 데이터 삭제)
python data_import/import_es_index.py --recreate

# 기존 데이터 있어도 강제 실행
python data_import/import_es_index.py --force
```
