# 온도 계산 시퀀스 다이어그램

## 1. 편의시설온도 🏪

```mermaid
sequenceDiagram
    actor User
    participant System
    participant NeedCalc
    participant POI
    participant AccessCalc
    
    User->>System: 매물 정보 입력
    System->>NeedCalc: 매물 옵션 분석
    NeedCalc->>NeedCalc: 필요도 계산<br/>(세탁기/주방 옵션 체크)
    
    System->>POI: 주변 POI 조회
    POI->>POI: 편의시설/병원/약국 검색
    POI->>AccessCalc: POI 목록 전달
    
    AccessCalc->>AccessCalc: 거리 점수 (60%)
    AccessCalc->>AccessCalc: 밀도 점수 (40%)
    AccessCalc-->>System: 접근성 점수
    
    System->>System: 유형별 점수 = 필요도 × 접근성
    System->>System: 총점 = 편의시설 50%<br/>+ 병원 25% + 약국 25%
    System->>System: 온도 변환 (30 + 13×점수)
    System-->>User: 편의시설온도 (30-43°C)
```


## 2. 허위매물온도 ⚠️

```mermaid
sequenceDiagram
    actor User
    participant System
    participant DataCollector
    participant Calculator
    
    User->>System: 지역(구) 선택
    System->>DataCollector: 구별 데이터 수집
    
    DataCollector->>DataCollector: 중개업소 분석<br/>(문제업소 비율)
    DataCollector->>DataCollector: 행정처분 분석<br/>(취소 5점, 정지 3점, 적발 1점)
    DataCollector->>DataCollector: 경매 건수 집계
    
    DataCollector->>Calculator: 3가지 지표 전달
    Calculator->>Calculator: Min-Max 정규화 (0-100)
    Calculator->>Calculator: 가중 평균<br/>(행정처분 40% + 경매 30%<br/>+ 문제업소 30%)
    Calculator-->>User: 허위매물온도 (0-100점)
```

## 3. 공원온도 🌳

```mermaid
sequenceDiagram
    actor User
    participant System
    participant ParkDB
    participant QualityCalc
    participant DistanceCalc
    
    User->>System: 매물 위치 입력
    System->>ParkDB: 주변 공원 조회 (800m)
    
    ParkDB->>QualityCalc: 공원 정보 전달
    QualityCalc->>QualityCalc: 크기 점수 (40%)
    QualityCalc->>QualityCalc: 시설 점수 (40%)
    QualityCalc->>QualityCalc: 유형 점수 (20%)
    QualityCalc-->>System: 공원 품질 점수
    
    System->>DistanceCalc: 거리 계산
    DistanceCalc->>DistanceCalc: 거리 점수 (exp(-d/400))
    DistanceCalc->>DistanceCalc: 거리 가중 평균
    DistanceCalc->>DistanceCalc: Min-Max 정규화
    DistanceCalc->>DistanceCalc: 온도 변환 (30 + 13×점수)
    DistanceCalc-->>User: 공원온도 (30-43°C)
```

## 4. 안전온도 🛡️

```mermaid
sequenceDiagram
    actor User
    participant System
    participant SafetyDB
    participant Calculator
    
    User->>System: 지역(구) 선택
    System->>SafetyDB: 안전 데이터 수집
    
    SafetyDB->>SafetyDB: 5대 범죄 집계<br/>(살인/강도/강간/절도/폭력)
    SafetyDB->>SafetyDB: CCTV 현황<br/>(생활방범/차량방범/어린이보호)
    SafetyDB->>SafetyDB: 지구대/파출소 개수
    SafetyDB->>SafetyDB: 소방서 개수
    SafetyDB->>SafetyDB: 안전비상벨 개수
    
    SafetyDB->>Calculator: 5가지 지표 전달
    Calculator->>Calculator: Min-Max 정규화 (0-100)
    Calculator->>Calculator: 범죄 점수 역수 처리
    Calculator->>Calculator: 가중 평균<br/>(범죄 30% + CCTV 30%<br/>+ 경찰 20% + 소방 10% + 비상벨 10%)
    Calculator-->>User: 안전온도 (0-100점)
```

## 5. 교통온도 🚇

```mermaid
sequenceDiagram
    actor User
    participant System
    participant SubwayService
    participant BusService
    participant Calculator
    
    User->>System: 매물 위치 입력
    
    System->>SubwayService: 주변 지하철역 조회
    SubwayService->>SubwayService: 가까운 역 3개 선택
    SubwayService->>SubwayService: 거리 점수 계산
    SubwayService->>SubwayService: 역 중요도 계산<br/>(출퇴근비율 + 역규모)
    SubwayService->>SubwayService: 가중 평균
    SubwayService-->>System: 지하철 점수
    
    System->>BusService: 주변 버스정류장 조회
    BusService->>BusService: 거리 점수 (70%)
    BusService->>BusService: 밀도 점수 (30%)
    BusService-->>System: 버스 점수
    
    System->>Calculator: 지하철/버스 점수 전달
    Calculator->>Calculator: Min-Max 정규화
    Calculator->>Calculator: 통합 (지하철 55% + 버스 45%)
    Calculator->>Calculator: 온도 변환 (30 + 13×점수)
    Calculator-->>User: 교통온도 (30-43°C)
```

## 📊 요약 비교표

| 온도 | 입력 | 주요 계산 | 출력 |
|------|------|----------|------|
| **편의시설** | 매물 정보 | 필요도 × 접근성 | 30-43°C |
| **허위매물** | 지역 | 중개업소 + 행정처분 + 경매 | 30-43°C |
| **공원** | 매물 위치 | 공원 품질 × 거리 | 30-43°C |
| **안전** | 지역 | 범죄 + 인프라 | 30-43°C |
| **교통** | 매물 위치 | 지하철 + 버스 | 30-43°C |
