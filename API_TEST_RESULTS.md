# API 테스트 결과

## 매물 상세 정보 DB 연동 완료

### 수정 사항

#### 1. 백엔드 시리얼라이저 개선 (`apps/backend/apps/listings/serializers.py`)

**가격 파싱 로직 개선 (만원 단위 표기):**
- ✅ 전세: "전세   1억 2,500만원" → `전세 1억 2,500만원`
- ✅ 월세: "월세   2,500만원/104만원" → `월세 2,500만원 / 104만원`
- ✅ 매매: "매매   4억 5,000만원" → `매매 4억 5,000만원`
- ✅ 단기임대: "단기임대   110만원/110만원" → `단기임대 110만원/110만원`

**한국어 가격 문자열 파싱:**
```python
"1억 2,500만원" → 125,000,000
"4억 5,000만원" → 450,000,000
"2,500만원" → 25,000,000
"104만원" → 1,040,000
```

**매물 정보 추출:**
- listing_info JSON에서 상세 정보 추출
- trade_info JSON에서 거래 정보 추출
- 모든 필드가 DB 데이터와 정확히 매핑됨

### 테스트 결과

#### 전세 매물 (ID: 1)
```json
{
  "id": 1,
  "title": "빌라 9.07평/11.7평",
  "price": "전세 1억 2,500만원",
  "transaction_type": "전세",
  "deposit": 125000000,
  "monthly_rent": 0
}
```

#### 월세 매물 (ID: 4)
```json
{
  "id": 4,
  "title": "빌라 10.9평/12.43평",
  "price": "월세 2,500만원 / 104만원",
  "transaction_type": "월세",
  "deposit": 25000000,
  "monthly_rent": 1040000
}
```

#### 매매 매물 (ID: 5)
```json
{
  "id": 5,
  "title": "빌라 5.99평/8.65평",
  "price": "매매 4억 5,000만원",
  "transaction_type": "매매",
  "deposit": 450000000,
  "monthly_rent": 0
}
```

#### 전세 매물 (ID: 3) - 억 단위만
```json
{
  "id": 3,
  "title": "빌라",
  "price": "전세 4억",
  "transaction_type": "전세",
  "deposit": 400000000,
  "monthly_rent": 0
}
```

#### 단기임대 매물 (ID: 20)
```json
{
  "id": 20,
  "title": "빌라 9평/10평",
  "price": "단기임대 110만원/110만원",
  "transaction_type": "단기임대 110만원/110만원",
  "deposit": 1100000,
  "monthly_rent": 1100000
}
```

### 연동된 필드 목록

#### 기본 정보
- ✅ id (매물 ID)
- ✅ title (매물 제목 - 건물형태 + 평수)
- ✅ image (대표 이미지)
- ✅ images (전체 이미지 배열)
- ✅ temperature (부동산 온도)
- ✅ price (포맷팅된 가격)
- ✅ deposit (보증금/매매가)
- ✅ monthly_rent (월세)

#### 거래 정보
- ✅ transaction_type (거래 유형: 전세/월세/매매/단기임대)
- ✅ building_type (건물 유형)
- ✅ land_num (매물 번호)
- ✅ address (주소)

#### 상세 정보 (listing_info에서 추출)
- ✅ floor (층수: "저층/3층")
- ✅ room_count (방/욕실 개수: "2개/1개")
- ✅ area_supply (공급면적: "38.68m2")
- ✅ area_exclusive (전용면적: "30m2")
- ✅ direction (방향: "안방/남동향")
- ✅ parking (주차: "가능")
- ✅ heating_method (난방방식: "중앙난방")
- ✅ elevator (엘리베이터: "없음")

#### 입주 정보 (trade_info에서 추출)
- ✅ move_in_date (입주가능일: "즉시입주 (협의가능)")
- ✅ maintenance_fee (관리비: "7만원 수도 관리비 별도 난방, 전기, 가스")

#### 중개사 정보
- ✅ agent_info.name (중개사무소명)
- ✅ agent_info.phone (전화번호)
- ✅ agent_info.representative (대표자)
- ✅ agent_info.address (주소)

#### 기타
- ✅ description (상세 설명)

### API 엔드포인트

```
GET /api/listings/lands/          # 매물 목록
GET /api/listings/lands/{id}/     # 매물 상세

# 필터링
GET /api/listings/lands/?address=서초구
GET /api/listings/lands/?deal_type=전세
GET /api/listings/lands/?building_type=빌라주택
```

### 프론트엔드 사용 예시

```typescript
// 매물 상세 페이지
const land = await fetchLandById('1');

console.log(land.price);           // "전세 1억 2,500만원"
console.log(land.floor);           // "저층/3층"
console.log(land.room_count);      // "2개/1개"
console.log(land.area_supply);     // "38.68m2"
console.log(land.maintenance_fee); // "7만원 수도 관리비 별도..."
```

### 데이터베이스 통계

```
총 매물 수: 8,948개
- 월세: 6,351개 (71%)
- 전세: 1,965개 (22%)
- 매매: 582개 (6.5%)
- 단기임대: 50개 (0.5%)
```

## 다음 단계

1. ✅ 백엔드 API 완료
2. ✅ 프론트엔드 타입 정의 완료
3. ⏳ 프론트엔드 컴포넌트 테스트 필요
4. ⏳ 부동산 온도 실제 계산 로직 구현 (현재 랜덤 값)
5. ⏳ 중개사 정보 데이터 수집 (현재 대부분 비어있음)

## 테스트 방법

```powershell
# 백엔드 실행
cd apps\backend
uv run python manage.py runserver

# 프론트엔드 실행
cd apps\frontend
npm run dev

# 브라우저에서 테스트
# http://localhost:3000/landDetail/1
# http://localhost:3000/landDetail/4
# http://localhost:3000/landDetail/5
```
