# 매물 데이터 통계

## 전체 현황

**총 매물 수: 9,914개**

## 거래유형별 분포

| 거래유형 | 매물 수 | 비율 |
|---------|--------|------|
| 월세 | 6,351개 | 64.1% |
| 전세 | 1,965개 | 19.8% |
| 단기임대 | 1,014개 | 10.2% |
| 매매 | 582개 | 5.9% |
| 미분류 | 2개 | 0.02% |

### 단기임대 상세 분포 (Top 10)

| 단기임대 유형 | 매물 수 |
|-------------|--------|
| 100만원/100만원 | 45개 |
| 100만원/70만원 | 37개 |
| 100만원/80만원 | 34개 |
| 90만원/90만원 | 26개 |
| 110만원/110만원 | 25개 |
| 70만원/70만원 | 25개 |
| 100만원/75만원 | 24개 |
| 기타 | 798개 |

**총 단기임대: 1,014개**

## 건물유형별 분포

```sql
SELECT building_type, COUNT(*) as count 
FROM land 
GROUP BY building_type 
ORDER BY count DESC;
```

| 건물유형 | 매물 수 |
|---------|--------|
| 원투룸 | 약 5,000개 |
| 빌라주택 | 약 2,500개 |
| 오피스텔 | 약 1,500개 |
| 아파트 | 약 900개 |

## 지역별 분포 (서울 구)

### 매물이 많은 구 Top 10

```sql
SELECT SPLIT_PART(address, ' ', 2) as district, COUNT(*) as count
FROM land 
WHERE address LIKE '서울%'
GROUP BY district 
ORDER BY count DESC 
LIMIT 10;
```

예상 결과:
- 강남구
- 송파구
- 서초구
- 강서구
- 노원구
- 등등...

## 필터 조합별 매물 수

### 강남구 매물
```sql
SELECT deal_type, COUNT(*) 
FROM land 
WHERE address LIKE '%강남구%' 
GROUP BY deal_type;
```

예상 결과:
- 월세: 약 400개
- 전세: 약 150개
- 단기임대: 약 80개
- 매매: 약 50개

### 아파트 매물
```sql
SELECT deal_type, COUNT(*) 
FROM land 
WHERE building_type = '아파트' 
GROUP BY deal_type;
```

예상 결과:
- 전세: 약 500개
- 월세: 약 300개
- 매매: 약 100개

## 가격 분포

### 전세 가격대
```sql
-- trade_info에서 가격 추출 필요
-- 예상: 1억~3억 사이가 가장 많음
```

### 월세 가격대
```sql
-- trade_info에서 가격 추출 필요
-- 보증금: 1,000만원~5,000만원
-- 월세: 50만원~150만원
```

## 데이터 품질

### 완전한 데이터
- 거래유형 있음: 9,912개 (99.98%)
- 거래유형 없음: 2개 (0.02%)

### 미분류 매물 (land_id)
- 1900
- 8759

이 2개 매물은 deal_type이 NULL이므로 필터링에서 제외됩니다.

## 필터 옵션 업데이트

### 거래유형 필터
```typescript
const TRANSACTION_OPTIONS = ['매매', '전세', '월세', '단기임대'];
```

### 단기임대 필터링 로직
```python
if deal_type == '단기임대':
    # deal_type에 "단기임대"가 포함된 모든 매물
    queryset = queryset.filter(deal_type__icontains='단기임대')
```

이렇게 하면 "단기임대 100만원/100만원", "단기임대 70만원/70만원" 등 모든 단기임대 매물이 필터링됩니다.

## 데이터 검증 쿼리

```sql
-- 전체 매물 수
SELECT COUNT(*) FROM land;
-- 결과: 9,914

-- 거래유형별 합계
SELECT 
    SUM(CASE WHEN deal_type = '월세' THEN 1 ELSE 0 END) as 월세,
    SUM(CASE WHEN deal_type = '전세' THEN 1 ELSE 0 END) as 전세,
    SUM(CASE WHEN deal_type = '매매' THEN 1 ELSE 0 END) as 매매,
    SUM(CASE WHEN deal_type LIKE '단기임대%' THEN 1 ELSE 0 END) as 단기임대,
    SUM(CASE WHEN deal_type IS NULL OR deal_type = '' THEN 1 ELSE 0 END) as 미분류
FROM land;
-- 결과: 6351 + 1965 + 582 + 1014 + 2 = 9,914 ✓

-- 중복 매물 확인
SELECT land_num, COUNT(*) 
FROM land 
GROUP BY land_num 
HAVING COUNT(*) > 1;
-- 결과: 중복 없음 (land_num은 UNIQUE)
```

## 추천 필터 조합

### 인기 조합 1: 강남구 + 전세 + 아파트
```
예상 매물 수: 약 50개
타겟: 강남구에서 전세로 아파트를 찾는 사용자
```

### 인기 조합 2: 서초구 + 월세 + 원투룸
```
예상 매물 수: 약 200개
타겟: 서초구에서 월세로 원투룸을 찾는 사용자
```

### 인기 조합 3: 송파구 + 전세 + 빌라주택
```
예상 매물 수: 약 100개
타겟: 송파구에서 전세로 빌라를 찾는 사용자
```

## 데이터 업데이트 이력

- 최초 임포트: 9,914개
- 마지막 업데이트: 2024-12-08
- 데이터 소스: 피터팬 매물 데이터

## 향후 개선 사항

1. ✅ 단기임대 필터 추가 완료
2. ⏳ 미분류 2개 매물 거래유형 수동 입력
3. ⏳ 가격대별 필터 추가
4. ⏳ 면적별 필터 추가
5. ⏳ 정기적인 데이터 업데이트 자동화
