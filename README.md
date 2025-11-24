# Real Estate AI Recommendation System

AI 기반 부동산 추천 시스템

## 프로젝트 구조

```
realestate-ai-reco/
├─ apps/
│  ├─ backend/          # Django API 서버
│  ├─ frontend/         # React 클라이언트
│  ├─ rag/             # LangGraph RAG 시스템
│  └─ reco/            # 추천 모델 파이프라인
├─ libs/               # 공용 라이브러리
├─ infra/              # 인프라 설정
├─ data/               # 데이터
├─ scripts/            # 운영 스크립트
└─ docs/               # 문서
```

## 시작하기

### 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# 환경 변수 설정 후 Docker Compose로 실행
make setup
make up
```

### 데이터 적재

```bash
# 매물 데이터 적재
make ingest

# 임베딩 생성
docker-compose exec rag python ../scripts/build_embeddings.py

# 그래프 DB 동기화
docker-compose exec rag python ../scripts/sync_graph.py
```

## 서비스

- Backend API: http://localhost:8000
- RAG System: http://localhost:8001
- Recommendation API: http://localhost:8002
- Frontend: http://localhost:3000
- Neo4j Browser: http://localhost:7474

## 문서

- [아키텍처](docs/architecture.md)
- [ERD](docs/erd.md)
- [그래프 스키마](docs/graph_schema.md)
- [API 명세](docs/api_spec.md)