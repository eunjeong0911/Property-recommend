# 개발자용 로컬 실행 가이드

Docker 없이 로컬에서 빠르게 개발하기 위한 가이드입니다.

## 사전 준비

### 필수 설치 항목
- **uv** (Python 패키지 관리자) - https://docs.astral.sh/uv/
- Node.js 18+ (프론트엔드용)
- PostgreSQL 16 (pgvector 확장 포함)
- Neo4j 5.15
- Redis 7

### 환경 변수 설정
`.env` 파일을 프로젝트 루트에 생성하고 다음 내용을 설정:

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=realestate
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Neo4j (주의: 비밀번호는 'neo4j'를 사용할 수 없습니다)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Django
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Redis
REDIS_URL=redis://localhost:6379/0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Google Login
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# NextAuth
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=http://localhost:3000

# 카카오 지도 API
NEXT_PUBLIC_KAKAO_MAP_KEY=your_kakao_map_key
KAKAO_API_KEY=your_kakao_rest_api_key
```

---

## 1. 데이터베이스 실행 및 초기화

### 1-1. 데이터베이스 실행 (Docker 사용 권장)

데이터베이스만 Docker로 실행하는 것이 가장 편합니다:

```bash
docker-compose up -d postgres neo4j redis
```

또는 로컬에 직접 설치한 경우 각각 실행하세요.

### 1-2. PostgreSQL 초기화 확인

PostgreSQL은 Docker 실행 시 자동으로 `infra/postgres/init.sql`이 실행되어 테이블과 pgvector 확장이 설정됩니다.

수동으로 확인하려면:
```bash
docker exec -it <postgres_container_id> psql -U postgres -d realestate
```

### 1-3. Neo4j 초기 설정

Neo4j 브라우저에 접속하여 초기 스키마를 생성합니다:

1. 브라우저에서 `http://localhost:7474` 접속
2. 로그인 (Username: `neo4j`, Password: `.env` 파일에 설정한 비밀번호)
3. 다음 Cypher 쿼리 실행:

```cypher
// 제약조건 생성
CREATE CONSTRAINT listing_id IF NOT EXISTS FOR (l:Listing) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT facility_id IF NOT EXISTS FOR (f:Facility) REQUIRE f.id IS UNIQUE;

// 인덱스 생성
CREATE INDEX listing_price IF NOT EXISTS FOR (l:Listing) ON (l.price);
CREATE INDEX listing_area IF NOT EXISTS FOR (l:Listing) ON (l.area);
```

또는 스크립트로 자동 실행:
```powershell
# PowerShell
Get-Content infra/neo4j/init.cypher | docker exec -i skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p password123

# 또는 컨테이너 이름 확인 후 실행
docker ps | findstr neo4j
Get-Content infra/neo4j/init.cypher | docker exec -i <컨테이너_이름> cypher-shell -u neo4j -p <비밀번호>
```

**스키마 생성 확인:**
```powershell
# 제약조건 확인
docker exec -i skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p password123 "SHOW CONSTRAINTS;"

# 인덱스 확인
docker exec -i skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p password123 "SHOW INDEXES;"
```

---

## 2. 백엔드 (Django) 실행

### 2-1. 가상환경 생성 및 의존성 설치 (uv 사용)

```bash
cd apps\backend
uv venv
uv pip install -r requirements.txt
```

`uv venv`는 `.venv` 폴더에 가상환경을 생성하고, `uv pip`로 빠르게 패키지를 설치합니다.

### 2-2. 데이터베이스 마이그레이션

```bash
uv run python manage.py migrate
```

### 2-3. 슈퍼유저 생성 (선택사항)

```bash
uv run python manage.py createsuperuser
```

### 2-4. 개발 서버 실행

```bash
uv run python manage.py runserver
```

백엔드가 `http://localhost:8000`에서 실행됩니다.

---

## 3. 프론트엔드 (Next.js) 실행

### 3-1. 의존성 설치

```bash
cd apps\frontend
npm install
```

### 3-2. 개발 서버 실행

```bash
npm run dev
```

프론트엔드가 `http://localhost:3000`에서 실행됩니다.

---

## 4. RAG 서비스 실행 (선택사항)

```bash
cd apps\rag
uv venv
uv pip install -r ../backend/requirements.txt
uv run python main.py
```

RAG 서비스가 `http://localhost:8001`에서 실행됩니다.

---

## 5. 추천 서비스 실행 (선택사항)

```bash
cd apps\reco
uv venv
uv pip install -r ../backend/requirements.txt
uv run python serve.py
```

추천 서비스가 `http://localhost:8002`에서 실행됩니다.

---

## 빠른 시작 명령어 모음

### 최초 1회 설정

```bash
# 1. 데이터베이스 실행
docker-compose up -d postgres neo4j redis

# 2. Neo4j 초기화 (브라우저에서 http://localhost:7474 접속 후 스키마 생성)

# 3. 백엔드 환경 설정
cd apps\backend
uv venv
uv pip install -r requirements.txt
uv run python manage.py migrate

# 4. 데이터 임포트 (백엔드 가상환경 사용)
cd ..\..\scripts
..\apps\backend\.venv\Scripts\python.exe data_import\main.py

# 5. 임베딩 생성 (선택사항)
..\apps\backend\.venv\Scripts\python.exe build_embeddings.py

# 5. 프론트엔드 환경 설정
cd ..\apps\frontend
npm install
```

### 일상적인 개발 시작

#### 터미널 1 - 데이터베이스
```bash
docker-compose up -d postgres neo4j redis
```

#### 터미널 2 - 백엔드
```bash
cd apps\backend
uv run python manage.py runserver
```

#### 터미널 3 - 프론트엔드
```bash
cd apps\frontend
npm run dev
```

---

## 유용한 Django 명령어

```bash
# 마이그레이션 파일 생성
uv run python manage.py makemigrations

# 마이그레이션 적용
uv run python manage.py migrate

# Django shell 실행
uv run python manage.py shell

# 정적 파일 수집
uv run python manage.py collectstatic

# 테스트 실행
uv run python manage.py test
```

---

## 데이터 초기화 및 임포트

### 통합 데이터 임포트 (권장)

모든 데이터를 한 번에 임포트하고 Neo4j 그래프 노드/엣지를 생성:

```powershell
# 백엔드 가상환경을 사용 (이미 requirements.txt 설치됨)
cd scripts
..\apps\backend\.venv\Scripts\python.exe data_import\main.py
```

이 스크립트는 다음을 자동으로 처리합니다:

**1. 교통 데이터 (Neo4j 노드 생성)**
- 지하철역 (Subway 노드)
- 버스정류장 (BusStop 노드)

**2. 편의시설 데이터 (Neo4j 노드 생성)**
- 의료시설 (Hospital, Pharmacy 노드)
- 대학교 (College 노드)
- 편의점 (ConvenienceStore 노드)
- 공원 (Park 노드)

**3. 안전시설 데이터 (Neo4j 노드 생성)**
- CCTV (CCTV 노드)
- 안심벨 (SafetyBell 노드)
- 경찰서 (PoliceStation 노드)
- 소방서 (FireStation 노드)

**4. 매물 데이터**
- Neo4j: Property 노드 생성
- PostgreSQL: listings 테이블에 저장

**5. 관계(엣지) 생성**
- Property -[NEAR_SUBWAY]-> Subway
- Property -[NEAR_BUS]-> BusStop
- Property -[NEAR_HOSPITAL]-> Hospital
- Property -[NEAR_COLLEGE]-> College
- Property -[NEAR_STORE]-> ConvenienceStore
- Property -[NEAR_PARK]-> Park
- Property -[NEAR_CCTV]-> CCTV
- Property -[NEAR_POLICE]-> PoliceStation
- 등등...

### 개별 스크립트 실행 (선택사항)

필요한 경우 개별적으로 실행:

```powershell
cd scripts

# PostgreSQL에만 매물 데이터 임포트
..\apps\backend\.venv\Scripts\python.exe data_import\import_postgres_only.py

# 임베딩 생성 (RAG용)
..\apps\backend\.venv\Scripts\python.exe build_embeddings.py
```

### 데이터 임포트 실시간 모니터링

임포트가 진행되는 동안 새 터미널에서 실시간 확인:

```powershell
cd scripts
.\monitor_import.ps1
```

5초마다 자동으로 업데이트되며 다음을 표시:
- Neo4j 노드 개수 (Property, Subway, Hospital 등)
- Neo4j 관계(엣지) 개수
- PostgreSQL 레코드 개수

### 데이터 확인

**PostgreSQL 데이터 확인:**
```powershell
docker exec -it skn18-final-1team-postgres-1 psql -U postgres -d realestate -c "SELECT COUNT(*) FROM listings;"
```

**Neo4j 그래프 확인 (명령어):**
```powershell
# 노드 개수 확인
docker exec -i skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p password123 "MATCH (n) RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC;"

# 관계 개수 확인
docker exec -i skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p password123 "MATCH ()-[r]->() RETURN type(r) as relationship, count(r) as count ORDER BY count DESC LIMIT 10;"
```

**Neo4j 브라우저 확인:**
- 브라우저에서 `http://localhost:7474` 접속
- 다음 쿼리 실행:
```cypher
// 전체 노드 수 확인
MATCH (n) RETURN count(n);

// Property 노드 샘플 조회
MATCH (p:Property) RETURN p LIMIT 10;

// 관계 확인
MATCH (p:Property)-[r]->(f) RETURN p, r, f LIMIT 20;
```

---

## 문제 해결

### 포트 충돌
- 백엔드: 8000번 포트
- 프론트엔드: 3000번 포트
- PostgreSQL: 5432번 포트
- Neo4j: 7474, 7687번 포트
- Redis: 6379번 포트

이미 사용 중인 포트가 있다면 `.env` 파일에서 변경하세요.

### 데이터베이스 연결 오류
- PostgreSQL, Neo4j, Redis가 실행 중인지 확인
- `.env` 파일의 연결 정보가 올바른지 확인

### 프론트엔드 빌드 오류
```bash
# node_modules 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install
```

### Python 패키지 충돌
```bash
# 가상환경 재생성
rmdir /s /q .venv
uv venv
uv pip install -r requirements.txt
```

---

## 개발 팁

1. **핫 리로드**: 프론트엔드와 백엔드 모두 코드 변경 시 자동으로 재시작됩니다.
2. **API 테스트**: `http://localhost:8000/admin`에서 Django Admin 사용 가능
3. **Neo4j 브라우저**: `http://localhost:7474`에서 그래프 데이터 확인 가능
4. **로그 확인**: 각 터미널에서 실시간 로그를 볼 수 있습니다.

---

## Docker로 돌아가기

다시 Docker를 사용하고 싶다면:

```bash
docker-compose up -d
```
