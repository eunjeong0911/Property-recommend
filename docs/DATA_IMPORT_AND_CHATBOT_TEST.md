# 🏠 부동산 RAG 챗봇 실행 가이드

## 📋 목차

1. [데이터 Import](#1-데이터-import)
2. [챗봇 실행 및 테스트](#2-챗봇-실행-및-테스트)
3. [문제 해결](#3-문제-해결)

---

## 1. 데이터 Import

### 1-1. 데이터베이스 서비스 시작

> ⚠️ **중요**: 데이터 Import 전에 DB 서비스가 완전히 시작되어야 합니다.

```bash
# PostgreSQL, Neo4j, Redis 시작
docker-compose up -d postgres neo4j redis
```

### 1-2. DB 준비 상태 확인 (약 30초 대기)

```bash
# PostgreSQL 준비 확인
docker-compose logs postgres --tail 5
# "database system is ready to accept connections" 메시지 확인

# Neo4j 준비 확인
docker-compose logs neo4j --tail 5
# "Started." 메시지 확인
```

### 1-3. Import 스크립트 실행

```bash
docker-compose --profile scripts run scripts python -m data_import.main
```

### 1-4. Import 성공 확인

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

### 1-5. 데이터 확인 (선택)

```bash
# PostgreSQL 매물 수 확인
docker-compose exec postgres psql -U postgres -d realestate -c "SELECT COUNT(*) FROM land;"
# 결과: 9914
```

---

## 2. 챗봇 실행 및 테스트

### 2-1. 전체 서비스 시작

```bash
docker-compose up -d
```

### 2-2. 서비스 상태 확인

```bash
docker-compose ps
```

**모든 서비스가 `Up` 상태여야 합니다:**

```
NAME                        STATUS
skn18-final-1team-backend   Up
skn18-final-1team-frontend  Up
skn18-final-1team-neo4j     Up (healthy)
skn18-final-1team-postgres  Up (healthy)
skn18-final-1team-rag       Up
skn18-final-1team-redis     Up (healthy)
```

### 2-3. 웹 브라우저 접속

| 서비스         | URL                   | 설명            |
| -------------- | --------------------- | --------------- |
| **프론트엔드** | http://localhost:3000 | 챗봇 UI         |
| 백엔드 API     | http://localhost:8000 | Django REST API |
| RAG API        | http://localhost:8001 | 챗봇 엔진       |
| Neo4j Browser  | http://localhost:7474 | Graph DB 관리   |

### 2-4. 챗봇 테스트 질문

**위치 기반 검색:**

```
"홍대역 근처 원룸 추천해줘"
"강남역 도보 10분 거리 오피스텔"
"서울대학교 근처 자취방"
```

**가격 조건 검색:**

```
"보증금 3000만원 이하 월세 50만원 이하"
"전세 2억 이하 아파트"
"매매 5억 이하 빌라"
```

**편의시설 조건:**

```
"편의점 가까운 원룸"
"병원 근처 오피스텔"
"공원 가까운 신축"
```

**안전 시설 조건:**

```
"CCTV 많은 동네"
"경찰서 가까운 안전한 곳"
```

**복합 조건:**

```
"홍대역 근처 보증금 5000만원 이하 편의점 가까운 원룸"
```

---

## 3. 문제 해결

### 3-1. 매물 목록이 안 보일 때

```bash
# 1. 전체 중지 + 볼륨 삭제
docker-compose down -v

# 2. DB 서비스 먼저 시작
docker-compose up -d postgres neo4j redis

# 3. 30초 대기 후 데이터 재Import
docker-compose --profile scripts run scripts python -m data_import.main

# 4. 전체 서비스 시작
docker-compose up -d
```

### 3-2. 특정 서비스 재시작

```bash
docker-compose restart backend   # 백엔드만
docker-compose restart rag       # RAG만
```

### 3-3. 로그 확인

```bash
docker-compose logs backend --tail 30   # 백엔드 로그
docker-compose logs rag --tail 30       # RAG 로그
docker-compose logs -f                  # 실시간 전체 로그
```

---

## 📌 빠른 시작 요약

```bash
# 1. DB 시작
docker-compose up -d postgres neo4j redis

# 2. 30초 대기 후 데이터 Import
docker-compose --profile scripts run scripts python -m data_import.main

# 3. 전체 서비스 시작
docker-compose up -d

# 4. 브라우저 접속: http://localhost:3000
```
