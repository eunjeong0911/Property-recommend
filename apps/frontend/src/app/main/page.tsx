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

import PreferenceFilter from '@/components/PreferenceFilter';
import Map from '@/components/Map';
import LandListFilter from '@/components/LandListFilter';
import LandList from '@/components/LandList';

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