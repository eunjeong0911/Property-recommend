/**
 * TemperatureAnalysis 컴포넌트
 * 
 * 서울시 구별 온도 분석 정보를 표시하는 컴포넌트
 */

'use client';

import { useMemo } from 'react';
import { seoulDistricts, getTemperatureColor } from '../mapdata/seoulDistricts';

export default function TemperatureAnalysis() {
    // 온도 기준 정렬된 구 목록
    const sortedDistricts = useMemo(() => {
        return [...seoulDistricts].sort((a, b) => b.temperature - a.temperature);
    }, []);

    const topDistricts = sortedDistricts.slice(0, 5);
    const bottomDistricts = sortedDistricts.slice(-5).reverse();

    const avgTemp = useMemo(() => {
        const sum = seoulDistricts.reduce((acc, d) => acc + d.temperature, 0);
        return Math.round(sum / seoulDistricts.length);
    }, []);

    return (
        <div className="w-[408px] h-[584px] mt-4 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-2xl p-4 flex flex-col">
            <h3 className="text-lg font-bold text-slate-800 mb-3 text-center">
                🌡️ 지역 온도 분석
            </h3>
            
            {/* 평균 온도 */}
            <div className="bg-white/60 rounded-xl p-3 mb-3 text-center">
                <div className="text-sm text-slate-600">서울시 평균 온도</div>
                <div className="text-2xl font-bold" style={{ color: getTemperatureColor(avgTemp) }}>
                    {avgTemp}°
                </div>
            </div>

            {/* 온도 높은 지역 TOP 5 */}
            <div className="flex-1 overflow-hidden">
                <div className="text-sm font-semibold text-slate-700 mb-2">🔥 온도 높은 지역</div>
                <div className="space-y-1.5">
                    {topDistricts.map((district, idx) => (
                        <div key={district.name} className="flex items-center justify-between bg-white/40 rounded-lg px-3 py-1.5">
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-slate-500 w-4">{idx + 1}</span>
                                <span className="text-sm font-medium text-slate-700">{district.name}</span>
                            </div>
                            <span className="text-sm font-bold" style={{ color: getTemperatureColor(district.temperature) }}>
                                {district.temperature}°
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* 온도 낮은 지역 TOP 5 */}
            <div className="flex-1 overflow-hidden mt-3">
                <div className="text-sm font-semibold text-slate-700 mb-2">❄️ 온도 낮은 지역</div>
                <div className="space-y-1.5">
                    {bottomDistricts.map((district, idx) => (
                        <div key={district.name} className="flex items-center justify-between bg-white/40 rounded-lg px-3 py-1.5">
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-slate-500 w-4">{idx + 1}</span>
                                <span className="text-sm font-medium text-slate-700">{district.name}</span>
                            </div>
                            <span className="text-sm font-bold" style={{ color: getTemperatureColor(district.temperature) }}>
                                {district.temperature}°
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* 범례 */}
            <div className="mt-3 pt-3 border-t border-white/40">
                <div className="text-xs text-slate-600 text-center mb-2">온도 범례</div>
                <div className="flex justify-center gap-1">
                    <div className="flex items-center gap-0.5">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3B82F6' }}></div>
                        <span className="text-[10px] text-slate-500">낮음</span>
                    </div>
                    <div className="flex items-center gap-0.5">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#10B981' }}></div>
                        <span className="text-[10px] text-slate-500">보통</span>
                    </div>
                    <div className="flex items-center gap-0.5">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#EAB308' }}></div>
                        <span className="text-[10px] text-slate-500">높음</span>
                    </div>
                    <div className="flex items-center gap-0.5">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#EF4444' }}></div>
                        <span className="text-[10px] text-slate-500">매우높음</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
