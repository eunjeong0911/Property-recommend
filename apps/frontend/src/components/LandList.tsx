/**
 * LandList 컴포넌트
 * 
 * 매물 목록을 표시하는 컴포넌트
 * 
 * 주요 기능:
 * - 매물 4개씩 한줄로 목록 표시
 * - 매물 정보 표시 (ex. 월세 5,000만원/35만원 )
 * - 매물 선택 기능
 * 
 * 사용 컴포넌트:
 * - LandImage: 매물 사진 표시
 */

'use client';

import LandImage from './LandImage';

interface Land {
    id: string;
    image?: string;
    temperature: number;
    price: string;
}

interface LandListProps {
    lands?: Land[];
}

const MOCK_LANDS: Land[] = [
    { id: '1', temperature: 0.4, price: '월세 1,000 / 68' },
    { id: '2', temperature: 0.6, price: '월세 2,000 / 75' },
    { id: '3', temperature: 0.8, price: '월세 1,500 / 60' },
    { id: '4', temperature: 0.5, price: '월세 3,000 / 80' },
];

export default function LandList({ lands = MOCK_LANDS }: LandListProps) {
    return (
        <div className="py-6 overflow-visible">
            <div className="grid grid-cols-4 gap-10 max-w-7xl mx-auto">
                {lands.map((land) => (
                    <LandImage
                        key={land.id}
                        id={land.id}
                        temperature={land.temperature}
                        price={land.price}
                    />
                ))}
            </div>
        </div>
    );
}
