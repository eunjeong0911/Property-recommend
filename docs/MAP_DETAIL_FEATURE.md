# 매물 상세 페이지 지도 기능

## 개요

매물 상세 페이지에서 해당 매물의 위치를 중심으로 지도를 표시하고, 상세한 매물 정보를 인포윈도우로 보여주는 기능입니다.

## 구현 내용

### 1. 백엔드 API 개선

**엔드포인트:** `GET /api/listings/lands/locations/`

**새로운 Query Parameter:**
- `land_id`: 특정 매물 ID (이 경우 해당 매물만 반환)

**사용 예시:**
```bash
# 특정 매물의 위치 정보
curl "http://localhost:8000/api/listings/lands/locations/?land_id=18375960"
```

**응답:**
```json
{
  "count": 1,
  "results": [
    {
      "id": "18375960",
      "latitude": 37.4656078421813,
      "longitude": 127.034503543674,
      "address": "서울특별시 서초구 양재동 208-9 화평빌라타운",
      "name": "Unknown",
      "price": "전세",
      "building_type": "빌라주택"
    }
  ]
}
```

### 2. Map 컴포넌트 개선

**Props 추가:**
```typescript
interface MapProps {
    landId?: string; // 매물 상세 페이지에서 전달되는 매물 ID
}
```

**동작 방식:**

#### 메인 페이지 (landId 없음)
- 여러 매물 마커 표시 (최대 100개)
- 서울 중심으로 지도 표시
- 줌 레벨: 7 (넓게)
- 마커 클릭 시 매물 상세 페이지로 이동
- 마커 호버 시 간단한 정보 표시

#### 매물 상세 페이지 (landId 있음)
- 해당 매물 1개만 마커 표시
- 매물 위치 중심으로 지도 표시
- 줌 레벨: 3 (확대)
- 인포윈도우 자동으로 열림
- 상세한 매물 정보 표시

### 3. 인포윈도우 내용

#### 메인 페이지 (간단한 정보)
```html
<div style="padding:10px;min-width:200px;">
    <div style="font-weight:bold;">전세</div>
    <div style="font-size:12px;">서울특별시 서초구 양재동 208-9</div>
    <div style="font-size:11px;">빌라주택</div>
</div>
```

#### 상세 페이지 (자세한 정보)
```html
<div style="padding:15px;min-width:250px;">
    <div style="font-weight:bold;font-size:16px;color:#2563eb;">전세</div>
    <div style="font-size:13px;">서울특별시 서초구 양재동 208-9 화평빌라타운</div>
    <div style="font-size:12px;">
        <span style="background:#e0f2fe;padding:2px 8px;">빌라주택</span>
    </div>
    <div style="font-size:11px;margin-top:8px;">
        매물번호: 18375960
    </div>
</div>
```

### 4. 페이지 연동

**매물 상세 페이지:** `apps/frontend/src/app/landDetail/[id]/page.tsx`

```tsx
<Map landId={id} />
```

## 기능 비교

| 기능 | 메인 페이지 | 상세 페이지 |
|------|------------|------------|
| 표시 매물 수 | 최대 100개 | 1개 |
| 지도 중심 | 서울 중심 | 매물 위치 |
| 줌 레벨 | 7 (넓게) | 3 (확대) |
| 인포윈도우 | 호버 시 표시 | 자동 표시 |
| 정보 상세도 | 간단 | 상세 |
| 마커 클릭 | 상세 페이지 이동 | 없음 |

## 데이터 흐름

### 메인 페이지
```
1. Map 컴포넌트 로드 (landId 없음)
   ↓
2. fetchLandLocations({ limit: 100 })
   ↓
3. 100개 매물 위치 로드
   ↓
4. 서울 중심으로 지도 표시
   ↓
5. 100개 마커 표시
```

### 상세 페이지
```
1. Map 컴포넌트 로드 (landId: "18375960")
   ↓
2. fetchLandLocations({ land_id: "18375960" })
   ↓
3. 해당 매물 위치 로드
   ↓
4. 매물 위치 중심으로 지도 표시
   ↓
5. 1개 마커 표시 + 인포윈도우 자동 열림
```

## 사용 예시

### 1. 메인 페이지에서 매물 찾기
```
http://localhost:3000/main
→ 지도에서 매물 마커 확인
→ 마커 클릭
→ 매물 상세 페이지로 이동
```

### 2. 상세 페이지에서 위치 확인
```
http://localhost:3000/landDetail/18375960
→ 해당 매물 위치 중심으로 지도 표시
→ 인포윈도우에 상세 정보 표시
→ 주변 시설 확인 가능
```

## 스타일링

### 인포윈도우 스타일 (상세 페이지)

- **제목 (거래유형)**: 
  - 폰트 크기: 16px
  - 색상: #2563eb (파란색)
  - 굵기: bold

- **주소**:
  - 폰트 크기: 13px
  - 색상: #374151 (진한 회색)
  - 줄 간격: 1.4

- **건물유형 태그**:
  - 배경: #e0f2fe (연한 파란색)
  - 패딩: 2px 8px
  - 둥근 모서리: 4px

- **매물번호**:
  - 폰트 크기: 11px
  - 색상: #9ca3af (연한 회색)
  - 상단 테두리: 1px solid #e5e7eb

## 테스트 방법

### 1. API 테스트
```bash
# 특정 매물 위치 조회
curl "http://localhost:8000/api/listings/lands/locations/?land_id=18375960"

# 응답 확인
# - latitude, longitude 값 확인
# - address, price, building_type 확인
```

### 2. 프론트엔드 테스트

**메인 페이지:**
```
1. http://localhost:3000/main 접속
2. 지도에 여러 마커 표시 확인
3. 마커에 마우스 올려서 정보 확인
4. 마커 클릭하여 상세 페이지 이동 확인
```

**상세 페이지:**
```
1. http://localhost:3000/landDetail/1 접속
2. 해당 매물 위치 중심으로 지도 표시 확인
3. 인포윈도우 자동 표시 확인
4. 상세 정보 내용 확인 (거래유형, 주소, 건물유형, 매물번호)
```

### 3. 브라우저 콘솔 확인 (F12)

**예상 로그:**
```
카카오 지도 스크립트 로드 완료
매물 위치 로드 완료: {id: "18375960", latitude: 37.46..., ...}
카카오 지도 API 로드 완료
지도 생성 완료
마커 추가 완료
매물 마커 1개 표시 완료
```

## 문제 해결

### 지도가 매물 위치로 이동하지 않는 경우

**원인:**
- Neo4j에 해당 매물의 위도/경도 정보가 없음
- API 응답이 비어있음

**해결:**
```bash
# Neo4j에서 해당 매물 확인
docker exec -i skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p password123 "MATCH (p:Property {id: '18375960'}) RETURN p.latitude, p.longitude;"

# 위도/경도가 없으면 데이터 임포트 필요
```

### 인포윈도우가 표시되지 않는 경우

**원인:**
- 카카오맵 API 로드 실패
- 마커 생성 오류

**해결:**
1. 브라우저 콘솔에서 오류 확인
2. 카카오맵 API 키 확인 (`.env` 파일)
3. 페이지 새로고침 (Ctrl+R)

### 마커가 표시되지 않는 경우

**원인:**
- API 응답이 비어있음
- locations 상태가 업데이트되지 않음

**해결:**
1. 브라우저 콘솔에서 "매물 위치 로드 완료" 메시지 확인
2. Network 탭에서 API 응답 확인
3. React DevTools로 locations 상태 확인

## 향후 개선 사항

1. ✅ 매물 상세 페이지 지도 중심 표시 완료
2. ✅ 상세한 인포윈도우 표시 완료
3. ⏳ 주변 시설 마커 추가 (지하철역, 학교, 편의점 등)
4. ⏳ 거리 측정 도구
5. ⏳ 로드뷰 연동
6. ⏳ 주변 매물 표시 (반경 1km 내)
7. ⏳ 지도 스타일 커스터마이징
8. ⏳ 인포윈도우에 매물 이미지 추가

## 참고 자료

- [카카오맵 API - 마커](https://apis.map.kakao.com/web/sample/basicMarker/)
- [카카오맵 API - 인포윈도우](https://apis.map.kakao.com/web/sample/basicInfowindow/)
- [카카오맵 API - 지도 중심 이동](https://apis.map.kakao.com/web/sample/moveMap/)
