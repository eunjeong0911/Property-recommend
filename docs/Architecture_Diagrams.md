# 🏗️ 전체 시스템 아키텍처 다이어그램

## 1. 전체 시스템 아키텍처 (서버 시작 → 사용자 응답)

```mermaid
flowchart TB
    subgraph STORAGE["💾 Storage Layer"]
        POSTGRES[(PostgreSQL<br/>Port 5432)]
        NEO4J[(Neo4j<br/>Port 7474, 7687)]
        REDIS[(Redis<br/>Port 6379)]
    end
    
    subgraph BACKEND["⚙️ Backend Layer"]
        DJANGO[Django REST API<br/>Port 8000<br/>+ RAG Module<br/>+ Reco Module]
    end
    
    subgraph FRONTEND["🖥️ Frontend Layer"]
        NEXTJS[Next.js 14<br/>Port 3000]
    end
    
    subgraph CLIENT["👥 Client Layer"]
        USER[사용자]
    end
    
    subgraph EXTERNAL["🌐 External APIs"]
        OPENAI[OpenAI]
        KAKAO[Kakao Map]
        GOOGLE[Google OAuth]
    end
    
    POSTGRES -.->|DB 준비 완료| DJANGO
    NEO4J -.->|DB 준비 완료| DJANGO
    REDIS -.->|DB 준비 완료| DJANGO
    
    DJANGO -->|서버 시작| NEXTJS
    NEXTJS -->|페이지 준비| USER
    
    USER -->|요청| NEXTJS
    NEXTJS -->|API 호출| DJANGO
    NEXTJS -.->|지도 표시| KAKAO
    
    DJANGO <-->|쿼리/응답| POSTGRES
    DJANGO <-->|그래프 쿼리| NEO4J
    DJANGO <-->|캐싱| REDIS
    DJANGO -.->|LLM 호출| OPENAI
    DJANGO -.->|OAuth| GOOGLE
    
    DJANGO -->|응답| NEXTJS
    NEXTJS -->|렌더링| USER
    
    classDef storage fill:#336791,stroke:#333,color:#fff,stroke-width:3px
    classDef backend fill:#092e20,stroke:#333,color:#fff,stroke-width:3px
    classDef frontend fill:#61dafb,stroke:#333,stroke-width:3px
    classDef client fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef external fill:#ff6b6b,stroke:#333,color:#fff,stroke-width:2px
    
    class POSTGRES,NEO4J,REDIS storage
    class DJANGO backend
    class NEXTJS frontend
    class USER client
    class OPENAI,KAKAO,GOOGLE external
```

---

## 2. 온도 계산 시퀀스 다이어그램

### 2-1. 교통 온도 계산 (30~43°C)

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend
    participant BE as Backend
    participant DB as PostgreSQL
    participant Neo4j as Neo4j
    
    User->>FE: 매물 조회
    FE->>BE: GET /api/listings/{id}
    
    BE->>DB: 매물 위치 조회
    DB-->>BE: 위도, 경도
    
    BE->>Neo4j: 지하철역 거리 쿼리<br/>MATCH (l:Listing)-[:NEAR]->(s:Subway)
    Neo4j-->>BE: 가까운 역 3개 + 거리
    
    BE->>DB: 지하철역 정보 조회<br/>(출퇴근 승하차, 일일 승하차)
    DB-->>BE: 역별 이용 통계
    
    Note over BE: 지하철 점수 계산<br/>1. 거리 점수 (0~250m: 1.0, 500m~: 지수감소)<br/>2. 역 중요도 (출퇴근비율 40% + 역규모 20%)<br/>3. 가까운 3개역 거리 가중 평균
    
    BE->>Neo4j: 버스정류장 거리 쿼리<br/>MATCH (l:Listing)-[:NEAR]->(b:BusStop)
    Neo4j-->>BE: 가장 가까운 정류장 + 300m 내 개수
    
    Note over BE: 버스 점수 계산<br/>1. 거리 점수 (exp(-거리/300)) × 70%<br/>2. 밀도 점수 (min(개수/8, 1.0)) × 30%
    
    Note over BE: 교통 점수 통합<br/>지하철 55% + 버스 45%<br/>→ 정규화 (0~1)
    
    BE->>BE: 온도 변환<br/>30 + (교통점수 × 13)
    
    BE-->>FE: 매물 + 교통온도 (30~43°C)
    FE-->>User: 결과 표시
```

### 2-2. 공원 온도 계산 (30~43°C)

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend
    participant BE as Backend
    participant DB as PostgreSQL
    participant Neo4j as Neo4j
    
    User->>FE: 매물 조회
    FE->>BE: GET /api/listings/{id}
    
    BE->>DB: 매물 위치 조회
    DB-->>BE: 위도, 경도
    
    BE->>Neo4j: 공원 거리 쿼리<br/>MATCH (l:Listing)-[:NEAR]->(p:Park)<br/>WHERE distance < 800m
    Neo4j-->>BE: 반경 800m 내 공원 목록 + 거리
    
    BE->>DB: 공원 상세 정보 조회
    DB-->>BE: 면적, 시설(5종류), 유형
    
    Note over BE: 각 공원 품질 점수<br/>1. 크기 점수 (Min-Max 정규화) × 40%<br/>2. 시설 점수 (5종류/5) × 40%<br/>3. 유형 점수 (근린1.0/어린이0.8) × 20%
    
    Note over BE: 거리 점수 계산<br/>exp(-거리/400)
    
    Note over BE: 매물 공원 점수<br/>각 공원 (품질×거리) 거리 가중 평균<br/>가중치 = 1/(1+거리/300)
    
    BE->>BE: 정규화 후 온도 변환<br/>30 + (공원점수 × 13)
    
    BE-->>FE: 매물 + 공원온도 (30~43°C)
    FE-->>User: 결과 표시
```

### 2-3. 편의시설 온도 계산 (30~43°C)

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend
    participant BE as Backend
    participant DB as PostgreSQL
    participant Neo4j as Neo4j
    
    User->>FE: 매물 조회
    FE->>BE: GET /api/listings/{id}
    
    BE->>DB: 매물 정보 조회
    DB-->>BE: 위도, 경도, 옵션<br/>(세탁기, 냉장고, 싱크대, 가스레인지)
    
    Note over BE: 필요도(Need) 계산<br/>편의시설: 0.7 + 세탁기없음(0.1) + 부실주방(0.1)<br/>병원/약국: 0.7 (고정)
    
    BE->>Neo4j: 편의시설 거리 쿼리<br/>MATCH (l:Listing)-[:NEAR]->(c:ConvenienceStore)
    Neo4j-->>BE: 가장 가까운 편의점 + 500m 내 개수
    
    BE->>Neo4j: 병원 거리 쿼리<br/>MATCH (l:Listing)-[:NEAR]->(h:Hospital)
    Neo4j-->>BE: 가장 가까운 병원 + 800m 내 개수
    
    BE->>Neo4j: 약국 거리 쿼리<br/>MATCH (l:Listing)-[:NEAR]->(p:Pharmacy)
    Neo4j-->>BE: 가장 가까운 약국 + 800m 내 개수
    
    Note over BE: 각 유형별 접근성(Access)<br/>거리점수(60%) + 밀도점수(40%)<br/>편의: d_max=800m, n_sat=5<br/>병원/약국: d_max=1200m, n_sat=2
    
    Note over BE: 유형별 점수 = Need × Access<br/>최종 = 편의50% + 병원25% + 약국25%
    
    BE->>BE: 온도 변환<br/>30 + (편의점수 × 13)
    
    BE-->>FE: 매물 + 편의시설온도 (30~43°C)
    FE-->>User: 결과 표시
```

### 2-4. 안전 온도 계산 (0~100점)

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend
    participant BE as Backend
    participant DB as PostgreSQL
    participant Neo4j as Neo4j
    
    User->>FE: 매물 조회
    FE->>BE: GET /api/listings/{id}
    
    BE->>DB: 매물 정보 조회
    DB-->>BE: 주소, 구 정보
    
    BE->>DB: 구별 범죄 통계 조회<br/>(5대 범죄: 살인/강도/강간/절도/폭력)
    DB-->>BE: 2024년 범죄 발생 건수, 검거율
    
    BE->>Neo4j: 안전 인프라 쿼리<br/>MATCH (l:Listing)-[:IN]->(d:District)
    Neo4j-->>BE: CCTV, 지구대/파출소, 소방서, 안전비상벨 개수
    
    Note over BE: 안전 온도 계산<br/>1. 범죄 점수 (역수, Min-Max) × 30%<br/>2. CCTV 점수 × 30%<br/>3. 지구대/파출소 점수 × 20%<br/>4. 소방서 점수 × 10%<br/>5. 안전비상벨 점수 × 10%
    
    BE->>BE: 가중 평균 (0~100점)<br/>등급: 매우안전(66~100)<br/>안전(33~66), 주의(0~33)
    
    BE-->>FE: 매물 + 안전온도 (0~100점)
    FE-->>User: 결과 표시
```

### 2-5. 허위매물 온도 계산 (0~100점)

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend
    participant BE as Backend
    participant DB as PostgreSQL
    
    User->>FE: 매물 조회
    FE->>BE: GET /api/listings/{id}
    
    BE->>DB: 매물 정보 조회
    DB-->>BE: 가격, 면적, 중개사 정보, 구 정보
    
    BE->>DB: 중개사 신뢰도 조회
    DB-->>BE: 행정처분 이력, 영업 상태
    
    BE->>DB: 구별 부동산 통계 조회
    DB-->>BE: 중개업소 수, 행정처분 건수, 경매 건수
    
    Note over BE: 행정처분 점수<br/>등록취소(5점) + 업무정지(3점) + 적발(1점)<br/>→ 행정처분 비율 = 점수 / 중개업소 수
    
    Note over BE: 문제업소 비율<br/>(휴업 + 업무정지 + 휴업연장) / 전체 × 100
    
    Note over BE: 허위매물 온도 계산<br/>1. 행정처분 비율 × 40%<br/>2. 경매건수 (Min-Max) × 30%<br/>3. 문제업소 비율 × 30%
    
    BE->>BE: 가중 평균 (0~100점)<br/>등급: 고위험(66~100)<br/>주의(33~66), 안전(0~33)
    
    BE-->>FE: 매물 + 허위매물온도 (0~100점)
    FE-->>User: 결과 표시
```

---

## 3. ML 모델 동작 흐름

```mermaid
flowchart LR
    subgraph TRAINING["학습 단계"]
        direction LR
        DATA_COLLECT[데이터<br/>수집] --> DATA_PREP[데이터<br/>전처리]
        DATA_PREP --> FEATURE_ENG[피처<br/>생성]
        FEATURE_ENG --> MODEL_TRAIN[모델<br/>학습]
        MODEL_TRAIN --> MODEL_EVAL[모델<br/>평가]
        MODEL_EVAL -->|성능 OK| MODEL_SAVE[모델<br/>저장]
        MODEL_EVAL -->|성능 부족| MODEL_TRAIN
    end
    
    subgraph INFERENCE["추론 단계"]
        direction LR
        REQUEST[추론<br/>요청] --> LOAD_MODEL[모델<br/>로드]
        LOAD_MODEL --> LOAD_DATA[데이터<br/>로드]
        LOAD_DATA --> PREPROCESS[전처리<br/>피처 생성]
        PREPROCESS --> PREDICT[예측<br/>수행]
        PREDICT --> RESPONSE[응답<br/>반환]
    end
    
    MODEL_SAVE -.-> LOAD_MODEL
    
    classDef training fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef inference fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    
    class DATA_COLLECT,DATA_PREP,FEATURE_ENG,MODEL_TRAIN,MODEL_EVAL,MODEL_SAVE training
    class REQUEST,LOAD_MODEL,LOAD_DATA,PREPROCESS,PREDICT,RESPONSE inference
```

---

## 4. LangGraph RAG 구조

```mermaid
flowchart TD
    START([사용자 질문])
    
    START --> CLASSIFY[classify_node<br/>질문 분류]
    
    CLASSIFY --> RISK[risk_analysis_node<br/>전세사기 위험도 분석<br/>예: 이 매물 안전한가요?]
    CLASSIFY --> LANDFIND[landfind_node<br/>매물 찾기<br/>예: 강남역 근처 원룸 찾아줘]
    CLASSIFY --> PREPARSER[preparser_node<br/>소프트 필터 추출<br/>예: 조용하고 깨끗한 방]
    CLASSIFY --> INFO[info_node<br/>부동산 일반 정보<br/>예: 전세와 월세 차이는?]
    CLASSIFY --> FAQ[faq_node<br/>서비스 운영 정보<br/>예: 회원가입은 어떻게 하나요?]
    
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


