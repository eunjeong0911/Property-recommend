# 지도 마커 상세 정보 오버레이 기능

## 개요

지도의 매물 마커를 클릭하면 상세 정보가 포함된 커스텀 오버레이가 표시되는 기능입니다.

## 구현 내용

### 1. 백엔드 API 개선

**추가된 정보:**
- `deal_type`: 거래유형 (전세, 월세, 매매 등)
- `maintenance_fee`: 관리비
- `area`: 면적 (전용/공급면적)
- `price`: 포맷팅된 가격

**API 응답 예시:**
```json
{
  "id": "18375960",
  "latitude": 37.4656078421813,
  "longitude": 127.034503543674,
  "address": "서울특별시 서초구 양재동 208-9 화평빌라타운",
  "deal_type": "전세",
  "building_type": "빌라주택",
  "price": "전세 1억 2,500만원",
  "maintenance_fee": "7만원 수도 관리비 별도 난방, 전기, 가스",
  "area": "30m2/38.68m2 (9.07평/11.7평)"
}
```

### 2. 프론트엔드 커스텀 오버레이

#### 메인 페이지 동작

**1단계: 마커 클릭**
- 간단한 정보 오버레이 표시
- 거래유형, 건물유형 태그
- "클릭하여 상세보기" 안내

**2단계: 오버레이 클릭 (또는 마커 재클릭)**
- 매물 상세 페이지로 이동

#### 상세 페이지 동작

**자동 표시:**
- 페이지 로드 시 오버레이 자동 표시
- 상세한 매물 정보 포함
- 닫기 버튼 (빨간 X 버튼)

**표시 정보:**
- 가격 (큰 글씨, 파란색)
- 전체 주소
- 거래유형 태그 (파란색)
- 건물유형 태그 (하늘색)
- 관리비
- 면적
- 매물번호

### 3. 오버레이 스타일

#### 메인 페이지 (간단)
```
┌─────────────────────────┐
│ 전세 1억 2,500만원      │
│ 서울특별시 서초구...    │
│ [빌라주택]              │
│ ─────────────────────   │
│ 클릭하여 상세보기       │
└─────────────────────────┘
```

#### 상세 페이지 (상세)
```
┌─────────────────────────┐ [X]
│ 전세 1억 2,500만원      │
│ 서울특별시 서초구 양재동│
│ 208-9 화평빌라타운      │
│ [전세] [빌라주택]       │
│ ─────────────────────   │
│ 관리비: 7만원...        │
│ 면적: 30m2/38.68m2      │
│ 매물번호: 18375960      │
└─────────────────────────┘
```

### 4. 사용자 인터랙션

#### 메인 페이지
1. 마커 클릭 → 오버레이 표시
2. 다른 마커 클릭 → 이전 오버레이 닫힘, 새 오버레이 표시
3. 오버레이 클릭 (또는 마커 재클릭) → 상세 페이지 이동

#### 상세 페이지
1. 페이지 로드 → 오버레이 자동 표시
2. X 버튼 클릭 → 오버레이 닫힘
3. 지도 드래그/줌 → 오버레이 유지

## 기술 구현

### 카카오맵 CustomOverlay 사용

```typescript
const customOverlay = new window.kakao.maps.CustomOverlay({
    position: position,
    content: overlayContent,
    yAnchor: 1.5,  // 마커 위에 표시
    zIndex: 3       // 다른 요소 위에 표시
});
```

### 동적 HTML 생성

```typescript
const overlayContent = document.createElement('div');
overlayContent.style.cssText = `
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 16px;
`;
overlayContent.innerHTML = contentHTML;
```

### 이벤트 처리

```typescript
// 닫기 버튼
const closeBtn = document.getElementById(`close-overlay-${location.id}`);
closeBtn.addEventListener('click', () => {
    customOverlay.setMap(null);
});

// 마커 클릭
window.kakao.maps.event.addListener(marker, 'click', () => {
    if (isOverlayOpen) {
        // 상세 페이지로 이동
        window.location.href = `/landDetail/${location.id}`;
    } else {
        // 오버레이 열기
        customOverlay.setMap(mapRef.current);
    }
});
```

## 스타일 가이드

### 색상
- **가격 (제목)**: #2563eb (파란색)
- **거래유형 태그**: 배경 #dbeafe, 텍스트 #1e40af
- **건물유형 태그**: 배경 #e0f2fe, 텍스트 #0369a1
- **본문**: #374151 (진한 회색)
- **보조 정보**: #6b7280 (회색)
- **매물번호**: #9ca3af (연한 회색)
- **닫기 버튼**: #ef4444 (빨간색)

### 크기
- **메인 페이지**: 최소 250px, 최대 350px
- **상세 페이지**: 최소 300px, 최대 350px
- **패딩**: 16px
- **둥근 모서리**: 12px
- **그림자**: 0 4px 12px rgba(0,0,0,0.15)

## 데이터 흐름

```
1. 사용자가 마커 클릭
   ↓
2. 마커 클릭 이벤트 발생
   ↓
3. isOverlayOpen 상태 확인
   ↓
4-A. 닫혀있으면 → 오버레이 표시
4-B. 열려있으면 → 상세 페이지 이동
   ↓
5. 다른 마커 클릭 시 이전 오버레이 자동 닫힘
```

## 테스트 방법

### 1. 메인 페이지 테스트
```
1. http://localhost:3000/main 접속
2. 지도에서 마커 클릭
3. 오버레이 표시 확인
   - 가격, 주소, 건물유형 확인
   - "클릭하여 상세보기" 메시지 확인
4. 다른 마커 클릭
   - 이전 오버레이 닫힘 확인
   - 새 오버레이 표시 확인
5. 오버레이 클릭 (또는 마커 재클릭)
   - 상세 페이지로 이동 확인
```

### 2. 상세 페이지 테스트
```
1. http://localhost:3000/landDetail/1 접속
2. 오버레이 자동 표시 확인
3. 상세 정보 확인
   - 가격
   - 전체 주소
   - 거래유형, 건물유형 태그
   - 관리비
   - 면적
   - 매물번호
4. X 버튼 클릭
   - 오버레이 닫힘 확인
5. 지도 드래그/줌
   - 오버레이 위치 유지 확인
```

### 3. API 테스트
```bash
# 추가 정보 포함 확인
curl "http://localhost:8000/api/listings/lands/locations/?land_id=1"

# 응답에서 확인할 항목:
# - deal_type
# - maintenance_fee
# - area
# - price
```

## 문제 해결

### 오버레이가 표시되지 않는 경우

**원인:**
- CustomOverlay 생성 오류
- 위치 정보 오류

**해결:**
1. 브라우저 콘솔에서 오류 확인
2. location 데이터 확인 (latitude, longitude)
3. 페이지 새로고침

### 닫기 버튼이 작동하지 않는 경우

**원인:**
- 이벤트 리스너 등록 타이밍 문제
- DOM 요소를 찾지 못함

**해결:**
1. setTimeout으로 이벤트 등록 지연 (현재 100ms)
2. 버튼 ID 확인 (`close-overlay-${location.id}`)

### 오버레이가 마커 아래에 표시되는 경우

**원인:**
- zIndex 설정 문제

**해결:**
```typescript
const customOverlay = new window.kakao.maps.CustomOverlay({
    zIndex: 3  // 높은 값으로 설정
});
```

### 여러 오버레이가 동시에 열리는 경우

**원인:**
- 이전 오버레이를 닫지 않음

**해결:**
```typescript
// 다른 오버레이 닫기
markersRef.current.forEach(item => {
    if (item.overlay !== customOverlay) {
        item.overlay.setMap(null);
    }
});
```

## 향후 개선 사항

1. ✅ 클릭 가능한 오버레이 완료
2. ✅ 상세 정보 표시 완료
3. ✅ 닫기 버튼 완료
4. ⏳ 오버레이 애니메이션 추가
5. ⏳ 매물 이미지 썸네일 추가
6. ⏳ 찜하기 버튼 추가
7. ⏳ 공유하기 버튼 추가
8. ⏳ 오버레이 내에서 간단한 슬라이더로 이미지 미리보기

## 참고 자료

- [카카오맵 API - CustomOverlay](https://apis.map.kakao.com/web/sample/customOverlay1/)
- [카카오맵 API - 이벤트](https://apis.map.kakao.com/web/documentation/#event)
