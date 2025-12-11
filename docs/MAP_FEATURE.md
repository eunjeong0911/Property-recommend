# 지도 매물 마커 기능

## 개요

Neo4j에 저장된 매물의 위도/경도 정보를 활용하여 카카오맵에 매물 마커를 표시하는 기능입니다.

## 구현 내용

### 1. 백엔드 API (`apps/backend/apps/listings/views.py`)

#### 새로운 엔드포인트: `/api/listings/lands/locations/`

**기능:**
- Neo4j에서 매물의 위도/경도 정보 조회
- 필터링 지원 (주소, 거래유형)
- PostgreSQL과 연동하여 추가 정보 제공

**Query Parameters:**
- `limit`: 반환할 최대 매물 수 (기본값: 100)
- `address`: 주소 필터 (부분 일치)
- `deal_type`: 거래유형 필터 (매매, 전세, 월세, 단기임대, 미분류)

**응답 예시:**
```json
{
  "count": 5,
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

### 2. 프론트엔드 API (`apps/frontend/src/api/landApi.ts`)

#### 새로운 함수: `fetchLandLocations()`

```typescript
export interface LandLocation {
    id: string;
    latitude: number;
    longitude: number;
    address: string;
    name: string;
    price?: string;
    building_type?: string;
}

export async function fetchLandLocations(params?: {
    limit?: number;
    address?: string;
    deal_type?: string;
}): Promise<LandLocation[]>
```

**사용 예시:**
```typescript
// 전체 매물 100개
const locations = await fetchLandLocations({ limit: 100 });

// 강남구 매물만
const gangnamLocations = await fetchLandLocations({ 
    address: '강남구',
    limit: 50 
});

// 전세 매물만
const jeonseLocations = await fetchLandLocations({ 
    deal_type: '전세',
    limit: 100 
});
```

### 3. Map 컴포넌트 (`apps/frontend/src/components/Map.tsx`)

#### 주요 기능

**1. 매물 위치 데이터 로드**
```typescript
useEffect(() => {
    const loadLocations = async () => {
        const data = await fetchLandLocations({ limit: 100 });
        setLocations(data);
    };
    loadLocations();
}, []);
```

**2. 매물 마커 표시**
- 각 매물의 위도/경도에 마커 생성
- 마커 클릭 시 매물 상세 페이지로 이동
- 마커 호버 시 인포윈도우 표시

**3. 인포윈도우 내용**
- 거래유형 (전세, 월세 등)
- 주소
- 건물유형

**4. 이벤트 처리**
- 클릭: 매물 상세 페이지로 이동 (`/landDetail/{id}`)
- 마우스 오버: 인포윈도우 표시
- 마우스 아웃: 인포윈도우 숨김

## 데이터 흐름

```
1. 사용자가 메인 페이지 접속
   ↓
2. Map 컴포넌트 로드
   ↓
3. fetchLandLocations() 호출
   ↓
4. 백엔드 API: /api/listings/lands/locations/
   ↓
5. Neo4j에서 위도/경도 조회
   ↓
6. PostgreSQL에서 추가 정보 조회 (선택적)
   ↓
7. 프론트엔드로 데이터 반환
   ↓
8. 카카오맵에 마커 표시
   ↓
9. 사용자가 마커 클릭
   ↓
10. 매물 상세 페이지로 이동
```

## Neo4j 데이터 구조

```cypher
// Property 노드 구조
(:Property {
    id: "18375960",
    name: "Unknown",
    address: "서울특별시 서초구 양재동 208-9 화평빌라타운",
    latitude: 37.4656078421813,
    longitude: 127.034503543674,
    location: point({srid:4326, x:127.034503543674, y:37.4656078421813})
})
```

## API 테스트

### 기본 조회
```bash
curl "http://localhost:8000/api/listings/lands/locations/?limit=5"
```

### 주소 필터
```bash
curl "http://localhost:8000/api/listings/lands/locations/?address=강남구&limit=10"
```

### 거래유형 필터
```bash
curl "http://localhost:8000/api/listings/lands/locations/?deal_type=전세&limit=20"
```

### 복합 필터
```bash
curl "http://localhost:8000/api/listings/lands/locations/?address=서초구&deal_type=월세&limit=30"
```

## 성능 최적화

### 1. 제한된 수의 마커 표시
- 기본값: 100개
- 너무 많은 마커는 성능 저하 유발
- 필요시 limit 파라미터 조정

### 2. 필터링 활용
- 지역별 필터링으로 관련 매물만 표시
- 거래유형별 필터링으로 사용자 관심사에 맞는 매물만 표시

### 3. 마커 클러스터링 (향후 개선)
- 많은 마커를 그룹화하여 표시
- 줌 레벨에 따라 자동 조정

## 사용 방법

### 1. 백엔드 실행
```powershell
cd apps\backend
uv run python manage.py runserver
```

### 2. 프론트엔드 실행
```powershell
cd apps\frontend
npm run dev
```

### 3. 브라우저에서 확인
```
http://localhost:3000/main
```

### 4. 지도에서 매물 확인
- 지도에 빨간 마커들이 표시됨
- 마커에 마우스를 올리면 매물 정보 표시
- 마커를 클릭하면 매물 상세 페이지로 이동

## 문제 해결

### 마커가 표시되지 않는 경우

**1. API 확인**
```bash
curl "http://localhost:8000/api/listings/lands/locations/?limit=5"
```

**2. 브라우저 콘솔 확인 (F12)**
- "매물 위치 X개 로드 완료" 메시지 확인
- "매물 마커 X개 표시 완료" 메시지 확인
- 오류 메시지 확인

**3. Neo4j 데이터 확인**
```bash
docker exec -i skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p password123 "MATCH (p:Property) WHERE p.latitude IS NOT NULL RETURN count(p);"
```

**4. 카카오맵 API 키 확인**
- `.env` 파일에 `NEXT_PUBLIC_KAKAO_MAP_KEY` 설정 확인

### 마커 클릭이 작동하지 않는 경우

**1. 브라우저 콘솔 확인**
- 클릭 이벤트 오류 확인

**2. 매물 ID 확인**
- 인포윈도우에 표시된 정보 확인
- 해당 ID로 매물 상세 페이지 접근 가능한지 확인

## 향후 개선 사항

1. ✅ 매물 마커 표시 완료
2. ⏳ 마커 클러스터링 추가
3. ⏳ 커스텀 마커 아이콘 (거래유형별 색상)
4. ⏳ 지도 범위 내 매물만 로드 (동적 로딩)
5. ⏳ 매물 필터와 연동 (필터 변경 시 마커 업데이트)
6. ⏳ 마커 클릭 시 사이드 패널에 매물 정보 표시
7. ⏳ 매물 검색 결과를 지도에 표시
8. ⏳ 지도 중심 기준 주변 매물 추천

## 데이터 통계

```sql
-- Neo4j에서 위도/경도가 있는 매물 수
MATCH (p:Property) 
WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL 
RETURN count(p);
// 결과: 약 3,000개

-- 지역별 매물 분포
MATCH (p:Property) 
WHERE p.latitude IS NOT NULL 
RETURN p.address, count(p) 
ORDER BY count(p) DESC 
LIMIT 10;
```

## 참고 자료

- [카카오맵 API 문서](https://apis.map.kakao.com/web/)
- [Neo4j Cypher 문서](https://neo4j.com/docs/cypher-manual/current/)
- [Django REST Framework](https://www.django-rest-framework.org/)
