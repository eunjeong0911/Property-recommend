# Scripts 디렉토리

데이터 파이프라인 스크립트 모음

## 폴더 구조

```
scripts/
├── 01_crawling/        # 데이터 수집
│   └── peterpan/       # 피터팬 매물 크롤러
│
├── 02_preprocessing/   # 데이터 전처리
│   └── generate_search_text_parallel.py  # ES search_text 생성
│
├── 03_import/          # DB 임포트
│   ├── neo4j/          # Neo4j 그래프 데이터
│   │   ├── facility/   # 시설 관계 임포트
│   │   ├── property/   # 매물 노드 임포트
│   │   └── temperature/ # 온도 점수 임포트
│   ├── postgres/       # PostgreSQL 임포트
│   └── elasticsearch/  # ES 인덱스 및 임베딩
│
└── 04_analysis/        # 분석 및 예측
    └── trust_prediction/ # 신뢰도 점수 예측
```

## 실행 순서

```bash
# 1. 크롤링 (선택)
python 01_crawling/peterpan/crawl_seoul.py

# 2. 전처리
python 02_preprocessing/generate_search_text_parallel.py

# 3. DB 임포트
python 03_import/neo4j/import_neo4j_only.py
python 03_import/postgres/import_postgres_only.py
python 03_import/elasticsearch/import_es_index.py
python 03_import/elasticsearch/import_es_embeddings.py

# 4. 분석 (선택)
python 04_analysis/trust_prediction/predict_trust_scores.py
```

## 환경 설정

`.env` 파일에 필수 변수 설정 필요:

- NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
- POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- ELASTICSEARCH_HOST (Docker: elasticsearch:9200)
