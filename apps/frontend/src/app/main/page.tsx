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

import dynamic from 'next/dynamic';
import LandListFilter from '@/components/LandListFilter';
import LandList from '@/components/LandList';

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
        <div className="relative w-full h-[450px] rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-2xl overflow-hidden p-2 flex items-center justify-center">
            <div className="text-slate-600 text-center">
                <div className="w-12 h-12 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                <p>지도를 불러오는 중...</p>
            </div>
        </div>
    )
});

export default function MainPage() {
    return (
        <div className="max-w-5xl mx-auto px-4 space-y-8 mb-24">
            <PreferenceFilter />
            <Map />
            <LandListFilter />
            <LandList />
        </div>
    );
}