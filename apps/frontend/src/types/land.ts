export interface Land {
    id: number;
    title: string;
    image?: string;
    images?: string[];
    temperature: number;
    deposit: number;
    monthly_rent: number;
    price: string; // Formatted price from backend
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
    agent_info?: {
        name?: string;
        phone?: string;
        representative?: string;
        address?: string;
    };
}

export interface LandFilterParams {
    region?: string;
    transaction_type?: string;
    building_type?: string;
    search?: string;
}
