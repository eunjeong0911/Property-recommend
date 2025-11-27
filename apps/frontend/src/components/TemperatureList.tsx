/**
 * TemperatureList 컴포넌트
 * 
 * 지역별 온도를 표시하는 컴포넌트
 * 
 * 주요 기능:
 * - 지역의 여러가지 온도 바 표시
 * 
 * 사용 컴포넌트:
 * - Temperature: 개별 온도 바 컴포넌트
 */

'use client';

import Temperature from './Temperature';

interface TemperatureData {
    label: string;
    value: number;
}

interface TemperatureListProps {
    temperatures?: TemperatureData[];
}

const DEFAULT_TEMPERATURES: TemperatureData[] = [
    { label: '대중교통', value: 0.8 },
    { label: '주변 공원', value: 0.6 },
    { label: '대학/직장 거리', value: 0.7 },
    { label: '편의시설', value: 0.9 },
    { label: '치안/안전', value: 0.5 },
];

export default function TemperatureList({ temperatures = DEFAULT_TEMPERATURES }: TemperatureListProps) {
    return (
        <div className="bg-white rounded-lg shadow-lg p-4 space-y-3">
            {temperatures.map((temp, index) => (
                <Temperature key={index} label={temp.label} value={temp.value} />
            ))}
        </div>
    );
}
