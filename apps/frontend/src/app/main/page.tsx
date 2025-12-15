/**
 * MainPage - PropTech Chatbot Interface
 * 
 * 메인 페이지 - 2컬럼 레이아웃
 * 
 * - 좌측: 필터 패널 + 매물 리스트
 * - 우측: 챗봇 영역 (sticky 고정)
 */

'use client';

import { useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import LandListFilter from '@/components/LandListFilter';
import LandList from '@/components/LandList';
import useBackendUserGuard from '@/hooks/useBackendUserGuard';
import { LandFilterParams } from '@/types/land';

// Chatbot을 동적 import (SSR 비활성화)
const Chatbot = dynamic(() => import('@/components/Chatbot'), {
    ssr: false,
});

export default function MainPage() {
    useBackendUserGuard();
    const [filterParams, setFilterParams] = useState<LandFilterParams>({});
    const [recommendedLandIds, setRecommendedLandIds] = useState<number[]>([]);

    const handleFilterChange = useCallback((params: LandFilterParams) => {
        setFilterParams(params);
    }, []);

    const handleRecommendedLands = useCallback((landIds: number[]) => {
        setRecommendedLandIds(landIds);
    }, []);

    return (
        <div className="max-w-[1440px] mx-auto px-8 py-8">
            {/* 2컬럼 그리드 레이아웃 */}
            <div className="grid grid-cols-[1fr_480px] gap-8 isolate">
                {/* 좌측: 필터 + 매물 리스트 */}
                <main className="space-y-6 z-0">
                    {/* 매물 필터 */}
                    <LandListFilter onFilterChange={handleFilterChange} />

                    {/* 매물 리스트 */}
                    <LandList
                        filterParams={filterParams}
                        recommendedLandIds={recommendedLandIds}
                    />
                </main>

                {/* 우측: 챗봇 영역 (sticky 고정) */}
                <aside className="sticky top-24 h-fit max-h-[calc(100vh-7rem)] z-10">
                    <Chatbot onRecommendLands={handleRecommendedLands} />
                </aside>
            </div>
        </div>
    );
}
