# Docker 배포 및 데이터 Import 가이드

## 개요

이 가이드는 Docker 환경에서 부동산 매물 추천 LLM 서비스를 배포하고 데이터를 import하는 방법을 설명합니다.

## 사전 요구사항

- Docker Desktop 설치 (Windows/Mac) 또는 Docker Engine (Linux)
- Docker Compose v2.0 이상
- 최소 8GB RAM (권장: 16GB)
- 최소 20GB 디스크 공간

## 1. 환경 설정

### 1.1 환경 변수 파일 생성

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env
```

### 1.2 필수 환경 변수 설정

`.env` 파일을 열어 다음 변수들을 설정하세요:

```bash
# PostgreSQL 설정
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=realestate
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Neo4j 설정
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password

# Kakao API (지오코딩용)
KAKAO_API_KEY=your_kakao_api_key

# OpenAI API (RAG용)
OPENAI_API_KEY=your_openai_api_key

# Django 설정
DJANGO_SECRET_KEY=your_django_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

## 2. 서비스 시작

### 2.1 모든 서비스 시작

```bash
# 백그라운드에서 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 2.2 서비스 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 예상 출력:
# NAME                COMMAND                  SERVICE    STATUS
# postgres            "docker-entrypoint..."   postgres   Up
# neo4j               "tini -g -- /startup"    neo4j      Up
# redis               "docker-entrypoint..."   redis      Up
# backend             "python manage.py ru..."  backend    Up
# rag                 "python main.py"         rag        Up
# frontend            "docker-entrypoint..."   frontend   Up
```

### 2.3 데이터베이스 마이그레이션

```bash
# Django 마이그레이션 실행
docker-compose exec backend python manage.py migrate
```

## 3. 데이터 Import

### 3.1 전체 데이터 Import

```bash
# scripts 프로필을 사용하여 데이터 import 실행
docker-compose --profile scripts run --rm scripts python data_import/main.py
```

**예상 소요 시간**: 30분 ~ 1시간 (데이터 크기에 따라 다름)

**Import 순서**:
1. 환경 변수 검증
2. 데이터베이스 연결 검증
3. 교통 데이터 (지하철역, 버스정류장)
4. 편의시설 데이터 (의료시설, 대학교, 편의점, 공원)
5. 안전시설 데이터 (CCTV, 안심벨, 경찰서, 소방서)
6. 매물 데이터 (Neo4j, PostgreSQL)
7. 데이터 연결 (Linking)

### 3.2 개별 데이터 Import

특정 데이터만 import하려면:

```bash
# 교통 데이터만
docker-compose --profile scripts run --rm scripts python data_import/importers/transport_importer.py

# 매물 데이터만 (Neo4j)
docker-compose --profile scripts run --rm scripts python data_import/importers/property_importer.py

# 매물 데이터만 (PostgreSQL)
docker-compose --profile scripts run --rm scripts python data_import/importers/postgres_importer.py
```

## 4. 검증

### 4.1 Neo4j 데이터 확인

1. 브라우저에서 http://localhost:7474 접속
2. 로그인 (사용자: neo4j, 비밀번호: .env에 설정한 값)
3. 다음 쿼리 실행:

```cypher
// 매물 수 확인
MATCH (p:Property) RETURN count(p) as property_count

// 지하철역 수 확인
MATCH (s:SubwayStation) RETURN count(s) as subway_count

// 매물-지하철역 연결 확인
MATCH (p:Property)-[r:NEAR_SUBWAY]->(s:SubwayStation)
RETURN count(r) as connections
```

### 4.2 PostgreSQL 데이터 확인

```bash
# PostgreSQL 컨테이너에 접속
docker-compose exec postgres psql -U postgres -d realestate

# 매물 수 확인
SELECT COUNT(*) FROM listings;

# 샘플 데이터 확인
SELECT listing_id, title, address FROM listings LIMIT 5;

# 종료
\q
```

### 4.3 Backend API 확인

```bash
# 헬스체크
curl http://localhost:8000/api/health/

# 매물 목록 (인증 필요할 수 있음)
curl http://localhost:8000/api/listings/
```

### 4.4 RAG 서비스 확인

```bash
# 헬스체크
curl http://localhost:8001/health

# 또는 브라우저에서 http://localhost:8001 접속
```

## 5. 문제 해결

### 5.1 Neo4j 연결 실패

**증상**: `ServiceUnavailable: Unable to retrieve routing information`

**해결 방법**:

```bash
# 1. Neo4j 컨테이너 상태 확인
docker-compose ps neo4j

# 2. Neo4j 로그 확인
docker-compose logs neo4j

# 3. Neo4j 재시작
docker-compose restart neo4j

# 4. 환경 변수 확인
docker-compose --profile scripts run --rm scripts env | grep NEO4J
```

### 5.2 PostgreSQL 연결 실패

**증상**: `psycopg2.OperationalError: could not connect to server`

**해결 방법**:

```bash
# 1. PostgreSQL 컨테이너 상태 확인
docker-compose ps postgres

# 2. PostgreSQL 로그 확인
docker-compose logs postgres

# 3. PostgreSQL 재시작
docker-compose restart postgres

# 4. 환경 변수 확인
docker-compose --profile scripts run --rm scripts env | grep POSTGRES
```

### 5.3 데이터 파일 누락

**증상**: `Data directory not found: /GraphDB_data/...`

**해결 방법**:

```bash
# 1. 로컬에 데이터 파일 존재 확인
ls -la GraphDB_data/

# 2. 컨테이너 내부 확인
docker-compose --profile scripts run --rm scripts ls -la /GraphDB_data/

# 3. 볼륨 마운트 확인
docker-compose config | grep -A 5 "scripts:"
```

### 5.4 지오코딩 실패

**증상**: `Error: KAKAO_API_KEY is not set in .env`

**해결 방법**:

1. Kakao Developers (https://developers.kakao.com)에서 API 키 발급
2. .env 파일에 `KAKAO_API_KEY` 추가
3. 주소 검색 API 권한 활성화 확인

### 5.5 메모리 부족

**증상**: 컨테이너가 OOM(Out of Memory)으로 종료됨

**해결 방법**:

1. Docker Desktop 설정에서 메모리 할당 증가 (최소 4GB, 권장 8GB)
2. 배치 크기 줄이기 (importers 파일에서 `batch_size` 조정)
3. 한 번에 하나의 importer만 실행

### 5.6 포트 충돌

**증상**: `Bind for 0.0.0.0:5432 failed: port is already allocated`

**해결 방법**:

```bash
# Windows에서 사용 중인 포트 확인
netstat -ano | findstr "5432"
netstat -ano | findstr "7687"
netstat -ano | findstr "8000"

# docker-compose.yml에서 포트 변경
# 예: "5433:5432" (호스트:컨테이너)

# 재시작
docker-compose down
docker-compose up -d
```

## 6. 유용한 명령어

### 6.1 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f neo4j
docker-compose logs -f postgres

# 최근 100줄만
docker-compose logs --tail=100 backend
```

### 6.2 컨테이너 접속

```bash
# Backend 컨테이너 접속
docker-compose exec backend bash

# PostgreSQL 컨테이너 접속
docker-compose exec postgres bash

# Scripts 컨테이너 실행 (일회성)
docker-compose --profile scripts run --rm scripts bash
```

### 6.3 데이터베이스 초기화

```bash
# 모든 컨테이너와 볼륨 삭제 (데이터 완전 삭제)
docker-compose down -v

# 이미지 재빌드
docker-compose build --no-cache

# 재시작
docker-compose up -d
```

### 6.4 특정 서비스 재시작

```bash
# Backend만 재시작
docker-compose restart backend

# 이미지 재빌드 후 재시작
docker-compose up -d --build backend
```

## 7. 성능 최적화

### 7.1 배치 크기 조정

데이터 import 속도를 조정하려면 각 importer 파일에서 `batch_size` 변수를 수정하세요:

```python
# scripts/data_import/importers/transport_importer.py
batch_size = 500  # 기본값, 메모리가 충분하면 1000으로 증가
```

### 7.2 병렬 처리

여러 터미널에서 독립적인 importer를 동시에 실행할 수 있습니다:

```bash
# 터미널 1
docker-compose --profile scripts run --rm scripts python data_import/importers/transport_importer.py

# 터미널 2
docker-compose --profile scripts run --rm scripts python data_import/importers/amenity_importer.py
```

## 8. 프로덕션 배포 시 고려사항

### 8.1 보안

- `.env` 파일을 Git에 커밋하지 마세요
- 프로덕션 환경에서는 강력한 비밀번호 사용
- `DJANGO_DEBUG=False` 설정
- HTTPS 사용 (Nginx 리버스 프록시 권장)

### 8.2 백업

```bash
# PostgreSQL 백업
docker-compose exec postgres pg_dump -U postgres realestate > backup.sql

# Neo4j 백업
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/data/backup.dump
```

### 8.3 모니터링

- Docker 컨테이너 헬스체크 설정
- 로그 수집 (ELK Stack, Grafana Loki 등)
- 메트릭 모니터링 (Prometheus, Grafana 등)

## 9. 추가 리소스

- [Docker 공식 문서](https://docs.docker.com/)
- [Neo4j 공식 문서](https://neo4j.com/docs/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [Django 공식 문서](https://docs.djangoproject.com/)

## 10. 지원

문제가 발생하면:
1. 이 가이드의 문제 해결 섹션 확인
2. 로그 확인 (`docker-compose logs`)
3. GitHub Issues에 문제 보고
