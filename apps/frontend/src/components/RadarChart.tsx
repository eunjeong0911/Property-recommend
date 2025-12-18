/**
 * RadarChart 컴포넌트
 * 
 * 매물의 5가지 평가 지표를 오각형 레이더 차트로 시각화합니다.
 * 
 * 평가 지표:
 * - 주거 쾌적성 (comfort)
 * - 건물 상태 (building)
 * - 편의시설 (amenities)
 * - 관리 효율성 (management)
 * - 안전/보안 (safety)
 */

'use client';

import React from 'react';
import {
    Radar,
    RadarChart as RechartsRadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Tooltip,
} from 'recharts';

interface RadarChartData {
    comfort: number;      // 주거 쾌적성
    building: number;     // 건물 상태
    amenities: number;    // 편의시설
    management: number;   // 관리 효율성
    safety: number;       // 안전/보안
}

interface RadarChartProps {
    data: RadarChartData;
}

export default function RadarChart({ data }: RadarChartProps) {
    // 디버깅용 로그
    console.log('RadarChart data:', data);

    // 데이터 유효성 검사
    if (!data || typeof data !== 'object') {
        console.error('RadarChart: Invalid data', data);
        return (
            <div className="w-full h-[300px] flex items-center justify-center text-slate-500">
                <p>차트 데이터를 불러올 수 없습니다.</p>
            </div>
        );
    }

    // 레이더 차트용 데이터 변환
    const chartData = [
        { subject: '주거 쾌적성', value: data.comfort || 0, fullMark: 100 },
        { subject: '건물 상태', value: data.building || 0, fullMark: 100 },
        { subject: '편의시설', value: data.amenities || 0, fullMark: 100 },
        { subject: '관리 효율성', value: data.management || 0, fullMark: 100 },
        { subject: '안전/보안', value: data.safety || 0, fullMark: 100 },
    ];

    // 커스텀 툴팁
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-white px-4 py-2 rounded-lg shadow-lg border border-purple-200">
                    <p className="text-sm font-semibold text-slate-800">{payload[0].payload.subject}</p>
                    <p className="text-sm text-[#16375B] font-bold">{payload[0].value}점</p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="w-full h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
                <RechartsRadarChart data={chartData}>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fill: '#475569', fontSize: 12, fontWeight: 500 }}
                    />
                    <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={{ fill: '#94a3b8', fontSize: 10 }}
                    />
                    <Radar
                        name="평가 점수"
                        dataKey="value"
                        stroke="#16375B"
                        fill="#16375B"
                        fillOpacity={0.6}
                        strokeWidth={2}
                    />
                    <Tooltip content={<CustomTooltip />} />
                </RechartsRadarChart>
            </ResponsiveContainer>
        </div>
    );
}
