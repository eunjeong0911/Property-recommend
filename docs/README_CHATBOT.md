# 부동산 챗봇 실행 및 접속 가이드

이 가이드는 Docker를 사용하여 부동산 챗봇 서비스를 실행하고 접속하는 방법을 설명합니다.

## 1. 서비스 실행 (Docker Compose)

프로젝트 루트 디렉토리(`c:\python\SKN18-FINAL-1TEAM`)에서 터미널을 열고 다음 명령어를 실행하세요.

```bash
# 모든 서비스 빌드 및 백그라운드 실행
docker-compose up -d --build
```

이 명령어는 다음 서비스들을 실행합니다:

- **Frontend**: Next.js 웹 애플리케이션 (포트 3000)
- **Backend**: FastAPI 서버 (포트 8000)
- **RAG**: 챗봇 로직 서버 (포트 8001)
- **Neo4j**: 그래프 데이터베이스 (포트 7474, 7687)
- **Postgres**: 관계형 데이터베이스 (포트 5432)
- **Redis**: 캐시 서버 (포트 6379)

## 2. 실행 상태 확인

서비스가 정상적으로 떴는지 확인하려면 다음 명령어를 사용하세요.

```bash
docker-compose ps
```

모든 컨테이너의 상태(State)가 `Up`으로 되어 있어야 합니다.

로그를 확인하고 싶다면:

```bash
# 전체 로그 확인
docker-compose logs -f

# 특정 서비스(예: frontend) 로그 확인
docker-compose logs -f frontend
```

## 3. 서비스 접속

### 🖥️ 프론트엔드 (사용자 화면)

웹 브라우저를 열고 다음 주소로 접속하세요.

- **URL**: [http://localhost:3000](http://localhost:3000)
- 우측 하단의 **챗봇 아이콘**을 클릭하여 대화를 시작할 수 있습니다.
- **테스트 질문**: "연세대학교 근처 원룸 찾아줘", "강남역 근처 오피스텔 있어?"

### ⚙️ 백엔드 API (Swagger UI)

API 문서를 확인하거나 직접 테스트하려면 다음 주소로 접속하세요.

- **RAG 서버**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **메인 백엔드**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 🗄️ Neo4j 데이터베이스 (Browser)

데이터를 직접 확인하거나 Cypher 쿼리를 실행하려면:

- **URL**: [http://localhost:7474](http://localhost:7474)
- **ID**: `neo4j`
- **Password**: `password` (또는 `.env` 파일에 설정된 비밀번호)

## 4. 종료 방법

서비스를 종료하려면 다음 명령어를 실행하세요.

```bash
docker-compose down
```
