# 🗃️ Data Import Scripts

Docker 환경에서 데이터베이스에 데이터를 import하는 스크립트입니다.

## 🚀 실행 방법

```bash
# 통합 Import (Neo4j + PostgreSQL + Elasticsearch 전체)
docker compose --profile scripts run --rm scripts python 03_import/import_all.py

# 특정 DB만 Import
docker compose --profile scripts run --rm scripts python 03_import/import_all.py --only neo4j
docker compose --profile scripts run --rm scripts python 03_import/import_all.py --only postgres
docker compose --profile scripts run --rm scripts python 03_import/import_all.py --only es

# ES 임베딩 생성 (벡터 검색용)
docker compose --profile scripts run --rm scripts python 03_import/elasticsearch/import_es_embeddings.py
```

> � 자세한 파일 구조 및 환경 변수 설정은 [docs/DATA_IMPORT_SCRIPTS.md](../../docs/DATA_IMPORT_SCRIPTS.md) 참고
