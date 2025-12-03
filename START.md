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

# 4. 데이터베이스 마이그레이션
docker-compose exec backend python manage.py migrate

# 5. 데이터 임포트 (30분~1시간 소요)
docker-compose exec backend python ../scripts/data_import/main.py
```

## 접속 주소

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Neo4j Browser: http://localhost:7474
- RAG/Chatbot: http://localhost:8001
- Recommendation: http://localhost:8002

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

# Neo4j 데이터 초기화
docker-compose exec backend python ../scripts/data_import/importers/reset_db.py
```

---

**상세 가이드는 [docs/](docs/) 폴더 참조**
