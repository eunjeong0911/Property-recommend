/**
 * MainPage - PropTech Chatbot Interface
 * 
 * 메인 페이지 - 2컬럼 레이아웃
 * 
 * - 좌측: 필터 패널 + 매물 리스트
 * - 우측: 챗봇 영역 (sticky 고정)
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import dynamic from 'next/dynamic';
import LandListFilter from '@/components/LandListFilter';
import ChatbotFilter from '@/components/ChatbotFilter';
import LandList from '@/components/LandList';
import useBackendUserGuard from '@/hooks/useBackendUserGuard';
import { LandFilterParams, Land } from '@/types/land';
import { fetchLandsByIds, fetchLandsByFilter, ChatbotFilterParams } from '@/api/landApi';

// Chatbot을 동적 import (SSR 비활성화)
const Chatbot = dynamic(() => import('@/components/Chatbot'), {
    ssr: false,
});

// FilterInfo 타입 정의 (Chatbot과 동일)
interface FilterInfo {
    summary: string
    details: {
        location?: string
        facilities?: string[]
        deal_type?: string
        building_type?: string
        max_deposit?: string
        max_rent?: string
        style?: string[]
    }
    search_strategy?: string
}

interface ChatbotRecommendData {
    landIds: number[]
    filterInfo: FilterInfo | null
    properties: any[]
}

// sessionStorage에서 필터 값 로드
const loadFilterFromStorage = (): LandFilterParams => {
    if (typeof window === 'undefined') return {};
    try {
        const saved = sessionStorage.getItem('landListFilter');
        if (!saved) return {};
        const parsed = JSON.parse(saved);
        return {
            region: parsed.selectedRegion || undefined,
            dong: parsed.selectedDong || undefined,
            transaction_type: parsed.selectedTransaction || undefined,
            building_type: parsed.selectedBuilding || undefined,
        };
    } catch {
        return {};
    }
};

export default function MainPage() {
    useBackendUserGuard();
    const [filterParams, setFilterParams] = useState<LandFilterParams>({});
    const [recommendedLandIds, setRecommendedLandIds] = useState<number[]>([]);
    const [chatbotFilterInfo, setChatbotFilterInfo] = useState<FilterInfo | null>(null);
    const [chatbotProperties, setChatbotProperties] = useState<any[]>([]);
    const [showChatbotFilter, setShowChatbotFilter] = useState(false);

    // 컴포넌트 마운트 시 sessionStorage에서 필터 로드
    useEffect(() => {
        const savedFilter = loadFilterFromStorage();
        if (Object.keys(savedFilter).length > 0) {
            setFilterParams(savedFilter);
        }
    }, []);

    // ★ 챗봇 필터 변경 시 실시간으로 매물 조회 (RAG 결과가 없을 때만 폴백)
    useEffect(() => {
        if (!showChatbotFilter || !chatbotFilterInfo?.details) return;

        // RAG에서 이미 properties를 제공한 경우 스킵 (Neo4j 기반 결과가 더 정확함)
        if (chatbotProperties.length > 0) {
            console.log('[page.tsx] ✅ RAG에서 제공한 매물 사용:', chatbotProperties.length, '개');
            return;
        }

        const details = chatbotFilterInfo.details;

        // 필터 조건이 하나라도 있을 때만 검색
        if (!details.location && !details.deal_type && !details.building_type) return;

        console.log('[page.tsx] 🔥 RAG 결과 없음 → 폴백 검색 시작:', details);

        const fetchFilteredLands = async () => {
            try {
                const lands = await fetchLandsByFilter({
                    location: details.location,
                    deal_type: details.deal_type,
                    building_type: details.building_type
                });

                console.log('[page.tsx] ✅ 폴백 매물 조회 완료:', lands.length, '개');

                if (lands.length > 0) {
                    setChatbotProperties(lands);
                }
            } catch (error) {
                console.error('[page.tsx] ❌ 폴백 매물 조회 실패:', error);
            }
        };

        fetchFilteredLands();
    }, [chatbotFilterInfo, showChatbotFilter, chatbotProperties.length]); // chatbotProperties.length 다시 추가

    const handleFilterChange = useCallback((params: LandFilterParams) => {
        setFilterParams(params);
    }, []);

    const handleRecommendedLands = useCallback((landIds: number[]) => {
        setRecommendedLandIds(landIds);
    }, []);

    // 챗봇에서 필터 정보와 매물 데이터 받기
    const handleChatbotRecommend = useCallback(async (data: ChatbotRecommendData) => {
        console.log('[handleChatbotRecommend] 📥 데이터 수신:', {
            landIds: data.landIds?.length,
            filterInfo: data.filterInfo?.summary,
            properties: data.properties?.length
        });

        setRecommendedLandIds(data.landIds);
        setChatbotFilterInfo(data.filterInfo);

        // ★★★ 핵심 수정: RAG에서 properties가 있으면 무조건 사용! ★★★
        if (data.properties && data.properties.length > 0) {
            console.log('[handleChatbotRecommend] ✅ RAG에서 properties 받음:', data.properties.length, '개');

            // 챗봇 응답의 properties에서 ID 추출 시도
            const propertyIds = data.properties
                .slice(0, 20)
                .map((p: any) => p.id || p.land_num)
                .filter(Boolean);

            console.log('[handleChatbotRecommend] 🔍 추출된 ID:', propertyIds);

            if (propertyIds.length > 0) {
                try {
                    // 백엔드 API로 완전한 Land 데이터 조회
                    const fullLandData = await fetchLandsByIds(propertyIds);
                    console.log('[handleChatbotRecommend] ✅ 완전한 Land 데이터 조회:', fullLandData.length, '개');
                    setChatbotProperties(fullLandData);
                } catch (error) {
                    console.error('[handleChatbotRecommend] ❌ 완전 데이터 조회 실패, 폴백:', error);
                    // 폴백: RAG 원본 데이터 사용
                    setChatbotProperties(data.properties.slice(0, 20));
                }
            } else {
                // ID 추출 실패해도 RAG 원본 데이터 사용!
                console.log('[handleChatbotRecommend] ⚠️ ID 추출 실패, RAG 원본 사용');
                setChatbotProperties(data.properties.slice(0, 20));
            }
        } else {
            console.log('[handleChatbotRecommend] ⚠️ RAG에서 properties 없음');
            // properties가 비어있을 때만 빈 배열
            // setChatbotProperties([]); // 이전 결과 유지하도록 주석 처리
        }
    }, []);

    // 챗봇 대화 시작 시 필터 모드 활성화
    const handleChatStart = useCallback(() => {
        setShowChatbotFilter(true);
    }, []);

    // 챗봇 필터 토글
    const handleToggleChatbotFilter = useCallback(() => {
        setShowChatbotFilter(prev => !prev);
    }, []);

    return (
        <div className="max-w-[1440px] mx-auto px-8 py-8">
            {/* 2컬럼 그리드 레이아웃 - 반반 */}
            <div className="grid grid-cols-2 gap-8 isolate">
                {/* 좌측: 필터 + 매물 리스트 */}
                <main className="space-y-6 z-0">
                    {/* 매물 필터 */}
                    {/* 매물 필터 영역 - 조건부 렌더링 */}
                    {showChatbotFilter ? (
                        <ChatbotFilter
                            filterInfo={chatbotFilterInfo}
                            onToggle={handleToggleChatbotFilter}
                        />
                    ) : (
                        <LandListFilter
                            onFilterChange={handleFilterChange}
                            chatbotFilterInfo={chatbotFilterInfo}
                            onToggleChatbotFilter={handleToggleChatbotFilter}
                        />
                    )}

                    {/* 매물 리스트 */}
                    <LandList
                        filterParams={filterParams}
                        recommendedLandIds={recommendedLandIds}
                        chatbotProperties={chatbotProperties}
                        showChatbotFilter={showChatbotFilter}
                    />
                </main>

                {/* 우측: 챗봇 영역 (sticky 고정) */}
                <aside className="sticky top-24 h-fit max-h-[calc(100vh-7rem)] z-10">
                    <Chatbot
                        onRecommendLands={handleRecommendedLands}
                        onChatbotRecommend={handleChatbotRecommend}
                        onChatStart={handleChatStart}
                    />
                </aside>
            </div>
        </div>
    );
}
