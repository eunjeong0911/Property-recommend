# 🚀 프로젝트 실행 가이드

## 필수 준비
- Docker & Docker Compose 설치 필요

## 실행 명령어

```bash
# 1. 환경 변수 파일 생성
cp .env.example .env

# 2. .env 파일 열어서 API 키 입력
# OPENAI_API_KEY=your_key
# KAKAO_API_KEY=your_key
# NEO4J_PASSWORD=your_password

# 3. Docker 실행
docker-compose up -d

# 4. 데이터베이스가 준비될 때까지 대기 (약 30초)
# Neo4j와 PostgreSQL의 헬스체크가 통과될 때까지 기다립니다
docker-compose ps

# 5. 데이터베이스 마이그레이션
docker-compose exec backend python manage.py migrate

# 6. 데이터 Import (30분~1시간 소요)
# scripts 프로필을 사용하여 데이터 import 실행
# depends_on 헬스체크 덕분에 데이터베이스가 준비된 후 시작됩니다
docker-compose --profile scripts run --rm scripts python data_import/main.py
```

## 접속 주소

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Neo4j Browser: http://localhost:7474
- RAG/Chatbot: http://localhost:8001
- Recommendation: http://localhost:8002
- OpenSearch: http://localhost:9200
- OpenSearch Dashboards: http://localhost:5601

## 자주 쓰는 명령어

```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 로그 확인
docker-compose logs -f

# 전체 초기화 (데이터 삭제)
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## 선택 사항

```bash
# Jupyter Notebook 실행
docker-compose --profile analytics up -d analytics
# 접속: http://localhost:8888

# 개별 데이터 Import 실행
docker-compose --profile scripts run --rm scripts python data_import/importers/transport_importer.py
docker-compose --profile scripts run --rm scripts python data_import/importers/property_importer.py

# PostgreSQL Land 테이블만 데이터 적재 (빌라주택, 아파트, 오피스텔, 원투룸)
docker-compose --profile scripts run --rm scripts python data_import/import_postgres_only.py

# OpenSearch 매물 인덱싱 (검색 기능 사용 시 필요)
docker-compose --profile scripts run --rm scripts python es_bulk_index.py
# OpenSearch Dashboards 접속: http://localhost:5601
```

## 문제 해결

### Neo4j 연결 실패
```bash
# Neo4j 컨테이너 상태 확인
docker-compose ps neo4j

# Neo4j 로그 확인
docker-compose logs neo4j

# Neo4j 재시작
docker-compose restart neo4j
```

### PostgreSQL 연결 실패
```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose ps postgres

# PostgreSQL 로그 확인
docker-compose logs postgres

# PostgreSQL 재시작
docker-compose restart postgres
```

### 데이터 Import 실패
```bash
# 환경 변수 확인
docker-compose --profile scripts run --rm scripts env | grep -E "NEO4J|POSTGRES|KAKAO"

# 데이터 디렉토리 확인
docker-compose --profile scripts run --rm scripts ls -la /GraphDB_data/

# 상세 로그와 함께 재실행
docker-compose --profile scripts run --rm scripts python data_import/main.py
```

### 포트 충돌
```bash
# 사용 중인 포트 확인 (Windows)
netstat -ano | findstr "5432"
netstat -ano | findstr "7687"
netstat -ano | findstr "8000"

# docker-compose.yml에서 포트 변경 후 재시작
docker-compose down
docker-compose up -d
```

---

**상세 가이드는 [docs/](docs/) 폴더 참조**
