import { Land, LandFilterParams } from '../types/land';

const API_BASE_URL = 'http://localhost:8000/api'; // Adjust if needed

export async function fetchLands(params?: LandFilterParams): Promise<Land[]> {
    const queryParams = new URLSearchParams();

    if (params) {
        if (params.region) queryParams.append('region', params.region);
        if (params.transaction_type) queryParams.append('transaction_type', params.transaction_type);
        if (params.building_type) queryParams.append('building_type', params.building_type);
        if (params.search) queryParams.append('search', params.search);
    }

    const response = await fetch(`${API_BASE_URL}/listings/lands/?${queryParams.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch lands');
    }

    return response.json();
}

export async function fetchLandById(id: string): Promise<Land> {
    const response = await fetch(`${API_BASE_URL}/listings/lands/${id}/`);

    if (!response.ok) {
        throw new Error('Failed to fetch land details');
    }

    return response.json();
}
