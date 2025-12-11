# 온도 계산 시퀀스 다이어그램

## 1. 편의시설온도 🏪

```mermaid
sequenceDiagram
    actor User
    participant System
    participant Analyzer
    participant POI
    
    User->>System: 매물 정보 입력
    System->>Analyzer: 매물 옵션 확인
    Analyzer->>Analyzer: 필요도 계산
    Analyzer->>POI: 주변 POI 조회
    POI->>POI: 접근성 계산
    POI-->>Analyzer: 접근성 점수
    Analyzer->>Analyzer: 최종 온도 계산
    Analyzer-->>User: 편의시설온도 반환
```


## 2. 허위매물온도 ⚠️

```mermaid
sequenceDiagram
    actor User
    participant System
    participant DataCollector
    participant Calculator
    
    User->>System: 지역 선택
    System->>DataCollector: 구별 데이터 수집
    DataCollector->>DataCollector: 중개업소 분석
    DataCollector->>DataCollector: 행정처분 분석
    DataCollector->>DataCollector: 경매 분석
    DataCollector->>Calculator: 3가지 지표 전달
    Calculator->>Calculator: 가중 평균 계산
    Calculator-->>User: 허위매물온도 반환
```

## 3. 공원온도 🌳

```mermaid
sequenceDiagram
    actor User
    participant System
    participant ParkDB
    participant Calculator
    
    User->>System: 매물 위치 입력
    System->>ParkDB: 주변 공원 조회
    ParkDB->>ParkDB: 공원 품질 평가
    ParkDB->>Calculator: 공원 정보 전달
    Calculator->>Calculator: 거리 가중 평균
    Calculator->>Calculator: 온도 변환
    Calculator-->>User: 공원온도 반환
```

## 4. 안전온도 🛡️

```mermaid
sequenceDiagram
    actor User
    participant System
    participant SafetyDB
    participant Calculator
    
    User->>System: 지역 선택
    System->>SafetyDB: 안전 데이터 수집
    SafetyDB->>SafetyDB: 범죄 분석
    SafetyDB->>SafetyDB: CCTV 분석
    SafetyDB->>SafetyDB: 경찰 소방 분석
    SafetyDB->>Calculator: 5가지 지표 전달
    Calculator->>Calculator: 가중 평균 계산
    Calculator-->>User: 안전온도 반환
```

## 5. 교통온도 🚇

```mermaid
sequenceDiagram
    actor User
    participant System
    participant Transit
    participant Calculator
    
    User->>System: 매물 위치 입력
    System->>Transit: 주변 교통 조회
    Transit->>Transit: 지하철 점수 계산
    Transit->>Transit: 버스 점수 계산
    Transit->>Calculator: 2가지 점수 전달
    Calculator->>Calculator: 통합 점수 계산
    Calculator-->>User: 교통온도 반환
```

## 📊 요약 비교표

| 온도 | 입력 | 주요 계산 | 출력 |
|------|------|----------|------|
| **편의시설** | 매물 정보 | 필요도 × 접근성 | 30-43°C |
| **허위매물** | 지역 | 중개업소 + 행정처분 + 경매 | 30-43°C |
| **공원** | 매물 위치 | 공원 품질 × 거리 | 30-43°C |
| **안전** | 지역 | 범죄 + 인프라 | 30-43°C |
| **교통** | 매물 위치 | 지하철 + 버스 | 30-43°C |
