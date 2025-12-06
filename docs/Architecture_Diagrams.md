# 🏗️ 전체 시스템 아키텍처 다이어그램

## 1. 전체 시스템 아키텍처

```mermaid
flowchart TD
    subgraph CLIENT["👥 Client Layer"]
        USER[사용자]
        WEB[Web Browser]
    end
    
    subgraph FRONTEND["🖥️ Frontend Layer"]
        NEXTJS[Next.js 14<br/>TypeScript<br/>Tailwind CSS]
    end
    
    subgraph BACKEND["⚙️ Backend Services Layer"]
        DJANGO[Django Backend<br/>REST API<br/>Port 8000]
        RAG[RAG Service<br/>LangGraph<br/>Port 8001]
        RECO[Recommendation<br/>ML Models<br/>Port 8002]
    end
    
    subgraph CACHE["💾 Cache Layer"]
        REDIS[(Redis<br/>세션 • 캐싱)]
    end
    
    subgraph DATABASE["🗄️ Database Layer"]
        POSTGRES[(PostgreSQL<br/>+ pgvector)]
        NEO4J[(Neo4j<br/>GraphDB)]
    end
    
    subgraph EXTERNAL["🌐 External Services"]
        OPENAI[OpenAI API]
        KAKAO[Kakao Map]
        GOOGLE[Google OAuth]
    end
    
    USER --> WEB
    WEB --> NEXTJS
    NEXTJS --> DJANGO
    NEXTJS --> RAG
    NEXTJS --> KAKAO
    
    DJANGO --> REDIS
    DJANGO --> POSTGRES
    DJANGO --> NEO4J
    DJANGO --> RECO
    DJANGO --> GOOGLE
    
    RAG --> POSTGRES
    RAG --> NEO4J
    RAG --> OPENAI
    
    RECO --> POSTGRES
    
    classDef frontend fill:#61dafb,stroke:#333,color:#000
    classDef backend fill:#092e20,stroke:#333,color:#fff
    classDef database fill:#336791,stroke:#333,color:#fff
    classDef cache fill:#dc382d,stroke:#333,color:#fff
    classDef external fill:#ff6b6b,stroke:#333,color:#fff
    
    class NEXTJS frontend
    class DJANGO,RAG,RECO backend
    class POSTGRES,NEO4J database
    class REDIS cache
    class OPENAI,KAKAO,GOOGLE external
```

---

## 2. Layered Architecture (계층형 아키텍처)

```mermaid
flowchart TB
    subgraph PRESENTATION["Presentation Layer"]
        direction TB
        P1[UI Components]
        P2[Pages - Next.js Routes]
        P3[Authentication - NextAuth]
    end
    
    subgraph APPLICATION["Application Layer"]
        direction TB
        A1[REST API - Django Views]
        A2[Business Logic - Services]
        A3[Validation - Serializers]
    end
    
    subgraph DOMAIN["Domain Layer"]
        direction TB
        D1[Domain Models]
        D2[Entities - User, Listing]
        D3[Business Rules - 온도 계산]
    end
    
    subgraph INFRASTRUCTURE["Infrastructure Layer"]
        direction TB
        I1[Database Access - ORM]
        I2[Cache - Redis Client]
        I3[External APIs]
    end
    
    subgraph DATA["Data Layer"]
        direction TB
        DB1[(PostgreSQL)]
        DB2[(Neo4j)]
        DB3[(Redis)]
    end
    
    PRESENTATION --> APPLICATION
    APPLICATION --> DOMAIN
    DOMAIN --> INFRASTRUCTURE
    INFRASTRUCTURE --> DATA
    
    classDef layer1 fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef layer2 fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef layer3 fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef layer4 fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef layer5 fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class PRESENTATION layer1
    class APPLICATION layer2
    class DOMAIN layer3
    class INFRASTRUCTURE layer4
    class DATA layer5
```

---

## 3. 데이터 흐름도 (Data Flow Diagram)

```mermaid
flowchart LR
    subgraph INPUT["입력"]
        USER_INPUT[사용자 입력]
        USER_ACTION[사용자 행동]
    end
    
    subgraph PROCESSING["처리"]
        VALIDATION[데이터 검증]
        BUSINESS_LOGIC[비즈니스 로직]
        DATA_TRANSFORM[데이터 변환]
    end
    
    subgraph STORAGE["저장"]
        WRITE_DB[DB 저장]
        WRITE_CACHE[캐시 저장]
    end
    
    subgraph RETRIEVAL["조회"]
        READ_CACHE{캐시 확인}
        READ_DB[DB 조회]
        GRAPH_QUERY[그래프 쿼리]
    end
    
    subgraph OUTPUT["출력"]
        RESPONSE[API 응답]
        UI_RENDER[UI 렌더링]
    end
    
    USER_INPUT --> VALIDATION
    USER_ACTION --> VALIDATION
    
    VALIDATION --> BUSINESS_LOGIC
    BUSINESS_LOGIC --> DATA_TRANSFORM
    
    DATA_TRANSFORM --> WRITE_DB
    DATA_TRANSFORM --> WRITE_CACHE
    
    BUSINESS_LOGIC --> READ_CACHE
    READ_CACHE -->|캐시 히트| RESPONSE
    READ_CACHE -->|캐시 미스| READ_DB
    READ_DB --> GRAPH_QUERY
    GRAPH_QUERY --> RESPONSE
    
    RESPONSE --> UI_RENDER
    
    classDef input fill:#e3f2fd,stroke:#1565c0
    classDef process fill:#fff3e0,stroke:#e65100
    classDef storage fill:#f3e5f5,stroke:#6a1b9a
    classDef retrieval fill:#e8f5e9,stroke:#2e7d32
    classDef output fill:#fce4ec,stroke:#c2185b
    
    class USER_INPUT,USER_ACTION input
    class VALIDATION,BUSINESS_LOGIC,DATA_TRANSFORM process
    class WRITE_DB,WRITE_CACHE storage
    class READ_CACHE,READ_DB,GRAPH_QUERY retrieval
    class RESPONSE,UI_RENDER output
```

---

## 4. 온도 계산 시퀀스 다이어그램

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend
    participant BE as Backend
    participant Cache as Redis
    participant DB as DB
    
    User->>FE: 매물 조회
    FE->>BE: GET /api/listings/{id}
    
    BE->>Cache: 캐시 확인
    
    alt 캐시 있음
        Cache-->>BE: 온도 반환
    else 캐시 없음
        BE->>DB: 매물 정보 조회
        DB-->>BE: 매물 데이터
        
        Note over BE: 5가지 온도 병렬 계산<br/>교통 • 공원 • 편의시설 • 안전 • 허위매물
        BE->>BE: 온도 계산 완료
        
        BE->>Cache: 캐싱 (1시간)
    end
    
    BE-->>FE: 매물 + 온도
    FE-->>User: 결과 표시
```

---

## 5. 추천 시스템 시퀀스 다이어그램

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend
    participant BE as Backend
    participant Reco as Reco Service
    participant Cache as Redis
    participant DB as DB
    
    User->>FE: 추천 요청
    FE->>BE: GET /api/recommend/
    
    BE->>Cache: 캐시 확인
    
    alt 캐시 있음
        Cache-->>BE: 추천 결과
    else 캐시 없음
        BE->>DB: 사용자 프로필 조회
        DB-->>BE: 선호도, 이력
        
        BE->>Reco: 추천 요청
        Reco->>DB: 행동 로그 조회
        DB-->>Reco: 사용자 로그
        
        Reco->>Reco: 협업 필터링
        Reco->>Reco: 콘텐츠 기반 필터링
        Reco->>Reco: ML 모델 추론
        Reco->>Reco: 순위 계산
        
        Reco-->>BE: 추천 매물 (Top 20)
        BE->>Cache: 캐싱 (30분)
    end
    
    BE-->>FE: 추천 매물
    FE-->>User: 결과 표시
```

---

## 6. RAG 챗봇 시퀀스 다이어그램

```mermaid
sequenceDiagram
    actor User as 👤 사용자
    participant FE as Frontend
    participant RAG as RAG Service
    participant DB as PostgreSQL
    participant Graph as Neo4j
    participant LLM as OpenAI GPT
    
    User->>FE: 챗봇 질문 입력<br/>"강남역 근처 원룸 찾아줘"
    FE->>RAG: POST /rag/query<br/>{question, user_id}
    
    RAG->>RAG: 질문 분석<br/>(의도 파악, 엔티티 추출)
    
    Note over RAG: 1️⃣ 검색 단계
    RAG->>DB: 벡터 유사도 검색<br/>(pgvector)
    DB-->>RAG: 유사 매물 목록
    
    RAG->>Graph: 그래프 쿼리<br/>MATCH (l:Listing)-[:NEAR]->(f:Facility)
    Graph-->>RAG: 관계 데이터<br/>(매물-시설 거리)
    
    RAG->>DB: 매물 상세 정보 조회
    DB-->>RAG: 매물 데이터 + 온도
    
    Note over RAG: 2️⃣ 컨텍스트 구성
    RAG->>RAG: 검색 결과 정리<br/>(Top 5 매물)
    RAG->>RAG: 프롬프트 생성<br/>(질문 + 컨텍스트)
    
    Note over RAG: 3️⃣ LLM 호출
    RAG->>LLM: POST /v1/chat/completions<br/>{prompt, context}
    LLM-->>RAG: 생성된 답변
    
    Note over RAG: 4️⃣ 후처리
    RAG->>RAG: 답변 검증<br/>(환각 체크)
    RAG->>RAG: 답변 포맷팅<br/>(마크다운, 링크 추가)
    
    RAG->>DB: 대화 이력 저장
    DB-->>RAG: 저장 완료
    
    RAG-->>FE: 답변 + 추천 매물 카드
    FE->>FE: 답변 렌더링
    FE-->>User: 챗봇 응답 표시
    
    alt 추가 질문
        User->>FE: "가격대는 어떻게 돼?"
        FE->>RAG: POST /rag/query<br/>{question, conversation_id}
        RAG->>DB: 이전 대화 이력 조회
        DB-->>RAG: 컨텍스트 복원
        RAG->>LLM: 연속 대화 처리
        LLM-->>RAG: 답변
        RAG-->>FE: 응답
        FE-->>User: 답변 표시
    end
```

---

## 7. ML 모델 동작 흐름

```mermaid
flowchart LR
    subgraph TRAINING["학습 단계 Offline"]
        direction LR
        DATA_COLLECT[데이터<br/>수집] --> DATA_PREP[데이터<br/>전처리]
        DATA_PREP --> FEATURE_ENG[피처<br/>생성]
        FEATURE_ENG --> MODEL_TRAIN[모델<br/>학습]
        MODEL_TRAIN --> MODEL_EVAL[모델<br/>평가]
        MODEL_EVAL -->|성능 OK| MODEL_SAVE[모델<br/>저장]
        MODEL_EVAL -->|성능 부족| MODEL_TRAIN
    end
    
    subgraph INFERENCE["추론 단계 Online"]
        direction LR
        REQUEST[추론<br/>요청] --> LOAD_MODEL[모델<br/>로드]
        LOAD_MODEL --> LOAD_DATA[데이터<br/>로드]
        LOAD_DATA --> PREPROCESS[전처리]
        PREPROCESS --> PREDICT[예측<br/>수행]
        PREDICT --> POSTPROCESS[후처리]
        POSTPROCESS --> RESPONSE[응답<br/>반환]
    end
    
    subgraph MONITORING["모니터링"]
        direction LR
        PERFORMANCE[성능<br/>모니터링] --> DRIFT[드리프트<br/>감지]
        DRIFT --> RETRAIN[재학습<br/>트리거]
    end
    
    MODEL_SAVE -.-> LOAD_MODEL
    RESPONSE -.-> PERFORMANCE
    RETRAIN -.-> DATA_COLLECT
    
    classDef training fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef inference fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef monitoring fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class DATA_COLLECT,DATA_PREP,FEATURE_ENG,MODEL_TRAIN,MODEL_EVAL,MODEL_SAVE training
    class REQUEST,LOAD_MODEL,LOAD_DATA,PREPROCESS,PREDICT,POSTPROCESS,RESPONSE inference
    class PERFORMANCE,DRIFT,RETRAIN monitoring
```

---

## 8. LangGraph RAG 구조

```mermaid
flowchart TD
    START([사용자 질문])
    
    START --> CLASSIFY[classify_node<br/>질문 분류]
    
    CLASSIFY --> RISK[risk_analysis_node<br/>매물 전세사기 위험도 분석]
    CLASSIFY --> LANDFIND[landfind_node<br/>사용자가 찾으려는 매물 추출]
    CLASSIFY --> PREPARSER[preparser_node<br/>소프트 필터 추출]
    CLASSIFY --> INFO[info_node<br/>부동산 일반 정보]
    CLASSIFY --> FAQ[faq_node<br/>서비스 운영 정보]
    
    RISK --> GEN
    
    LANDFIND --> ORCHESTRATOR
    PREPARSER --> ORCHESTRATOR
    
    INFO --> GEN
    FAQ --> GEN
    
    subgraph ORCHESTRATOR["agent_orchestrator (GraphDB + RDB 검색)"]
        NEO4J[neo4jSearch_node<br/>매물·거리·관계 기반 탐색]
        SQL[SQL_node<br/>RDB: 매물 상세 조회]
    end
    
    ORCHESTRATOR --> AGENT_TRUST[agent_trust<br/>중개사 신뢰도 분석]
    ORCHESTRATOR --> AGENT_PRICE[agent_price<br/>매물 가격 분석]
    
    AGENT_TRUST --> GEN
    AGENT_PRICE --> GEN
    
    GEN[Gen_node<br/>LLM 응답 생성]
    
    GEN --> END([END])
    
    classDef input fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef classify fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef extract fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef info fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef analysis fill:#ffe0f0,stroke:#c2185b,stroke-width:2px
    classDef search fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef generate fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef invisible fill:none,stroke:none
    
    class START input
    class CLASSIFY classify
    class LANDFIND,PREPARSER extract
    class INFO,FAQ info
    class RISK,AGENT_TRUST,AGENT_PRICE analysis
    class NEO4J,SQL search
    class GEN generate
    class END output
```

### LangGraph 노드 설명

| 노드 | 역할 | 설명 |
|------|------|------|
| **classify_node** | 질문 분류 | 사용자 질문의 의도를 파악하여 적절한 노드로 라우팅 |
| **risk_analysis_node** | 전세사기 위험도 분석 | 매물의 전세사기 위험도 분석 |
| **landfind_node** | 매물 추출 | 사용자가 찾으려는 매물 정보 추출 |
| **preparser_node** | 소프트 필터 추출 | 질문에서 주관적 조건 추출 (깨끗한, 조용한, 밝은 등)<br/>예: "강남역 근처 깨끗한 방" → 소프트 필터: 깨끗함 |
| **info_node** | 부동산 정보 | 부동산 관련 일반 정보 제공 |
| **faq_node** | FAQ | 서비스 운영 관련 자주 묻는 질문 처리 |
| **agent_trust** | 신뢰도 분석 | 중개사 신뢰도 분석 |
| **agent_price** | 가격 분석 | 매물 가격 적정성 분석 |
| **agent_orchestrator** | 검색 오케스트레이터 | GraphDB와 RDB를 병렬로 검색 조율 |
| **neo4jSearch_node** | 그래프 검색 | Neo4j에서 매물-거리-관계 기반 탐색 |
| **SQL_node** | RDB 검색 | PostgreSQL에서 매물 상세 정보 조회 |
| **Gen_node** | LLM 응답 생성 | LLM을 호출하여 최종 답변 생성 (위험도 분석, 가격 적정성, 추천 매물 등) |

---

## 9. 전체 데이터 파이프라인

```mermaid
flowchart LR
    subgraph SOURCE["데이터 소스"]
        CRAWL[크롤링]
        OPEN_DATA[공공 데이터]
        USER_DATA[사용자 데이터]
    end
    
    subgraph ETL["ETL 처리"]
        EXTRACT[추출]
        TRANSFORM[변환]
        LOAD[적재]
    end
    
    subgraph STORAGE["저장소"]
        PG[(PostgreSQL)]
        NEO[(Neo4j)]
        S3[(S3)]
    end
    
    subgraph ANALYTICS["분석"]
        JUPYTER[Jupyter]
        ML_TRAIN[ML 학습]
        REPORT[리포트]
    end
    
    subgraph APPLICATION["애플리케이션"]
        API[REST API]
        RAG_APP[RAG 챗봇]
        RECO_APP[추천 시스템]
    end
    
    CRAWL --> EXTRACT
    OPEN_DATA --> EXTRACT
    USER_DATA --> EXTRACT
    
    EXTRACT --> TRANSFORM
    TRANSFORM --> LOAD
    
    LOAD --> PG
    LOAD --> NEO
    LOAD --> S3
    
    PG --> JUPYTER
    NEO --> JUPYTER
    S3 --> JUPYTER
    
    JUPYTER --> ML_TRAIN
    JUPYTER --> REPORT
    
    PG --> API
    PG --> RAG_APP
    PG --> RECO_APP
    
    NEO --> RAG_APP
    
    ML_TRAIN --> RECO_APP
    
    classDef source fill:#e8f5e9,stroke:#2e7d32
    classDef etl fill:#fff3e0,stroke:#e65100
    classDef storage fill:#e3f2fd,stroke:#1565c0
    classDef analytics fill:#f3e5f5,stroke:#6a1b9a
    classDef app fill:#fce4ec,stroke:#c2185b
    
    class CRAWL,OPEN_DATA,USER_DATA source
    class EXTRACT,TRANSFORM,LOAD etl
    class PG,NEO,S3 storage
    class JUPYTER,ML_TRAIN,REPORT analytics
    class API,RAG_APP,RECO_APP app
```

---

## 📊 다이어그램 요약

| 다이어그램 | 목적 | 주요 내용 |
|-----------|------|-----------|
| **전체 시스템 아키텍처** | 시스템 전체 구조 | 계층별 컴포넌트 및 연결 관계 |
| **Layered Architecture** | 계층형 구조 | Presentation → Application → Domain → Infrastructure → Data |
| **데이터 흐름도** | 데이터 처리 과정 | 입력 → 처리 → 저장 → 조회 → 출력 |
| **온도 계산 시퀀스** | 온도 계산 흐름 | 5가지 온도 병렬 계산 및 캐싱 |
| **추천 시스템 시퀀스** | 추천 알고리즘 | 협업 필터링 + 콘텐츠 기반 + ML 모델 |
| **RAG 챗봇 시퀀스** | 챗봇 동작 원리 | 검색 → 컨텍스트 구성 → LLM 호출 → 답변 생성 |
| **ML 모델 동작** | 모델 학습/추론 | 학습 → 저장 → 로드 → 추론 → 모니터링 |
| **LangGraph RAG 구조** | RAG 그래프 구조 | 질문 분류 → 병렬 검색 → 답변 생성 |
| **데이터 파이프라인** | 데이터 흐름 전체 | 수집 → ETL → 저장 → 분석 → 애플리케이션 |
