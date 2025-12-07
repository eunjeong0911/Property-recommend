import { Land, LandFilterParams } from '../types/land';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchLands(params?: LandFilterParams): Promise<Land[]> {
    const queryParams = new URLSearchParams();

    if (params) {
        if (params.region) queryParams.append('address', params.region);
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

export async function fetchLandById(id: string): Promise<Land> {
    const response = await fetch(`${API_BASE_URL}/api/listings/lands/${id}/`);

    if (!response.ok) {
        throw new Error('Failed to fetch land details');
    }

    return response.json();
}
