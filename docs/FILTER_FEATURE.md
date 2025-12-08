# 매물 필터링 기능 구현 완료

## 수정 사항

### 1. LandListFilter 컴포넌트 (`apps/frontend/src/components/LandListFilter.tsx`)

#### 필터 옵션 업데이트 (DB 데이터 기준)

**지역 필터:**
- 변경 전: 전국 광역시/도 목록
- 변경 후: 서울 25개 구 목록
  ```
  강남구, 강동구, 강북구, 강서구, 관악구, 광진구, 구로구, 금천구,
  노원구, 도봉구, 동대문구, 동작구, 마포구, 서대문구, 서초구, 성동구,
  성북구, 송파구, 양천구, 영등포구, 용산구, 은평구, 종로구, 중구, 중랑구
  ```

**거래유형 필터:**
- 매매, 전세, 월세 (DB와 일치)

**건물유형 필터:**
- 변경 전: 아파트, 오피스텔, 빌라, 원룸, 투룸
- 변경 후: 아파트, 오피스텔, 빌라주택, 원투룸 (DB와 일치)

#### 검색 기능 추가
- 주소, 매물번호로 검색 가능
- 실시간 검색 (입력 시 즉시 필터링)
- 검색어 태그 표시 및 삭제 기능

### 2. 필터 파라미터 매핑

**프론트엔드 → 백엔드:**
```typescript
{
  region: '강남구'          → address: '강남구'
  transaction_type: '전세'  → deal_type: '전세'
  building_type: '아파트'   → building_type: '아파트'
  search: '서초동'          → search: '서초동'
}
```

**백엔드 필터링 (Django):**
```python
# apps/backend/apps/listings/views.py
filterset_fields = ['address', 'deal_type', 'building_type']
search_fields = ['land_num', 'address']
```

## 사용 방법

### 1. 지역 필터
```
서울 구 → 강남구 선택 → 강남구 매물만 표시
```

### 2. 거래유형 필터
```
거래유형 → 전세 선택 → 전세 매물만 표시
```

### 3. 건물유형 필터
```
건물유형 → 아파트 선택 → 아파트만 표시
```

### 4. 검색
```
검색창에 "서초동" 입력 → 주소에 "서초동"이 포함된 매물 표시
```

### 5. 복합 필터
```
강남구 + 전세 + 아파트 → 강남구의 전세 아파트만 표시
```

### 6. 초기화
```
초기화 버튼 → 모든 필터 해제
```

## 필터 동작 흐름

```
1. 사용자가 필터 선택
   ↓
2. LandListFilter에서 onFilterChange 콜백 호출
   ↓
3. MainPage에서 filterParams 상태 업데이트
   ↓
4. LandList 컴포넌트에 filterParams 전달
   ↓
5. fetchLands API 호출 (쿼리 파라미터 포함)
   ↓
6. Django 백엔드에서 필터링된 데이터 반환
   ↓
7. 필터링된 매물 목록 표시
```

## API 엔드포인트 예시

```
# 기본 목록
GET /api/listings/lands/

# 강남구 매물 (부분 일치)
GET /api/listings/lands/?address=강남구

# 전세 매물 (정확히 일치)
GET /api/listings/lands/?deal_type=전세

# 아파트 (정확히 일치)
GET /api/listings/lands/?building_type=아파트

# 복합 필터
GET /api/listings/lands/?address=강남구&deal_type=전세&building_type=아파트

# 검색 (매물번호, 주소)
GET /api/listings/lands/?search=서초동
```

## 필터링 테스트 결과

### 월세 필터링
```json
// GET /api/listings/lands/?deal_type=월세
[
  { "id": 9915, "price": "월세 2,000만원 / 50만원", "transaction_type": "월세" },
  { "id": 9914, "price": "월세 3,000만원 / 50만원", "transaction_type": "월세" },
  { "id": 9913, "price": "월세 5,000만원 / 65만원", "transaction_type": "월세" }
]
// ✅ 월세만 반환됨 (전세, 매매 제외)
```

### 전세 필터링
```json
// GET /api/listings/lands/?deal_type=전세
[
  { "id": 9890, "price": "전세 1억 5,000만원", "transaction_type": "전세" },
  { "id": 9889, "price": "전세 1억 5,000만원", "transaction_type": "전세" },
  { "id": 9886, "price": "전세 1억 8,500만원", "transaction_type": "전세" }
]
// ✅ 전세만 반환됨 (월세, 매매 제외)
```

### 복합 필터링 (전세 + 아파트)
```json
// GET /api/listings/lands/?deal_type=전세&building_type=아파트
[
  { "id": 4119, "price": "전세 2억", "transaction_type": "전세", "building_type": "아파트" },
  { "id": 4108, "price": "전세 9,520만원", "transaction_type": "전세", "building_type": "아파트" },
  { "id": 4099, "price": "전세 2억 2,000만원", "transaction_type": "전세", "building_type": "아파트" }
]
// ✅ 전세 아파트만 반환됨
```

### 복합 필터링 (강남구 + 월세)
```json
// GET /api/listings/lands/?address=강남구&deal_type=월세
// Total: 311개
[
  { "id": 9564, "price": "월세 1,000만원 / 40만원", "transaction_type": "월세", "address": "서울특별시 강남구 ..." },
  { "id": 9561, "price": "월세 3,000만원 / 100만원", "transaction_type": "월세", "address": "서울특별시 강남구 ..." },
  { "id": 9558, "price": "월세 5,000만원 / 71만원", "transaction_type": "월세", "address": "서울특별시 강남구 ..." }
]
// ✅ 강남구의 월세 매물만 반환됨
```

## 테스트 방법

### 1. 프론트엔드 실행
```powershell
cd apps\frontend
npm run dev
```

### 2. 브라우저에서 테스트
```
http://localhost:3000/main
```

### 3. 필터 테스트 시나리오

**시나리오 1: 지역 필터**
1. "서울 구" 드롭다운 클릭
2. "강남구" 선택
3. 강남구 매물만 표시되는지 확인

**시나리오 2: 거래유형 필터**
1. "거래유형" 드롭다운 클릭
2. "전세" 선택
3. 전세 매물만 표시되는지 확인

**시나리오 3: 건물유형 필터**
1. "건물유형" 드롭다운 클릭
2. "아파트" 선택
3. 아파트만 표시되는지 확인

**시나리오 4: 복합 필터**
1. 강남구 + 전세 + 아파트 선택
2. 조건에 맞는 매물만 표시되는지 확인

**시나리오 5: 검색**
1. 검색창에 "서초동" 입력
2. 주소에 "서초동"이 포함된 매물만 표시되는지 확인

**시나리오 6: 필터 해제**
1. 선택된 필터 태그의 X 버튼 클릭
2. 해당 필터만 해제되는지 확인
3. "초기화" 버튼 클릭
4. 모든 필터가 해제되는지 확인

## 데이터베이스 통계

```sql
-- 지역별 매물 수
SELECT SPLIT_PART(address, ' ', 2) as district, COUNT(*) 
FROM land 
WHERE address LIKE '서울%' 
GROUP BY district 
ORDER BY COUNT(*) DESC;

-- 거래유형별 매물 수
SELECT deal_type, COUNT(*) 
FROM land 
WHERE deal_type IN ('매매', '전세', '월세')
GROUP BY deal_type;

-- 건물유형별 매물 수
SELECT building_type, COUNT(*) 
FROM land 
GROUP BY building_type;
```

## 향후 개선 사항

1. ✅ 서울 구 필터 완료
2. ⏳ 경기도 시/구 필터 추가
3. ⏳ 가격 범위 필터 추가
4. ⏳ 면적 범위 필터 추가
5. ⏳ 지하철역 기반 필터 추가
6. ⏳ 학교 기반 필터 추가
7. ⏳ 필터 조합 저장 기능
8. ⏳ 인기 필터 조합 추천

## 수정된 백엔드 필터링 로직

### 변경 사항 (`apps/backend/apps/listings/views.py`)

**변경 전:**
```python
filterset_fields = ['address', 'deal_type', 'building_type']
# 문제: address는 정확히 일치하는 경우만 필터링
```

**변경 후:**
```python
def get_queryset(self):
    queryset = super().get_queryset()
    
    # 지역 필터 (부분 일치 - icontains)
    address = self.request.query_params.get('address', None)
    if address:
        queryset = queryset.filter(address__icontains=address)
    
    # 거래유형 필터 (정확히 일치)
    deal_type = self.request.query_params.get('deal_type', None)
    if deal_type:
        queryset = queryset.filter(deal_type=deal_type)
    
    # 건물유형 필터 (정확히 일치)
    building_type = self.request.query_params.get('building_type', None)
    if building_type:
        queryset = queryset.filter(building_type=building_type)
    
    return queryset
```

**개선 효과:**
- ✅ 거래유형 필터링 정확도 100% (월세 선택 시 월세만 표시)
- ✅ 건물유형 필터링 정확도 100% (아파트 선택 시 아파트만 표시)
- ✅ 지역 필터링 부분 일치 (강남구 선택 시 주소에 "강남구" 포함된 모든 매물)
- ✅ 복합 필터링 정상 작동 (AND 조건)

## 문제 해결

### 필터가 작동하지 않는 경우

1. **백엔드 재시작**
   ```powershell
   cd apps\backend
   # Ctrl+C로 종료 후
   uv run python manage.py runserver
   ```

2. **API 직접 테스트**
   ```powershell
   # 월세 필터링 테스트
   curl "http://localhost:8000/api/listings/lands/?deal_type=월세"
   
   # 강남구 + 전세 복합 필터링 테스트
   curl "http://localhost:8000/api/listings/lands/?address=강남구&deal_type=전세"
   ```

3. **브라우저 콘솔 확인**
   - F12 → Console 탭
   - Network 탭에서 API 요청 URL 확인
   - 응답 데이터 확인

4. **필터 파라미터 확인**
   - React DevTools로 filterParams 상태 확인
   - LandList 컴포넌트의 props 확인

### 매물이 표시되지 않는 경우

1. **데이터 확인**
   ```sql
   -- 월세 매물 수 확인
   SELECT COUNT(*) FROM land WHERE deal_type = '월세';
   
   -- 강남구 매물 수 확인
   SELECT COUNT(*) FROM land WHERE address LIKE '%강남구%';
   
   -- 복합 조건 확인
   SELECT COUNT(*) FROM land WHERE address LIKE '%강남구%' AND deal_type = '월세';
   ```

2. **필터 조건 완화**
   - 복합 필터 대신 단일 필터로 테스트
   - 검색어 제거 후 테스트

3. **초기화 후 재시도**
   - "초기화" 버튼 클릭 후 다시 필터 선택
   - 페이지 새로고침 (F5)
