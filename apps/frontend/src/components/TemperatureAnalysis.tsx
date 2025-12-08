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
        <div className="w-[408px] h-[584px] mt-4 rounded-2xl border border-red-200/60 bg-gradient-to-b from-red-50/90 via-orange-50/90 to-amber-50/90 backdrop-blur-md shadow-lg p-4 flex flex-col relative overflow-hidden">
            {/* 배경 장식 */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-red-400/20 to-orange-400/20 rounded-full blur-3xl"></div>
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-amber-400/20 to-red-400/20 rounded-full blur-2xl"></div>
            
            {/* 헤더 */}
            <div className="relative z-10">
                <h3 className="text-lg font-bold bg-gradient-to-r from-red-600 via-orange-500 to-amber-500 bg-clip-text text-transparent mb-3 text-center flex items-center justify-center gap-2">
                    <span className="text-xl">🌡️</span>
                    지역 온도 분석
                </h3>
            </div>
            
            {/* 평균 온도 */}
            <div className="relative z-10 bg-gradient-to-r from-red-500/10 via-orange-500/10 to-amber-500/10 rounded-xl p-3 mb-3 text-center border border-red-200/40 backdrop-blur-sm">
                <div className="text-sm text-slate-600 font-medium">서울시 평균 온도</div>
                <div className="text-3xl font-bold bg-gradient-to-r from-red-500 via-orange-500 to-amber-500 bg-clip-text text-transparent">
                    {avgTemp}°
                </div>
                <div className="w-full h-1.5 bg-white/60 rounded-full mt-2 overflow-hidden">
                    <div 
                        className="h-full bg-gradient-to-r from-red-500 via-orange-500 to-amber-400 rounded-full transition-all duration-1000"
                        style={{ width: `${avgTemp}%` }}
                    ></div>
                </div>
            </div>

            {/* 온도 높은 지역 TOP 5 */}
            <div className="flex-1 overflow-hidden relative z-10">
                <div className="text-sm font-bold text-red-600 mb-2 flex items-center gap-1.5">
                    <span className="w-5 h-5 bg-gradient-to-r from-red-500 to-orange-500 rounded-full flex items-center justify-center text-white text-xs">🔥</span>
                    온도 높은 지역
                </div>
                <div className="space-y-1.5">
                    {topDistricts.map((district, idx) => (
                        <div 
                            key={district.name} 
                            className="flex items-center justify-between bg-white/60 hover:bg-white/80 rounded-lg px-3 py-2 border border-red-100/60 transition-all hover:shadow-md hover:scale-[1.02] cursor-pointer group"
                        >
                            <div className="flex items-center gap-2">
                                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                                    idx === 0 ? 'bg-gradient-to-r from-red-500 to-red-600' :
                                    idx === 1 ? 'bg-gradient-to-r from-orange-500 to-orange-600' :
                                    idx === 2 ? 'bg-gradient-to-r from-amber-500 to-amber-600' :
                                    'bg-slate-400'
                                }`}>
                                    {idx + 1}
                                </span>
                                <span className="text-sm font-semibold text-slate-700 group-hover:text-red-600 transition-colors">{district.name}</span>
                            </div>
                            <span className="text-sm font-bold px-2 py-0.5 rounded-full bg-gradient-to-r from-red-500 to-orange-500 text-white shadow-sm">
                                {district.temperature}°
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* 온도 낮은 지역 TOP 5 */}
            <div className="flex-1 overflow-hidden mt-3 relative z-10">
                <div className="text-sm font-bold text-blue-600 mb-2 flex items-center gap-1.5">
                    <span className="w-5 h-5 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white text-xs">❄️</span>
                    온도 낮은 지역
                </div>
                <div className="space-y-1.5">
                    {bottomDistricts.map((district, idx) => (
                        <div 
                            key={district.name} 
                            className="flex items-center justify-between bg-white/60 hover:bg-white/80 rounded-lg px-3 py-2 border border-blue-100/60 transition-all hover:shadow-md hover:scale-[1.02] cursor-pointer group"
                        >
                            <div className="flex items-center gap-2">
                                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                                    idx === 0 ? 'bg-gradient-to-r from-blue-500 to-blue-600' :
                                    idx === 1 ? 'bg-gradient-to-r from-cyan-500 to-cyan-600' :
                                    idx === 2 ? 'bg-gradient-to-r from-sky-500 to-sky-600' :
                                    'bg-slate-400'
                                }`}>
                                    {idx + 1}
                                </span>
                                <span className="text-sm font-semibold text-slate-700 group-hover:text-blue-600 transition-colors">{district.name}</span>
                            </div>
                            <span className="text-sm font-bold px-2 py-0.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-sm">
                                {district.temperature}°
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* 범례 */}
            <div className="mt-3 pt-3 border-t border-red-200/40 relative z-10">
                <div className="text-xs text-slate-600 text-center mb-2 font-medium">온도 범례</div>
                <div className="flex justify-center gap-2">
                    <div className="flex items-center gap-1 px-2 py-1 bg-white/60 rounded-full">
                        <div className="w-3 h-3 rounded-full bg-gradient-to-r from-blue-400 to-blue-500 shadow-sm"></div>
                        <span className="text-[10px] text-slate-600 font-medium">낮음</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-1 bg-white/60 rounded-full">
                        <div className="w-3 h-3 rounded-full bg-gradient-to-r from-green-400 to-emerald-500 shadow-sm"></div>
                        <span className="text-[10px] text-slate-600 font-medium">보통</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-1 bg-white/60 rounded-full">
                        <div className="w-3 h-3 rounded-full bg-gradient-to-r from-yellow-400 to-amber-500 shadow-sm"></div>
                        <span className="text-[10px] text-slate-600 font-medium">높음</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-1 bg-white/60 rounded-full">
                        <div className="w-3 h-3 rounded-full bg-gradient-to-r from-red-400 to-red-500 shadow-sm"></div>
                        <span className="text-[10px] text-slate-600 font-medium">매우높음</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
