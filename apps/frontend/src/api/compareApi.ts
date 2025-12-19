/**
 * 매물 비교 API
 */

export interface CompareRequest {
    land_ids: number[];
}

export interface CompareResponse {
    summary: string;  // LLM 생성 마크다운
    properties: PropertyData[];
    count: number;
}

export interface PropertyData {
    land_id: number;
    land_num: string;
    address: string;
    building_type: string;
    deal_type: string;
    deposit: number;
    monthly_rent: number;
    jeonse_price: number;
    sale_price: number;
    area_exclusive?: string;
    area_supply?: string;
    floor?: string;
    room_count?: string;
    direction?: string;
    parking?: string;
    heating_method?: string;
    price_prediction?: {
        prediction_class: number;
        prediction_label: string;
        prediction_label_korean: string;
        probability_underpriced: number;
        probability_fair: number;
        probability_overpriced: number;
    };
    broker?: {
        office_name: string;
        trust_score: string;
        trust_grade: string;
    };
}

/**
 * 매물 비교 API 호출
 */
export async function compareProperties(landIds: number[]): Promise<CompareResponse> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${API_BASE_URL}/api/listings/lands/compare/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ land_ids: landIds }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '매물 비교 요청에 실패했습니다.');
    }

    return response.json();
}
