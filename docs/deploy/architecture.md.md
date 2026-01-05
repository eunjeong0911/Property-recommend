# 상세 아키텍처 및 배포 가이드
## 1. 전체 아키텍처 개요

### 1.1 네트워크 구성
```
Internet
    ↓
[ALB] (Public Subnet)
    ↓
[Bastion Host] (Public Subnet) ← SSH 접속용
    ↓
Private Subnet:
├── App Server (10.0.139.182)
│   ├── Backend (Django)
│   ├── Frontend (Next.js)
│   ├── Nginx (Reverse Proxy)
│   └── Scripts (데이터 처리)
├── RAG Server (10.0.14.99)
│   ├── RAG Service (FastAPI)
│   ├── Redis (캐시)
│   └── Elasticsearch (검색)
└── Neo4j Server (10.0.24.54)
    └── Neo4j (그래프 DB)
```

### 1.2 외부 서비스
- **AWS RDS PostgreSQL**: 메인 데이터베이스
- **AWS ECR**: Docker 이미지 저장소

---

## 2. 서버 구성

### 2.1 App Server (t3.small, 2GB RAM)
**역할**: 메인 애플리케이션 서버

**실행 서비스**:
- `realestate-backend`: Django REST API
- `realestate-frontend`: Next.js 웹 애플리케이션
- `realestate-nginx`: Reverse Proxy & SSL Termination
- `realestate-scripts`: 데이터 처리

**Docker Compose 파일**: `docker-compose.prod.app.yml`

**포트**:
- 80 (HTTP) → Nginx
- 443 (HTTPS) → Nginx

### 2.2 RAG Server (t3.small, 2GB RAM)
**역할**: AI 챗봇 서비스

**실행 서비스**:
- `realestate-rag`: FastAPI RAG 서비스
- `redis`: 캐시 서버
- `elasticsearch`: 검색 엔진

**Docker Compose 파일**: `docker-compose.prod.rag.yml`

**포트**:
- 8001 (RAG API)
- 6379 (Redis)
- 9200 (Elasticsearch)

### 2.3 Neo4j Server (t3.small, 2GB RAM)
**역할**: 그래프 데이터베이스

**실행 서비스**:
- `neo4j`: 그래프 DB

**Docker Compose 파일**: `docker-compose.prod.neo4j.yml`

**포트**:
- 7474 (HTTP)
- 7687 (Bolt)

---

## 3. Docker 이미지 구성

### 3.1 ECR 저장소
**AWS ECR Repository**: `046685909225.dkr.ecr.ap-northeast-2.amazonaws.com`

**이미지 목록**:
```
realestate-backend:latest
realestate-frontend:latest
realestate-rag:latest
realestate-scripts:latest
```

### 3.2 이미지별 상세 정보

#### 3.2.1 Backend (Django)
**Dockerfile**: `infra/docker/backend.Dockerfile`

**베이스 이미지**: `python:3.11-slim`

**포함 내용**:
- Django 애플리케이션 코드
- Python 패키지 (requirements.txt)
- Gunicorn WSGI 서버

**볼륨 마운트**:
- `./data:/app/data` (데이터 파일)
- `./apps/backend/config/settings/prod.py:/app/config/settings/prod.py` (설정 파일)

---

#### 3.2.2 Frontend (Next.js)
**Dockerfile**: `infra/docker/frontend.Dockerfile`

**베이스 이미지**: `node:20-alpine`

**빌드 인자 (Build Args)**:
```bash
NEXT_PUBLIC_API_URL=https://goziphouse.com
NEXT_PUBLIC_KAKAO_MAP_KEY=<카카오맵_키>
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<구글_클라이언트_ID>
```

**런타임 환경변수** (docker-compose에서 주입):
```yaml
environment:
  - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
  - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
  - NEXTAUTH_URL=https://goziphouse.com
  - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
```

**볼륨 마운트**: 없음 (모든 코드가 이미지에 포함)

---

#### 3.2.3 RAG (FastAPI)
**Dockerfile**: `infra/docker/rag.Dockerfile`

**베이스 이미지**: `python:3.11-slim`

**포함 내용**:
- FastAPI 애플리케이션 코드
- Python 패키지
- Uvicorn ASGI 서버

**볼륨 마운트**: 없음

---

#### 3.2.4 Scripts (데이터 처리)
**Dockerfile**: `infra/docker/scripts.Dockerfile`

**베이스 이미지**: `python:3.11-slim`

**포함 내용**:
- 크롤링 스크립트
- 데이터 임포트 스크립트
- ML 모델 파일 (`apps/reco/models/**/*.pkl`)
- Python 패키지

**볼륨 마운트**:
- `./data:/app/data` (크롤링 데이터 저장)

**특이사항**:
- `.dockerignore`에서 `apps/reco/models/**/*.pkl` 예외 처리
- ML 모델 파일이 이미지에 포함됨

---

## 4. 빌드 및 배포 프로세스

### 4.1 로컬 빌드 → ECR Push → EC2 배포

#### Step 1: ECR 로그인
```bash
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  046685909225.dkr.ecr.ap-northeast-2.amazonaws.com
```

#### Step 2: 이미지 빌드
```bash
# Backend
docker build -f infra/docker/backend.Dockerfile -t realestate-backend:latest .

# Frontend (빌드 인자 필수!)
docker build -f infra/docker/frontend.Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=https://goziphouse.com \
  --build-arg NEXT_PUBLIC_KAKAO_MAP_KEY=29d460d952fdd2737e2be0432924660c \
  --build-arg NEXT_PUBLIC_GOOGLE_CLIENT_ID=427910451644-tbsnm5701k94burftvo12kv8p8ngpcvo.apps.googleusercontent.com \
  -t realestate-frontend:latest .

# RAG
docker build -f infra/docker/rag.Dockerfile -t realestate-rag:latest .

# Scripts
docker build -f infra/docker/scripts.Dockerfile -t realestate-scripts:latest .
```

#### Step 3: 이미지 태그
```bash
docker tag realestate-backend:latest 046685909225.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-backend:latest
docker tag realestate-frontend:latest 046685909225.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-frontend:latest
docker tag realestate-rag:latest 046685909225.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-rag:latest
docker tag realestate-scripts:latest 046685909225.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-scripts:latest
```

#### Step 4: ECR Push
```bash
docker push 046685909225.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-backend:latest
docker push 046685909225.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-frontend:latest
docker push 046685909225.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-rag:latest
docker push 046685909225.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-scripts:latest
```

#### Step 5: EC2 배포
```bash
# EC2 접속 (Bastion 경유)
ssh -i "realestate-key.pem" ec2-user@<서버_IP>

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  046685909225.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 Pull
docker-compose --env-file .env.production -f docker-compose.prod.app.yml pull

# 서비스 재시작
docker-compose --env-file .env.production -f docker-compose.prod.app.yml up -d --force-recreate
```

---

## 5. 볼륨 마운트 전략

### 5.1 데이터 볼륨 (App Server)
```yaml
volumes:
  - ./data:/app/data  # 크롤링 데이터, CSV 파일
```

**포함 내용**:
- `data/01_raw/`: 크롤링 원본 데이터
- `data/02_processed/`: 전처리된 데이터
- `data/03_final/`: 최종 데이터

**사용 서비스**: Backend, Scripts

---

### 5.2 설정 파일 볼륨 (App Server)
```yaml
volumes:
  - ./apps/backend/config/settings/prod.py:/app/config/settings/prod.py
```

**이유**: 설정 변경 시 이미지 재빌드 없이 수정 가능

**사용 서비스**: Backend

---

### 5.3 Nginx 설정 볼륨 (App Server)
```yaml
volumes:
  - ./infra/nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
  - ./infra/nginx/ssl:/etc/nginx/ssl:ro
```

**포함 내용**:
- `nginx.prod.conf`: Nginx 설정
- `ssl/`: SSL 인증서

**사용 서비스**: Nginx

---

### 5.4 Neo4j 데이터 볼륨 (Neo4j Server)
```yaml
volumes:
  - neo4j_data:/data
  - neo4j_logs:/logs
```

**이유**: 데이터 영속성 보장

**사용 서비스**: Neo4j

---

### 5.5 Elasticsearch 데이터 볼륨 (RAG Server)
```yaml
volumes:
  - elasticsearch_data:/usr/share/elasticsearch/data
```

**이유**: 인덱스 데이터 영속성 보장

**사용 서비스**: Elasticsearch

---

# 6. 환경변수 주입 방식

**빌드타임 (Frontend)**:
- `NEXT_PUBLIC_*` 변수는 빌드 시 `--build-arg`로 주입
- 이미지에 하드코딩됨

**런타임 (Backend, RAG, Scripts)**:
- `.env.production` 파일에서 읽음
- `docker-compose`의 `env_file` 또는 `environment`로 주입
