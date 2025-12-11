# 🏠 부동산 RAG 챗봇 시스템 가이드

## 📋 목차

1. [사전 요구 사항](#사전-요구-사항)
2. [프로젝트 시작하기](#프로젝트-시작하기)
3. [데이터 Import](#데이터-import)
4. [서비스 시작](#서비스-시작)
5. [챗봇 사용](#챗봇-사용)
6. [문제 해결](#문제-해결)

---

## 사전 요구 사항

- **Docker Desktop** 설치 및 실행
- **Git** 설치
- `.env` 파일 설정 (OpenAI API Key 필수)

```bash
# .env 파일 필수 항목
OPENAI_API_KEY=sk-...
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=realestate
NEO4J_AUTH=neo4j/password
```

---

## 프로젝트 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN18-FINAL-1TEAM.git
cd SKN18-FINAL-1TEAM
```

### 2. 환경 변수 설정

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 API 키 입력
```

---

## 데이터 Import

### Step 1: 데이터베이스 서비스 시작

```bash
docker-compose up -d postgres neo4j redis
```

### Step 2: 데이터베이스 준비 대기 (약 30초)

```bash
# PostgreSQL 상태 확인
docker-compose logs postgres --tail 5

# Neo4j 상태 확인
docker-compose logs neo4j --tail 5
```

### Step 3: 데이터 Import 실행

```bash
docker-compose --profile scripts run scripts python -m data_import.main
```

**Import 결과 (정상 시):**

```
======================================================================
                         Import 완료 요약
======================================================================
총 작업: 13개
  ✓ 성공: 13개
  ✗ 실패: 0개
======================================================================
✓ 모든 데이터 Import가 성공적으로 완료되었습니다!
```

---

## 서비스 시작

### 전체 서비스 시작

```bash
docker-compose up -d
```

### 서비스 상태 확인

```bash
docker-compose ps
```

**정상 상태:**

```
NAME                        STATUS
skn18-final-1team-backend   Up
skn18-final-1team-frontend  Up
skn18-final-1team-neo4j     Up (healthy)
skn18-final-1team-postgres  Up (healthy)
skn18-final-1team-rag       Up
skn18-final-1team-redis     Up (healthy)
```

---

## 챗봇 사용

### 1. 웹 브라우저 접속

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **RAG API**: http://localhost:8001

### 2. 챗봇 질문 예시

```
"홍대역 근처 보증금 5000만원 이하 원룸 찾아줘"
"강남역 도보 10분 거리 전세 아파트"
"편의점 가까운 신축 오피스텔"
"CCTV 많은 안전한 동네 월세 추천"
```

### 3. 챗봇 작동 방식

```
1. 사용자 질문 입력
   ↓
2. Neo4j에서 위치 기반 매물 검색
   ↓
3. PostgreSQL에서 상세 정보 조회 + 가격 필터링
   ↓
4. GPT-4o-mini로 자연어 답변 생성
   ↓
5. 매물 추천 결과 표시
```

---

## 문제 해결

### 매물 목록이 로드되지 않는 경우

```bash
# 1. 볼륨 완전 삭제 후 재시작
docker-compose down -v

# 2. DB 서비스 먼저 시작
docker-compose up -d postgres neo4j redis

# 3. 30초 대기 후 데이터 재Import
docker-compose --profile scripts run scripts python -m data_import.main

# 4. 전체 서비스 시작
docker-compose up -d
```

### 로그 확인

```bash
# 백엔드 로그
docker-compose logs backend --tail 50

# RAG 로그
docker-compose logs rag --tail 50

# 전체 로그 (실시간)
docker-compose logs -f
```

### 서비스 재시작

```bash
# 특정 서비스 재시작
docker-compose restart backend

# 전체 재시작
docker-compose restart
```

---

## 데이터베이스 스키마

### PostgreSQL (land 테이블)

| 컬럼          | 타입         | 설명          |
| ------------- | ------------ | ------------- |
| land_id       | SERIAL       | PK            |
| land_num      | VARCHAR(20)  | 매물번호      |
| building_type | VARCHAR(20)  | 건물형태      |
| address       | VARCHAR(200) | 주소          |
| deal_type     | VARCHAR(30)  | 거래유형      |
| deposit       | INT          | 보증금 (만원) |
| monthly_rent  | INT          | 월세 (만원)   |
| jeonse_price  | INT          | 전세가 (만원) |
| sale_price    | INT          | 매매가 (만원) |

### Neo4j (Graph Database)

- **Property**: 매물 노드 (id, 좌표)
- **SubwayStation**: 지하철역
- **NEAR_SUBWAY**: 매물-지하철역 관계

---

## 포트 정리

| 서비스        | 포트 | 용도        |
| ------------- | ---- | ----------- |
| Frontend      | 3000 | 웹 UI       |
| Backend       | 8000 | Django API  |
| RAG           | 8001 | 챗봇 API    |
| PostgreSQL    | 5432 | RDB         |
| Neo4j Browser | 7474 | Graph DB UI |
| Neo4j Bolt    | 7687 | Graph DB    |
| Redis         | 6379 | 캐시        |
