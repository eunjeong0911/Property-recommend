import { Land, LandFilterParams } from '../types/land';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchLands(params?: LandFilterParams): Promise<Land[]> {
    const queryParams = new URLSearchParams();

    if (params) {
        // 자치구 + 행정동을 조합하여 address로 전달
        let addressFilter = '';
        if (params.region) addressFilter = params.region;
        if (params.dong) addressFilter += (addressFilter ? ' ' : '') + params.dong;

        if (addressFilter) queryParams.append('address', addressFilter);
        if (params.transaction_type) queryParams.append('deal_type', params.transaction_type);
        if (params.building_type) queryParams.append('building_type', params.building_type);
        if (params.search) queryParams.append('search', params.search);
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
}

export async function fetchLandsByFilter(params: ChatbotFilterParams): Promise<Land[]> {
    const queryParams = new URLSearchParams();

    // 위치를 search로 전달 (주소 검색)
    if (params.location) queryParams.append('search', params.location);
    if (params.deal_type) queryParams.append('deal_type', params.deal_type);
    if (params.building_type) queryParams.append('building_type', params.building_type);

    const response = await fetch(`${API_BASE_URL}/api/listings/lands/?${queryParams.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch lands by filter');
    }

    const data = await response.json();
    const results = data.results || data;
    return results.slice(0, 20); // 상위 20개만 반환
}

export async function fetchLandById(id: string): Promise<Land> {
    const response = await fetch(`${API_BASE_URL}/api/listings/lands/${id}/`);

    if (!response.ok) {
        throw new Error('Failed to fetch land details');
    }

    return response.json();
}

// 여러 ID로 Land 데이터 일괄 조회 (챗봇 추천용)
export async function fetchLandsByIds(ids: (string | number)[]): Promise<Land[]> {
    if (!ids || ids.length === 0) return [];

    // 병렬로 개별 요청 (백엔드에 일괄 조회 API가 없으므로)
    const promises = ids.slice(0, 20).map(id =>
        fetch(`${API_BASE_URL}/api/listings/lands/${id}/`)
            .then(res => res.ok ? res.json() : null)
            .catch(() => null)
    );

    const results = await Promise.all(promises);
    return results.filter((land): land is Land => land !== null);
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

