import { Land, LandFilterParams } from '../types/land';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchLands(params?: LandFilterParams): Promise<Land[]> {
    const queryParams = new URLSearchParams();

    if (params) {
        if (params.district) queryParams.append('district', params.district);
        if (params.dong) queryParams.append('dong', params.dong);
        if (params.transaction_type) queryParams.append('deal_type', params.transaction_type);
        if (params.building_type) queryParams.append('building_type', params.building_type);
        if (params.search) queryParams.append('search', params.search);

        // 하위 호환성을 위해 address도 전달 (필요시)
        if (params.district || params.dong) {
            let addressFilter = params.district || '';
            if (params.dong) addressFilter += (addressFilter ? ' ' : '') + params.dong;
            queryParams.append('address', addressFilter);
        }
    }

    const response = await fetch(`${API_BASE_URL}/api/listings/lands/?${queryParams.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch lands');
    }

    const data = await response.json();
    return data.results || data; // DRF pagination support
}

// ChatbotFilter 조건으로 매물 검색 (실시간 필터링용)
export interface ChatbotFilterParams {
    location?: string;          // 위치 (검색어로 사용)
    deal_type?: string;         // 거래 유형
    building_type?: string;     // 건물 유형
    max_deposit?: number;       // 보증금 상한 (만원)
    max_rent?: number;          // 월세 상한 (만원)
}

export async function fetchLandsByFilter(params: ChatbotFilterParams): Promise<Land[]> {
    const queryParams = new URLSearchParams();

    // 위치를 address로 전달 (주소 검색)
    if (params.location) queryParams.append('address', params.location);
    if (params.deal_type) queryParams.append('deal_type', params.deal_type);
    if (params.building_type) queryParams.append('building_type', params.building_type);

    console.log('[fetchLandsByFilter] 🔍 API 호출:', `${API_BASE_URL}/api/listings/lands/?${queryParams.toString()}`);

    const response = await fetch(`${API_BASE_URL}/api/listings/lands/?${queryParams.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch lands by filter');
    }

    const data = await response.json();
    let results: Land[] = data.results || data;

    console.log('[fetchLandsByFilter] 📦 API 응답:', results.length, '개');

    // 클라이언트 사이드 가격 필터링 (백엔드에서 지원하지 않는 경우)
    if (params.max_deposit) {
        results = results.filter(land => {
            const deposit = land.deposit || 0;
            return deposit <= params.max_deposit!;
        });
        console.log('[fetchLandsByFilter] 💰 보증금 필터 후:', results.length, '개');
    }

    if (params.max_rent) {
        results = results.filter(land => {
            const rent = land.monthly_rent || 0;
            return rent <= params.max_rent!;
        });
        console.log('[fetchLandsByFilter] 💰 월세 필터 후:', results.length, '개');
    }

    return results.slice(0, 50); // 상위 50개만 반환
}

export async function fetchLandById(id: string): Promise<Land> {
    const response = await fetch(`${API_BASE_URL}/api/listings/lands/${id}/`);

    if (!response.ok) {
        throw new Error('Failed to fetch land details');
    }

    return response.json();
}

// 여러 ID로 Land 데이터 일괄 조회 (챗봇 추천용)
// RAG에서 반환하는 id는 land_num(매물번호)이므로 search API 사용
export async function fetchLandsByIds(ids: (string | number)[]): Promise<Land[]> {
    if (!ids || ids.length === 0) return [];

    console.log('[fetchLandsByIds] 🔍 조회할 ID들:', ids.slice(0, 5), '...');

    // 방법 1: 개별 조회 (land_num으로 검색)
    const promises = ids.slice(0, 20).map(async (id) => {
        try {
            // land_num으로 검색
            const response = await fetch(`${API_BASE_URL}/api/listings/lands/?search=${id}`);
            if (!response.ok) return null;
            const data = await response.json();
            const results = data.results || data;
            // 정확히 일치하는 매물 찾기
            const exactMatch = results.find((land: Land) =>
                land.land_num === String(id) || land.id === Number(id)
            );
            return exactMatch || (results.length > 0 ? results[0] : null);
        } catch {
            return null;
        }
    });

    const results = await Promise.all(promises);
    const validResults = results.filter((land): land is Land => land !== null);
    console.log('[fetchLandsByIds] ✅ 조회 완료:', validResults.length, '개');
    return validResults;
}

export async function fetchSimilarListings(landId: string): Promise<Land[]> {
    const response = await fetch(`${API_BASE_URL}/api/listings/lands/${landId}/similar_listings/`);

    if (!response.ok) {
        throw new Error('Failed to fetch similar listings');
    }

    const data = await response.json();
    return data.results || [];
}

export interface LandLocation {
    id: string;
    latitude: number;
    longitude: number;
    address: string;
    name: string;
    price?: string;
    deal_type?: string;
    building_type?: string;
    area?: string;
}

export async function fetchLandLocations(params?: {
    limit?: number;
    land_id?: string;
    address?: string;
    deal_type?: string;
}): Promise<LandLocation[]> {
    const queryParams = new URLSearchParams();

    if (params) {
        if (params.limit) queryParams.append('limit', params.limit.toString());
        if (params.land_id) queryParams.append('land_id', params.land_id);
        if (params.address) queryParams.append('address', params.address);
        if (params.deal_type) queryParams.append('deal_type', params.deal_type);
    }

    const response = await fetch(`${API_BASE_URL}/api/listings/lands/locations/?${queryParams.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch land locations');
    }

    const data = await response.json();
    return data.results || [];
}

export interface FacilityInfo {
    count: number;
    name: string;
    icon: string;
}

export interface NearbyFacilities {
    medical: FacilityInfo;
    convenience: FacilityInfo;
    transportation: FacilityInfo;
    safety: FacilityInfo;
    location?: {
        latitude: number;
        longitude: number;
    };
}

export async function fetchNearbyFacilities(landId: string): Promise<NearbyFacilities> {
    const response = await fetch(`${API_BASE_URL}/api/listings/lands/${landId}/nearby_facilities/`);

    if (!response.ok) {
        throw new Error('Failed to fetch nearby facilities');
    }

    return response.json();
}

export interface FacilityLocation {
    name: string;
    latitude: number;
    longitude: number;
    type: string;
    category: string;
}

export interface FacilityLocationsResponse {
    category: string;
    count: number;
    facilities: FacilityLocation[];
}

export async function fetchFacilityLocations(
    landId: string,
    category: 'transportation' | 'medical' | 'convenience' | 'safety'
): Promise<FacilityLocationsResponse> {
    const response = await fetch(
        `${API_BASE_URL}/api/listings/lands/${landId}/facility_locations/?category=${category}`
    );

    if (!response.ok) {
        throw new Error('Failed to fetch facility locations');
    }

    return response.json();
}
