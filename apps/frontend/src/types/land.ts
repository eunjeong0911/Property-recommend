export interface Land {
    id: number;
    title: string;
    image?: string;
    images?: string[];
    temperature: number;
    deposit: number;
    monthly_rent: number;
    price: string; // Formatted price from backend
    deal_type?: string; // 거래 유형 (월세, 전세 등)
    region?: string;
    transaction_type?: string;
    building_type?: string;
    land_num?: string;
    address?: string;
    floor?: string;
    room_count?: string;
    area_supply?: string;
    area_exclusive?: string;
    direction?: string;
    parking?: string;
    move_in_date?: string;
    maintenance_fee?: string;
    heating_method?: string;
    elevator?: string;
    description?: string;
    additional_options?: string;
    jeonse_loan?: string;        // 전세자금대출
    move_in_report?: string;     // 전입신고 여부
    approval_date?: string;      // 사용승인일
    trade_info?: any;            // 거래 정보 JSON

    // 가격 예측 정보
    price_prediction?: {
        prediction_class: number;
        prediction_label: string;
        prediction_label_korean: string;
        probability_underpriced: number;
        probability_fair: number;
        probability_overpriced: number;
    };

    // 레이더 차트 데이터
    radar_chart_data?: {
        building_age: number;        // 건물연식 (0-100)
        options: number;              // 옵션 충실도 (0-100)
        security: number;             // 보안 수준 (0-100)
        space_efficiency: number;     // 공간 효율성 (0-100)
        transportation: number;       // 교통 접근성 (0-100)
    };

    // 중개업소 정보 (agent_info 대신 broker 사용)
    broker?: {
        id: number;
        office_name?: string;
        representative?: string;
        phone?: string;
        address?: string;
        registration_number?: string;
        trust_score?: 'A' | 'B' | 'C' | null;
        trust_grade?: string;
        trust_score_updated_at?: string | null;
    };
}

export interface LandFilterParams {
    region?: string;
    dong?: string;
    transaction_type?: string;
    building_type?: string;
    search?: string;
}
