/**
 * MainPage
 * 
 * 메인 페이지
 * 
 * - Header.tsx (헤더)
 * - Chatbot.tsx (챗봇)
 * - PreferenceFilter.tsx (선호도 필터)
 * - Map.tsx (지도)
 * - LandListFilter.tsx (매물 목록)
 * - LandList.tsx (매물 목록)
 * - Temperature.tsx (온도)
 * - TemperatureList.tsx (온도 목록)
 * - Footer.tsx (푸터)
 */

'use client';

import { useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import LandListFilter from '@/components/LandListFilter';
import LandList from '@/components/LandList';
import useBackendUserGuard from '@/hooks/useBackendUserGuard';
import { LandFilterParams } from '@/types/land';

// 무거운 컴포넌트들을 lazy loading으로 변경하여 초기 로딩 성능 개선
const PreferenceFilter = dynamic(() => import('@/components/PreferenceFilter'), {
    ssr: false,
    loading: () => (
        <div className="flex justify-center w-full py-4" style={{ height: 132 }}>
            <div className="flex items-center gap-2 text-slate-600">
                <div className="w-6 h-6 border-3 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                <span>필터 불러오는 중...</span>
            </div>
        </div>
    )
});

const Map = dynamic(() => import('@/components/Map'), {
    ssr: false,
    loading: () => (
        <div className="relative w-[600px] h-[500px] rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-2xl overflow-hidden p-2 flex items-center justify-center">
            <div className="text-slate-600 text-center">
                <div className="w-12 h-12 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                <p>지도를 불러오는 중...</p>
            </div>
        </div>
    )
});

const TemperatureAnalysis = dynamic(() => import('@/components/TemperatureAnalysis'), {
    ssr: false,
    loading: () => (
        <div className="w-[280px] h-[500px] rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-2xl p-4 flex items-center justify-center">
            <div className="text-slate-600 text-center">
                <div className="w-8 h-8 border-3 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                <p className="text-sm">온도 분석 로딩 중...</p>
            </div>
        </div>
    )
});

export default function MainPage() {
    useBackendUserGuard();
    const [filterParams, setFilterParams] = useState<LandFilterParams>({});

    const handleFilterChange = useCallback((params: LandFilterParams) => {
        setFilterParams(params);
    }, []);

    return (
        <div className="max-w-5xl mx-auto px-4 space-y-8 mb-24">
            <section className="space-y-6">
                <div className="text-center space-y-2 pt-8">
                    <h2 className="text-3xl font-bold text-slate-800 flex items-center justify-center gap-2">
                        <span>나만의 좋은 지역 찾기</span>
                        <span className="text-2xl">✨</span>
                    </h2>
                    <p className="text-slate-600 text-sm">
                        필터를 선택하여 원하는 조건의 지역을 찾아보세요
                    </p>
                </div>
                <PreferenceFilter />
                <div className="flex justify-center gap-4">
                    <Map />
                    <TemperatureAnalysis />
                </div>
            </section>
            {/* 섹션 3: 매물 추천 리스트 */}
            <section className="space-y-6">
                <div className="text-center space-y-2">
                    <h2 className="text-3xl font-bold text-slate-800 flex items-center justify-center gap-2">
                        <span>매물 추천 리스트</span>
                        <span className="text-2xl">🏠</span>
                    </h2>
                    <p className="text-slate-600 text-sm">
                        회원님의 선호도에 맞는 매물을 추천해드립니다
                    </p>
                </div>
                <LandListFilter onFilterChange={handleFilterChange} />
                <LandList filterParams={filterParams} />
            </section>
        </div>
    );
}
