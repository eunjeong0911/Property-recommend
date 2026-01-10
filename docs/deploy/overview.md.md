# 전체적인 요약

## 1. 전체 아키텍처 개요

### 1.1 인프라 구성도
```
                    ┌─────────────┐
                    │   Internet  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │     ALB     │ (Load Balancer)
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│  App Server    │ │ RAG Server  │ │ Neo4j Server    │
│ (10.0.139.182) │ │(10.0.140.112)│ │  (10.0.24.54)   │
└────────────────┘ └─────────────┘ └─────────────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  RDS (PostgreSQL)
                    └─────────────┘
```

### 1.2 서버별 역할 요약

| 서버 | Private IP | 주요 역할 | 서비스 |
|------|-----------|----------|--------|
| **App Server** | 10.0.139.182 | 웹 애플리케이션 | Backend, Frontend, Nginx |
| **RAG Server** | 10.0.140.112 | AI 챗봇 | RAG, Redis, Elasticsearch |
| **Neo4j Server** | 10.0.24.54 | 그래프 DB | Neo4j |

---

## 2. 서버 구성 및 역할

### 2.1 App Server (메인 애플리케이션)

**인스턴스**: t3.small (2GB RAM)

**실행 서비스**:
```
┌─────────────────────────────┐
│      App Server             │
│  ┌────────┐  ┌──────────┐   │
│  │ Nginx  │  │ Frontend │   │
│  │  :80   │  │  :3000   │   │
│  └───┬────┘  └──────────┘   │
│      │                      │
│  ┌───▼────┐  ┌──────────┐   │
│  │Backend │  │ Scripts  │   │
│  │ :8000  │  │(on-demand)│  │
│  └────────┘  └──────────┘   │
└─────────────────────────────┘
```

**주요 기능**:
- **Nginx**: Reverse Proxy, SSL 종료, 정적 파일 서빙
- **Backend (Django)**: REST API, 인증, 데이터 관리
- **Frontend (Next.js)**: 사용자 인터페이스
- **Scripts**: 데이터 크롤링, 전처리, ML 모델 실행

---

### 2.2 RAG Server (AI 챗봇)

**인스턴스**: t3.small (2GB RAM)

**실행 서비스**:
```
┌─────────────────────────────┐
│      RAG Server             │
│  ┌────────────────────┐     │
│  │   RAG Service      │     │
│  │   (FastAPI)        │     │
│  │      :8001         │     │
│  └──┬──────────────┬──┘     │
│     │              │        │
│  ┌──▼───┐    ┌────▼──────┐  │
│  │Redis │    │Elasticsearch││
│  │:6379 │    │   :9200    │ │
│  └──────┘    └────────────┘ │
└─────────────────────────────┘
```

**주요 기능**:
- **RAG Service**: LangChain 기반 AI 챗봇
- **Redis**: 대화 세션 캐시
- **Elasticsearch**: 벡터 검색 (매물 임베딩)

---

### 2.3 Neo4j Server (그래프 데이터베이스)

**인스턴스**: t3.small (2GB RAM)

**실행 서비스**:
```
┌─────────────────────────────┐
│    Neo4j Server             │
│  ┌────────────────────┐     │
│  │      Neo4j         │     │
│  │  (Graph Database)  │     │
│  │   :7474 (HTTP)     │     │
│  │   :7687 (Bolt)     │     │
│  └────────────────────┘     │
└─────────────────────────────┘
```

**주요 기능**:
- 매물-시설 관계 저장
- 그래프 기반 추천 알고리즘
- 온도 지표 계산

---

## 3. 배포 프로세스

### 3.1 CI/CD 파이프라인

```
┌──────────────┐
│ 1. Git Push  │
│   (dev)      │
└──────┬───────┘
       │
┌──────▼───────┐
│ 2. ECR Build │
│  (이미지 빌드) │
└──────┬───────┘
       │
┌──────▼───────┐
│ 3. ECR Push  │
│ (이미지 푸시) │
└──────┬───────┘
       │
┌──────▼───────┐
│ 4. EC2 Pull  │
│ (이미지 다운) │
└──────┬───────┘
       │
┌──────▼───────┐
│ 5. Deploy    │
│ (서비스 재시작)│
└──────────────┘
```
---

## 4. 데이터 파이프라인

### 4.1 데이터 흐름

```
1. 크롤링
   └─> data/RDB/land/*.json

2. 전처리
   └─> search_text, style_tags 생성

3. 데이터베이스 임포트
   ├─> PostgreSQL (매물 정보)
   ├─> Neo4j (그래프 관계)
   └─> Elasticsearch (검색 인덱스)

4. 임베딩 생성
   └─> Elasticsearch (벡터 저장)

5. ML 모델 실행
   ├─> 중개사 신뢰도 예측
   └─> 가격 적정성 판단
```

### 4.2 Scripts 실행 순서

```bash
# =================================================================
# 1단계: 기본 데이터 임포트
# =================================================================
# 1-1. PostgreSQL 매물 데이터
docker-compose --profile scripts run --rm scripts \
  python scripts/03_import/postgres/import_postgres_only.py

# 1-2. 중개사 데이터 & 관계 설정
docker-compose --profile scripts run --rm scripts \
  python scripts/03_import/reimport_brokers.py


# =================================================================
# 2단계: AI 모델 분석 & 지표 계산
# =================================================================
# 2-1. 중개사 신뢰도 등급 예측
docker-compose --profile scripts run --rm scripts \
  python scripts/04_analysis/trust_prediction/predict_trust_scores.py

# 2-2. 매물 가격 적정성 판단
docker-compose --profile scripts run --rm scripts \
  python apps/reco/models/price_model/ML/src/apply_model_to_json.py

# 2-3. Neo4j 그래프 생성 & 온도 지표(Temperature) 계산
docker-compose --profile scripts run --rm scripts \
  python scripts/03_import/neo4j/import_neo4j_only.py


# =================================================================
# 3단계: 검색엔진 최적화 (RAG)
# =================================================================
# 3-1. Elasticsearch 매물 인덱스 생성
docker-compose --profile scripts run --rm scripts \
  python scripts/03_import/elasticsearch/es817_property_importer.py

# 3-2. 임베딩(Vector) 생성 및 주입
docker-compose --profile scripts run --rm scripts \
  python scripts/03_import/elasticsearch/import_es_embeddings.py
```

---

## 6. 사용자 요청 흐름 예시

### 6.1 매물 조회
```
사용자 브라우저
    ↓ HTTPS
ALB (goziphouse.com)
    ↓
Nginx (App Server)
    ↓ /api/listings/
Backend (Django)
    ↓ SQL
PostgreSQL (RDS)
    ↓
Backend → Nginx → ALB → 사용자
```

### 6.2 AI 챗봇 질문
```
사용자 브라우저
    ↓ HTTPS
ALB (goziphouse.com)
    ↓
Nginx (App Server)
    ↓ /rag/query
RAG Service (RAG Server)
    ├─> Elasticsearch (벡터 검색)
    ├─> Neo4j (그래프 검색)
    └─> OpenAI (LLM)
    ↓
RAG → Nginx → ALB → 사용자
```