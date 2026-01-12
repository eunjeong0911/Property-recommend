# SKN18-FINAL-1TEAM - 부동산 매물 추천 AI 플랫폼

## 1. 프로젝트 개요

### 1.1 프로젝트 소개
서울시 부동산 매물 데이터를 기반으로 사용자에게 최적의 매물을 추천하는 지능형 플랫폼입니다. AI 기반 중개사 신뢰도 평가, 가격 적정성 분석, 자연어 기반 매물 검색 기능을 제공합니다.

### 1.2 핵심 가치
- AI 기반 추천: 머신러닝 모델을 활용한 중개사 신뢰도 평가 및 가격 적정성 분석
- RAG 챗봇: LangGraph 기반 대화형 매물 검색 및 추천 서비스
- 하이브리드 검색: Elasticsearch 전문 검색 + Neo4j 그래프 검색의 결합
- 그래프 DB: Neo4j를 활용한 매물-시설 간 관계 기반 검색
- 실시간 분석: Elasticsearch를 통한 매물 통계 및 트렌드 분석

### 1.3 프로젝트 배경

#### 설문조사 결과 분석

타 서비스 이용 불편사항:
| 불편사항 | 비율 |
|---------|------|
| 허위매물 | 58.3% |
| UI/UX | 16.7% |
| 정보부족 | 12.5% |
| 기타 | 8.3% |
| 매물관리 | 4.2% |

신규 서비스 도입 희망 기능:
| 희망 기능 | 비율 |
|----------|------|
| 허위매물 판별 | 25.0% |
| 매물비교/추천 | 21.4% |
| 기타 | 17.9% |
| 검색/필터 개선 | 14.3% |
| 후기/리뷰 | 10.7% |
| 실거래가 | 7.1% |
| 사진/정보 | 3.6% |

#### 설문조사 기반 구현 기능

허위매물 판별:
- 중개사 신뢰도 모델로 거래성사율, 운영기간, 자격구분 등을 활용한 A/B/C 등급 분류
- 매물 상세정보에서 중개사 신뢰도 즉시 확인 가능

매물비교/추천:
- 가격 적정성 모델로 지역별 시세 대비 저렴/적정/비쌈 분류
- 매물 상세정보에서 가격 적정성 즉시 확인 가능

검색/필터 개선:
- AI 챗봇을 통한 자연어 기반 매물 검색
- Elasticsearch + Neo4j 하이브리드 검색

UI/UX 개선:
- 메인 화면에서 채팅으로 바로 원하는 매물 검색 가능
- 여러 매물 동시 비교 화면 제공

---

## 2. 주요 기능

### 2.1 AI 챗봇 (RAG)
- 자연어 기반 매물 검색 ("강남역 근처 깨끗한 원룸 찾아줘")
- LangGraph 기반 질문 분류 및 응답
- Neo4j + PostgreSQL + Elasticsearch 하이브리드 검색
- 하드 필터 (지역, 가격) + 소프트 필터 (깨끗한, 조용한) 동시 처리
- 1순위, 2순위, 3순위 매물 랭킹 추천
- 주변 시설까지 거리(m) 및 도보 시간(분) 제공
- CCTV, 비상벨 개수 등 안전 정보 제공

### 2.2 ML 모델
- 중개사 신뢰도 모델: A/B/C 등급 분류 (Test Accuracy 73.24%)
- 가격 적정성 모델: 저렴/적정/비쌈 분류 (Test Accuracy 73.46%)

### 2.3 매물 검색 및 필터링
- 서울 25개 구 지역 필터
- 거래유형 필터 (매매, 전세, 월세, 단기임대)
- 건물유형 필터 (아파트, 오피스텔, 빌라주택, 원투룸)
- 주소/매물번호 검색
- 복합 필터링 지원

### 2.4 지도 기능
- 카카오맵 기반 매물 위치 표시
- 마커 클릭 시 매물 상세 페이지 이동
- 주변 시설 정보 표시 (지하철, 편의점, 병원 등)

### 2.5 온도 지표 시스템
- 교통 온도 (30~43도): 지하철역, 버스정류장 접근성
- 공원 온도 (30~43도): 주변 공원 품질 및 거리
- 편의시설 온도 (30~43도): 편의점, 병원, 약국 접근성
- 안전 온도 (0~100점): 범죄율, CCTV, 지구대 등
- 허위매물 온도 (0~100점): 중개사 신뢰도 기반

### 2.6 커뮤니티
- 자유게시판 / 행정동별 게시판
- 댓글 및 좋아요 기능
- 매물 찜 목록 관리

### 2.7 사용자 기능
- Google OAuth 소셜 로그인
- 선호도 설문조사 (신규 사용자)
- 검색/조회 이력 추적
- 프로필 관리

---

## 3. 기술 스택

### 3.1 Frontend
| 기술 | 버전 | 용도 |
|------|------|------|
| Next.js | 14 | React 프레임워크 (App Router) |
| TypeScript | 5.3 | 타입 안정성 |
| Tailwind CSS | 3.4 | 스타일링 |
| React Context API | - | 상태 관리 |
| Kakao Map API | - | 지도 표시 |
| NextAuth.js | - | 인증 (Google OAuth) |

### 3.2 Backend
| 기술 | 버전 | 용도 |
|------|------|------|
| Django | 4.2 | 웹 프레임워크 |
| Django REST Framework | - | RESTful API |
| FastAPI | 0.109 | RAG/Reco 서버 |
| Python | 3.11 | 백엔드 언어 |
| JWT | - | 인증 토큰 |

### 3.3 Database
| 기술 | 버전 | 용도 |
|------|------|------|
| PostgreSQL | 16 | 관계형 DB + pgvector |
| Neo4j | 5.15 | 그래프 DB (APOC 플러그인) |
| Redis | 7 | 캐싱 및 세션 |
| Elasticsearch | 8.17 | 전문 검색 + 벡터 검색 |

### 3.4 AI/ML
| 기술 | 용도 |
|------|------|
| OpenAI GPT-4 | LLM |
| LangChain / LangGraph | RAG 파이프라인 |
| scikit-learn | ML 모델 |
| LightGBM | 가격 적정성 모델 |
| Logistic Regression | 중개사 신뢰도 모델 |
| SHAP | 모델 해석 |
| text-embedding-3-large | 벡터 임베딩 (3072차원) |

### 3.5 Infrastructure
| 기술 | 용도 |
|------|------|
| Docker | 컨테이너화 |
| Docker Compose | 서비스 오케스트레이션 |
| uv | Python 패키지 관리 |
| npm | Node.js 패키지 관리 |

---

## 4. 시스템 아키텍처

### 4.1 전체 시스템 구조

```
                            +-------------+
                            |   사용자    |
                            +------+------+
                                   |
                                   v
+------------------------------------------------------------------+
|                    Frontend (Next.js 14)                          |
|  - 챗봇 인터페이스                                                 |
|  - 매물 검색 & 필터링                                              |
|  - 커뮤니티, 찜 목록                                               |
|  - 카카오맵 지도                                                   |
+---------------------------+--------------------------------------+
                            | REST API / WebSocket
                            v
+------------------------------------------------------------------+
|                  Backend (Django REST API)                        |
|  - 사용자 인증/인가 (JWT)                                          |
|  - 매물 CRUD API                                                  |
|  - 커뮤니티 API                                                    |
+----+----------+----------+----------+----------------------------+
     |          |          |          |
     v          v          v          v
+--------+ +--------+ +--------+ +--------+
|PostgreSQL| | Neo4j | | Redis | |  ES    |
|+pgvector| | Graph | | Cache | |8.17    |
+--------+ +--------+ +--------+ +--------+

     ^                    ^
     |                    |
+----+----+          +----+----+
|   RAG   |          |  Reco   |
| Server  |          | Server  |
|(FastAPI)|          |(FastAPI)|
|- 챗봇   |          |- ML추천 |
|- 검색   |          |- 신뢰도 |
+----+----+          |- 가격   |
     |               +---------+
     v
+---------+
| OpenAI  |
+---------+
```

### 4.2 주요 컴포넌트

Frontend Layer:
- Next.js 14 (App Router)
- TypeScript + Tailwind CSS
- NextAuth.js (Google OAuth)

Backend Layer:
- Django 4.2 + DRF
- JWT 인증
- RESTful API

Data Layer:
- PostgreSQL 16: 매물 데이터, 사용자 정보
- Neo4j 5.15: 매물-시설 관계 그래프
- Elasticsearch 8.17: 하이브리드 검색 (키워드 + 벡터)
- Redis 7: 세션 캐시

AI/ML Services:
- RAG Server: LangGraph 기반 챗봇
- Reco Server: ML 모델 (신뢰도, 가격)

### 4.3 데이터 흐름

매물 검색 흐름:
```
사용자 -> Frontend -> Backend -> PostgreSQL/Neo4j/Elasticsearch
-> 하이브리드 검색 (Neo4j 60% + ES 40%)
-> Backend -> Frontend -> 사용자
```

챗봇 대화 흐름:
```
사용자 질문 -> Frontend -> RAG Server
-> LangGraph Pipeline:
  1. classify_node (질문 분류)
  2. parallel_search (Neo4j + Vector 병렬)
  3. es_rerank (텍스트 재정렬)
  4. sql_search (상세 정보)
  5. generate_node (GPT-4 응답)
-> Frontend -> 사용자
```

ML 모델 추론 흐름:
```
매물 데이터 -> Reco Server
-> Trust Model (중개사 신뢰도: A/B/C)
-> Price Model (가격 적정성: 저렴/적정/비쌈)
-> Backend -> Frontend
```

---

## 5. 프로젝트 구조

```
SKN18-FINAL-1TEAM/
|
+-- apps/                          # 애플리케이션 코드
|   +-- backend/                   # Django 백엔드
|   |   +-- apps/
|   |   |   +-- users/            # 사용자 인증 및 이력 관리
|   |   |   +-- community/        # 커뮤니티 기능
|   |   |   +-- listings/         # 매물 관리
|   |   |   +-- recommend/        # 추천 시스템
|   |   |   +-- graph/            # Neo4j 그래프 분석
|   |   |   +-- search/           # Elasticsearch 검색
|   |   +-- config/               # Django 설정
|   |   +-- requirements.txt
|   |
|   +-- frontend/                  # Next.js 프론트엔드
|   |   +-- src/
|   |   |   +-- app/              # 페이지 라우트
|   |   |   +-- components/       # React 컴포넌트
|   |   |   +-- api/              # API 클라이언트
|   |   |   +-- hooks/            # 커스텀 훅
|   |   |   +-- types/            # TypeScript 타입
|   |   +-- package.json
|   |
|   +-- rag/                       # RAG 챗봇 서버 (FastAPI)
|   |   +-- nodes/                # LangGraph 노드
|   |   +-- graphs/               # 그래프 정의
|   |   +-- prompts/              # 프롬프트 템플릿
|   |   +-- main.py
|   |
|   +-- reco/                      # 추천 서버 (FastAPI)
|       +-- models/               # ML 모델
|       |   +-- trust_model/      # 중개사 신뢰도 모델
|       |   +-- price_model/      # 가격 적정성 모델
|       +-- serve.py
|
+-- data/                          # 데이터 파일
|   +-- Crawling/                 # 크롤링 원본 데이터
|   +-- RDB/                      # PostgreSQL용 데이터
|   +-- GraphDB_data/             # Neo4j용 데이터
|   +-- brokerInfo/               # 중개사 정보
|
+-- docs/                          # 문서
|   +-- architecture.md
|   +-- api_spec.md
|   +-- erd.md
|   +-- graph_schema.md
|
+-- infra/                         # 인프라 설정
|   +-- docker/                   # Dockerfile들
|   +-- postgres/                 # PostgreSQL 초기화
|   +-- elasticsearch/            # ES 매핑
|
+-- scripts/                       # 스크립트
|   +-- dataCrawling/             # 크롤링 스크립트
|   +-- data_import/              # 데이터 임포트
|
+-- docker-compose.yml             # Docker 서비스 정의
+-- .env                          # 환경변수
+-- README.md
```

---

## 6. ML 모델

### 6.1 중개사 신뢰도 모델 (Trust Model)

목적: 부동산 중개사의 신뢰도를 A/B/C 등급으로 분류

#### 데이터
- 출처: 크롤링 데이터 + V-WORLD API (중개업소 정보, 중개업자 정보)
- 규모: 351개 중개사무소
- 매칭: 3단계 매칭 (중개사무소명+대표자명, 등록번호+중개사무소명, 중개사무소명+대표자명)

#### 타겟 생성
```
1. 거래성사율 계산
   거래성사율 = 거래완료 / (거래완료 + 등록매물)

2. 지역별 표준화 (Z-score)
   Performance_Zscore = (거래성사율 - 지역평균) / 지역표준편차

3. 자격점수 표준화
   Qual_Zscore = (자격점수 - 평균) / 표준편차

4. 복합 Z-score (성사율 70% + 자격 30%)
   Zscore = Performance_Zscore * 0.7 + Qual_Zscore * 0.3

5. 대표자구분 가중치 적용
   공인중개사: 0.0, 법인: +0.2, 중개보조원: -0.1, 중개인: -0.3

6. 등급 분류 (Train 기준 분위수)
   A등급: 상위 30% (Zscore_조정 > 70th percentile)
   B등급: 중위 40% (30th ~ 70th percentile)
   C등급: 하위 30% (Zscore_조정 < 30th percentile)
```

#### Feature (총 14개)

실적 지표 (3개) - log 변환 적용:
- 등록매물_log, 총거래활동량_log, 1인당_거래량_log

인력 지표 (3개):
- 총_직원수, 중개보조원_비율, 자격증_보유비율

경험 지표 (3개):
- 운영기간_년, 숙련도_지수, 운영_안정성

구조 지표 (1개):
- 대형사무소

대표자 자격 (2개):
- 대표_공인중개사, 대표_법인

지역 지표 (2개):
- 지역_경쟁강도, 1층_여부

#### 모델 성능

| 지표 | 값 |
|------|-----|
| Test Accuracy | 73.24% |
| Train Accuracy | 80.43% |
| 과적합 정도 | 7.19% |
| CV Mean | 74.76% (+/-7.60%) |

등급별 성능 (Test 기준):
| 등급 | Precision | Recall | F1-Score |
|------|-----------|--------|----------|
| C등급(0) | 0.62 | 0.94 | 0.75 |
| B등급(1) | 0.75 | 0.69 | 0.72 |
| A등급(2) | 0.87 | 0.65 | 0.74 |

특징:
- C등급(신뢰도 낮음) 재현율이 가장 높음 (94%) - 문제 중개사 잘 감지
- A등급(신뢰도 높음) 정밀도가 가장 높음 (87%) - 우수 중개사 정확히 분류

알고리즘:
- 모델: Logistic Regression
- 최적화: GridSearchCV (144개 조합 탐색)
- 하이퍼파라미터: C=1, penalty='l1', solver='saga', class_weight='balanced'

---

### 6.2 가격 적정성 모델 (Price Model)

목적: 월세 매물의 가격을 저렴/적정/비쌈으로 분류

#### 데이터
- 학습 데이터: 2024.08~2025.08 서울시 월세 실거래가 (1년치)
- 테스트 데이터: 2025.09~2025.10 월세 실거래가
- 출처: 서울시 월세 실거래가 + 한국은행 금리 데이터

#### 타겟 생성
```
1. 환산보증금 계산
   적용이자율 = (기준금리 + 2.0%) / 100
   환산보증금(만원) = 보증금(만원) + (임대료(만원) x 12) / 적용이자율

2. 평당가 계산
   환산보증금_평당가 = 환산보증금(만원) / 전용평수

3. 행정동x건물용도별 분위수 분류
   저렴(0): 33.3% 미만
   적정(1): 33.3% ~ 66.7%
   비쌈(2): 66.7% 초과
```

#### Feature (총 19개)

지역 정보 (4개):
- 자치구명_LE, 법정동명_LE, 자치구_건물용도_LE, 구_권역

건물 특성 (6개):
- 건물용도, 임대면적, 면적_qcat, 층, 건축연차, 건축시대

지역 집계 (3개):
- 자치구_월별_임대료수준_구간, 자치구_용도_월별_임대료_평균, 법정동_용도_월별_임대료_평균

금리 정보 (2개):
- KORIBOR, 기업대출

가격 구조 (2개):
- 보증금임대료비율_구간, 보증금_지역대비

교호작용 (2개):
- 면적_x_건축연차, 자치구거래량_x_면적

#### 모델 성능 비교

| 모델 | Accuracy | F1-macro |
|------|----------|----------|
| LightGBM | 73.46% | 0.7317 |
| XGBoost | 68.80% | 0.6854 |
| LSTM | 67.04% | 0.6715 |

LightGBM 등급별 성능:
| 등급 | Precision | Recall | F1 |
|------|-----------|--------|-----|
| 저렴(0) | 0.85 | 0.85 | 0.85 |
| 적정(1) | 0.63 | 0.63 | 0.63 |
| 비쌈(2) | 0.74 | 0.74 | 0.74 |

알고리즘:
- 모델: LightGBM
- 최적화: Early Stopping (50 라운드)
- 선택 이유: Tree 기반 모델이 Label Encoding과 교호작용 피처에 효율적

#### SHAP 분석 (TOP-3)
1. 보증금_지역대비: 지역 평균 대비 상대적 가격
2. 임대면적: 면적 차이로 가격 등급 변화
3. 자치구_월별_임대료수준_구간: 최근 지역 임대료 수준

---

## 7. RAG 챗봇

### 7.1 LangGraph 노드 구조

| 노드 | 파일명 | 역할 |
|------|--------|------|
| classify_node | classify_node.py | 사용자 질문 분류 |
| neo4j_search_node | neo4j_search_node.py | Neo4j 그래프 DB 검색 |
| sql_search_node | sql_search_node.py | PostgreSQL 매물 검색 |
| es_search_node | es_search_node.py | Elasticsearch 전문 검색 |
| vector_search_node | vector_search_node.py | 벡터 유사도 검색 |
| cache_filter_node | cache_filter_node.py | 캐시 및 필터링 |
| generate_node | generate_node.py | LLM 기반 최종 응답 생성 |

### 7.2 질문 분류 및 라우팅

```
사용자 질문
    |
    v
classify_node (질문 분류)
    |
    +-- risk_analysis_node (전세사기 위험도 분석)
    |   예: "이 매물 안전한가요?"
    |
    +-- landfind_node (매물 찾기)
    |   예: "강남역 근처 원룸 찾아줘"
    |
    +-- preparser_node (소프트 필터 추출)
    |   예: "조용하고 깨끗한 방"
    |
    +-- info_node (부동산 일반 정보)
    |   예: "전세와 월세 차이는?"
    |
    +-- faq_node (서비스 운영 정보)
        예: "회원가입은 어떻게 하나요?"
```

### 7.3 검색 파이프라인

```
landfind_node / preparser_node
    |
    v
agent_orchestrator (GraphDB + RDB 검색)
    |
    +-- neo4jSearch_node (매물/거리/관계 기반 탐색)
    +-- SQL_node (RDB: 매물 상세 조회)
    |
    v
agent_trust (중개사 신뢰도 분석)
agent_price (매물 가격 분석)
    |
    v
Gen_node (LLM 응답 생성)
```

### 7.4 검색 기준
- 지하철역: 반경 1.5km 이내
- 버스/약국: 반경 200m 이내
- 공원: 반경 500m 이내

### 7.5 하이브리드 검색 점수 조합
- Neo4j 그래프 검색: 60%
- Elasticsearch 텍스트 검색: 40%

---

## 8. 데이터베이스 스키마

### 8.1 PostgreSQL ERD

#### Users App
| 테이블 | 설명 |
|--------|------|
| User | Google OAuth 정보, 상태 플래그, 프로필 이미지 |
| LoginHistory | 로그인/로그아웃 로그 |
| SearchHistory | 검색 행동 로그 |
| ListingViewHistory | 매물 조회 로그 |
| Wishlist | 찜 상태 |
| WishlistHistory | 찜 이력 |
| PreferenceSurvey | 사용자 우선순위 JSON 저장 |

#### Community App
| 테이블 | 설명 |
|--------|------|
| CommunityPost | 게시판 종류/지역 필드, Soft Delete, 조회수/좋아요 수 |
| CommunityComment | 댓글 (Soft Delete) |
| CommunityPostLike | 사용자-게시글 좋아요 관계 |

#### Listings App
| 테이블 | 설명 |
|--------|------|
| listings | 매물 기본 정보 |
| listing_embeddings | 매물 벡터 임베딩 |

### 8.2 Neo4j 그래프 스키마

#### Nodes
| 노드 | 속성 |
|------|------|
| Property | id, name, address, latitude, longitude, location |
| Subway | id, name, line |
| BusStop | id, name |
| Park | id, name, area, facilities |
| Hospital | id, name, type |
| Pharmacy | id, name |
| ConvenienceStore | id, name |
| District | id, name |

#### Relationships
| 관계 | 설명 |
|------|------|
| (Property)-[:LOCATED_IN]->(District) | 매물이 위치한 구 |
| (Property)-[:NEAR]->(Subway) | 매물 주변 지하철역 |
| (Property)-[:NEAR]->(BusStop) | 매물 주변 버스정류장 |
| (Property)-[:NEAR]->(Park) | 매물 주변 공원 |
| (Property)-[:NEAR]->(Hospital) | 매물 주변 병원 |
| (Property)-[:NEAR]->(Pharmacy) | 매물 주변 약국 |
| (Property)-[:NEAR]->(ConvenienceStore) | 매물 주변 편의점 |

### 8.3 Elasticsearch 인덱스

| 필드 | 타입 | 설명 |
|------|------|------|
| land_num | keyword | 매물 번호 (고유 ID) |
| address | text (nori) | 전체 주소 |
| search_text | text (nori) | 검색용 전처리 텍스트 |
| style_tags | keyword[] | 스타일 태그 배열 |
| building_type | keyword | 건물 형태 |
| deal_type | keyword | 거래 유형 |
| deposit | integer | 보증금 (만원) |
| monthly_rent | integer | 월세 (만원) |
| location | geo_point | 좌표 (lat, lon) |

---

## 9. API 명세

### 9.1 인증 API
```
POST /api/users/auth/google/       # Google OAuth 로그인
POST /api/users/auth/login/        # 이메일/비밀번호 로그인
POST /api/users/token/refresh/     # 토큰 갱신
POST /api/users/logout/            # 로그아웃
```

### 9.2 사용자 API
```
GET    /api/users/me/                    # 내 정보 조회
PATCH  /api/users/me/update/             # 내 정보 수정
DELETE /api/users/me/                    # 계정 삭제
POST   /api/users/me/profile-image/      # 프로필 이미지 업로드
GET    /api/users/preference-survey/     # 선호도 조사 조회
POST   /api/users/preference-survey/     # 선호도 조사 제출
GET    /api/users/history/search/        # 검색 이력 조회
POST   /api/users/history/search/        # 검색 이력 저장
POST   /api/users/history/view/          # 조회 이력 저장
```

### 9.3 찜 목록 API
```
GET    /api/users/wishlist/              # 찜 목록 조회
POST   /api/users/wishlist/              # 찜 추가
DELETE /api/users/wishlist/<listing_id>/ # 찜 삭제
```

### 9.4 매물 API
```
GET    /api/listings/lands/              # 매물 목록 조회
GET    /api/listings/lands/<id>/         # 매물 상세 조회
GET    /api/listings/lands/locations/    # 매물 위치 조회 (지도용)
```

### 9.5 커뮤니티 API
```
GET    /api/community/posts/             # 게시글 목록
POST   /api/community/posts/             # 게시글 작성
GET    /api/community/posts/<id>/        # 게시글 상세
PATCH  /api/community/posts/<id>/        # 게시글 수정
DELETE /api/community/posts/<id>/        # 게시글 삭제
POST   /api/community/posts/<id>/comments/  # 댓글 작성
POST   /api/community/posts/<id>/like/   # 좋아요
DELETE /api/community/posts/<id>/like/   # 좋아요 취소
```

### 9.6 RAG API
```
POST   /query                            # 챗봇 질문
```

### 9.7 추천 API
```
POST   /recommend                        # 추천 매물 조회
```

---

## 10. 설치 및 실행 가이드

### 10.1 사전 요구사항
- Docker Desktop
- Python 3.11+
- Node.js 18+
- Git

### 10.2 환경변수 설정

.env.example 파일을 복사하여 .env 파일 생성 후 필수 값 입력:

```bash
# 필수 설정
POSTGRES_PASSWORD=your_password
NEO4J_PASSWORD=your_password
OPENAI_API_KEY=your_api_key
NEXTAUTH_SECRET=your_secret

# 선택 설정 (기능별)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
NEXT_PUBLIC_KAKAO_MAP_KEY=your_kakao_key
```

NEXTAUTH_SECRET 생성:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 10.3 Docker Compose 실행 (권장)

```bash
# 1. 인프라 서비스 먼저 실행
docker compose up -d postgres neo4j redis elasticsearch

# 2. 각 서비스 빌드
docker compose build backend rag reco frontend

# 3. 전체 서비스 시작
docker compose up -d

# 4. 서비스 상태 확인
docker compose ps

# 5. Django 마이그레이션
docker compose exec backend python manage.py migrate

# 6. 데이터 Import (30분~1시간 소요)
docker compose --profile scripts run --rm scripts python 03_import/import_all.py
```

### 10.4 로컬 개발 환경 (개별 실행)

Backend (Django):
```bash
cd apps/backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Frontend (Next.js):
```bash
cd apps/frontend
npm install
npm run dev
```

RAG Server (FastAPI):
```bash
cd apps/rag
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

Reco Server (FastAPI):
```bash
cd apps/reco
pip install -r requirements.txt
python serve.py
```

### 10.5 접속 주소

| 서비스 | URL | 설명 |
|--------|-----|------|
| Frontend | http://localhost:3000 | 메인 웹사이트 |
| Backend API | http://localhost:8000 | Django REST API |
| RAG/Chatbot | http://localhost:8001 | AI 챗봇 서비스 |
| Recommendation | http://localhost:8002 | 추천 서비스 |
| Neo4j Browser | http://localhost:7474 | Neo4j 그래프 DB 관리 |
| Kibana | http://localhost:5601 | Elasticsearch 대시보드 |

---

## 11. 데이터 파이프라인

### 11.1 실행 모드

| 모드 | 스크립트 | 역할 | 용도 |
|------|----------|------|------|
| 크롤링 | crawl_seoul.py | 웹사이트에서 최신 매물 데이터 수집 | DB 갱신 없이 데이터만 수집 |
| 데이터 적재 | run_neo4j_full_import.py | 수집된 데이터를 가공하여 DB에 적재 | 로직 수정 후 DB 재적재 |
| 전체 실행 | run_all_process.py | 크롤링 + 적재 순차 실행 | 정기 배치, 시스템 초기화 |

### 11.2 Docker 환경 실행

크롤링만 실행:
```bash
docker-compose run --rm crawling python "scripts/dataCrawling/피터팬 매물 데이터/crawl_seoul.py"
```

데이터 적재만 실행:
```bash
docker-compose run --rm crawling python scripts/data_import/run_neo4j_full_import.py
```

전체 파이프라인 실행:
```bash
docker-compose run --rm crawling python scripts/data_import/run_all_process.py
```

### 11.3 데이터 적재 프로세스

1. Geocoding: 주소 -> 좌표 변환 (data/GraphDB_data 생성)
2. Preprocessing: LLM 활용 설명/태그 생성 (data/RDB 생성)
3. Transport/Amenity: 인프라 데이터 적재
4. Reference DB: PostgreSQL, Neo4j, OpenSearch 적재
5. Embedding: 벡터 생성 및 인덱싱
6. Linking: 데이터 간 관계 연결

### 11.4 ML 모델 실행

중개사 신뢰도 모델:
```bash
# Step 1: 데이터 전처리
docker compose run --rm reco python models/trust_model/data_preprocessing/run_all_preprocessing.py

# Step 2: 모델 학습
docker compose run --rm reco python models/trust_model/run_all.py

# Step 3: 중개사 기본정보 Import
docker compose --profile scripts run --rm scripts python 03_import/reimport_brokers.py

# Step 4: Trust Score 예측 및 DB 저장
docker compose --profile scripts run --rm scripts python 04_analysis/trust_prediction/predict_trust_scores.py
```

가격 적정성 모델:
```bash
# Step 1: 데이터 전처리
docker compose run --rm reco python models/price_model/ML/src/prepare_wolse_dataset.py

# Step 2: 모델 학습
docker compose run --rm reco python models/price_model/ML/src/main.py

# Step 3: SHAP 분석
docker compose run --rm reco python models/price_model/ML/src/example_shap.py

# Step 4: 매물에 적용
docker compose run --rm reco python models/price_model/ML/src/apply_model_to_json.py
```

---

## 12. 매물 데이터 통계

### 12.1 전체 현황
- 총 매물 수: 9,914개

### 12.2 거래유형별 분포

| 거래유형 | 매물 수 | 비율 |
|---------|--------|------|
| 월세 | 6,351개 | 64.1% |
| 전세 | 1,965개 | 19.8% |
| 단기임대 | 1,014개 | 10.2% |
| 매매 | 582개 | 5.9% |

### 12.3 건물유형별 분포

| 건물유형 | 매물 수 |
|---------|--------|
| 원투룸 | 약 5,000개 |
| 빌라주택 | 약 2,500개 |
| 오피스텔 | 약 1,500개 |
| 아파트 | 약 900개 |

---

## 13. Docker 명령어 참고

### 13.1 기본 명령어

| 명령어 | 설명 |
|--------|------|
| docker compose up -d | 모든 서비스 백그라운드 실행 |
| docker compose down | 서비스 중지 + 컨테이너 삭제 |
| docker compose ps | 서비스 상태 확인 |
| docker compose logs -f | 전체 로그 실시간 확인 |
| docker compose logs -f backend | 특정 서비스 로그 확인 |

### 13.2 이미지 빌드

```bash
# 전체 빌드
docker compose build

# 특정 서비스만 빌드
docker compose build backend rag

# 캐시 무시하고 빌드
docker compose build --no-cache

# 빌드 후 바로 실행
docker compose up -d --build
```

### 13.3 완전 초기화

```bash
# 모든 컨테이너 + 볼륨 + 네트워크 삭제
docker compose down -v --remove-orphans

# 이미지 삭제
docker compose down --rmi all

# 캐시 삭제 후 새로 빌드
docker compose build --no-cache

# 서비스 시작
docker compose up -d
```

### 13.4 Profile 기반 서비스

```bash
# Kibana (Elasticsearch 대시보드)
docker compose --profile dashboards up -d

# Jupyter Notebook (Analytics)
docker compose --profile analytics up -d

# 스크립트 실행
docker compose --profile scripts run --rm scripts python 03_import/<스크립트명>

# 크롤링
docker compose --profile crawling run --rm crawling python <스크립트명>
```

---

## 14. 문제 해결

### 14.1 Migration 오류
```bash
python manage.py showmigrations
# 잘못된 항목은 --fake 초기화 후 재적용
```

### 14.2 Docker 서비스 재시작
```bash
docker-compose down && docker-compose up -d
```

### 14.3 프론트엔드 빌드 캐시
```bash
rm -rf .next && npm run dev
```

### 14.4 ES 연결 실패
```bash
# ES 컨테이너 상태 확인
docker-compose ps elasticsearch

# ES 로그 확인
docker-compose logs elasticsearch

# ES 재시작
docker-compose restart elasticsearch
```

### 14.5 Neo4j 데이터 확인
```bash
docker exec -i realestate-neo4j cypher-shell -u neo4j -p password "MATCH (p:Property) RETURN count(p);"
```

---

## 15. 문서 목록

### 아키텍처 및 설계
- docs/Architecture_Diagrams.md - 전체 시스템 아키텍처 및 시퀀스 다이어그램
- docs/erd.md - 데이터베이스 ERD
- docs/graph_schema.md - Neo4j 그래프 스키마
- docs/폴더구조.md - 프로젝트 폴더 구조

### API 및 백엔드
- docs/api_spec.md - API 명세서
- docs/API_TEST_RESULTS.md - API 테스트 결과
- docs/backend_readme.md - 백엔드 개발 가이드

### 기능 구현
- docs/FILTER_FEATURE.md - 매물 필터링 기능
- docs/MAP_FEATURE.md - 지도 기능
- docs/MAP_DETAIL_FEATURE.md - 지도 상세 기능
- docs/MAP_OVERLAY_FEATURE.md - 지도 오버레이 기능
- docs/DATA_STATISTICS.md - 매물 데이터 통계
- docs/README_CHATBOT.md - 챗봇 기능 가이드

### ML 모델
- docs/PRICE_ML_MODEL.md - 가격 적정성 모델
- apps/reco/models/trust_model/README.md - 중개사 신뢰도 모델
- docs/MODEL_APPLICATION_README.md - 모델 적용 가이드

### 개발 환경
- START.md - 빠른 시작 가이드
- START_FOR_DEVELOPER.md - 개발자 가이드
- docs/가상환경.md - Python 가상환경 설정
- docs/DOCKER_DEPLOYMENT_GUIDE.md - Docker 배포 가이드
- docs/ELASTICSEARCH_GUIDE.md - Elasticsearch 가이드
- docs/NEO4J_DOCUMENTATION.md - Neo4j 가이드

---

## 16. 팀 정보

SKN18-FINAL-1TEAM - SK Networks Family AI Camp 18기 최종 프로젝트

---

Made by SKN18-FINAL-1TEAM
