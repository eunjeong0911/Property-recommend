/**
 * MainPage - PropTech Chatbot Interface
 * 
 * 메인 페이지 - 2컬럼 레이아웃
 * 
 * - 좌측: 필터 패널 + 매물 리스트
 * - 우측: 챗봇 영역 (sticky 고정)
 * 
 * ★ 핵심: 
 * - 일반 필터: LandListFilter + 일반 LandList (사용자 직접 필터링)
 * - 챗봇 필터: ChatbotFilter + 챗봇 LandList (AI 추천 매물)
 * - 두 리스트는 완전히 분리되어 독립적으로 동작
 */

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import LandListFilter from '@/components/LandListFilter';
import ChatbotFilter from '@/components/ChatbotFilter';
import LandList from '@/components/LandList';
import useBackendUserGuard from '@/hooks/useBackendUserGuard';
import { LandFilterParams, Land } from '@/types/land';
import { fetchLandsByIds, fetchLandsByFilter } from '@/api/landApi';

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

// 가격 문자열에서 숫자 추출 (예: "3000만원" -> 3000)
const parsePrice = (priceStr?: string): number | undefined => {
    if (!priceStr) return undefined;
    const match = priceStr.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : undefined;
};

export default function MainPage() {
    useBackendUserGuard();
    
    // ★★★ 일반 필터용 상태 (사용자 직접 필터링) ★★★
    const [filterParams, setFilterParams] = useState<LandFilterParams>({});
    
    // ★★★ 챗봇 필터용 상태 (AI 추천) ★★★
    const [chatbotFilterInfo, setChatbotFilterInfo] = useState<FilterInfo | null>(null);
    const [chatbotProperties, setChatbotProperties] = useState<Land[]>([]);
    const [showChatbotFilter, setShowChatbotFilter] = useState(false);
    const [isLoadingChatbotLands, setIsLoadingChatbotLands] = useState(false);
    
    // 이전 필터 정보를 추적하여 불필요한 API 호출 방지
    const prevFilterRef = useRef<string>('');

    // 컴포넌트 마운트 시 sessionStorage에서 필터 로드
    useEffect(() => {
        const savedFilter = loadFilterFromStorage();
        if (Object.keys(savedFilter).length > 0) {
            setFilterParams(savedFilter);
        }
    }, []);

    // ★★★ 핵심: ChatbotFilter 조건이 변경될 때마다 실시간으로 매물 조회 ★★★
    useEffect(() => {
        // 챗봇 필터 모드가 아니면 스킵
        if (!showChatbotFilter) return;
        
        // 필터 정보가 없으면 스킵
        if (!chatbotFilterInfo?.details) {
            console.log('[page.tsx] ⚠️ 필터 정보 없음 - 스킵');
            return;
        }

        const details = chatbotFilterInfo.details;
        
        // 필터 조건이 하나도 없으면 스킵
        if (!details.location && !details.deal_type && !details.building_type) {
            console.log('[page.tsx] ⚠️ 필터 조건 없음 - 스킵');
            return;
        }

        // 필터 변경 감지 (JSON 문자열로 비교)
        const currentFilterStr = JSON.stringify(details);
        if (prevFilterRef.current === currentFilterStr) {
            console.log('[page.tsx] ⏭️ 필터 변경 없음 - 스킵');
            return;
        }
        prevFilterRef.current = currentFilterStr;

        console.log('[page.tsx] 🔥 ChatbotFilter 조건 변경 감지! 실시간 검색 시작:', details);

        const fetchFilteredLands = async () => {
            setIsLoadingChatbotLands(true);
            
            try {
                // 가격 문자열을 숫자로 변환
                const maxDeposit = parsePrice(details.max_deposit);
                const maxRent = parsePrice(details.max_rent);

                const lands = await fetchLandsByFilter({
                    location: details.location,
                    deal_type: details.deal_type,
                    building_type: details.building_type,
                    max_deposit: maxDeposit,
                    max_rent: maxRent
                });

                console.log('[page.tsx] ✅ 실시간 매물 조회 완료:', lands.length, '개');
                setChatbotProperties(lands);
            } catch (error) {
                console.error('[page.tsx] ❌ 실시간 매물 조회 실패:', error);
                setChatbotProperties([]);
            } finally {
                setIsLoadingChatbotLands(false);
            }
        };

        fetchFilteredLands();
    }, [chatbotFilterInfo, showChatbotFilter]);

    const handleFilterChange = useCallback((params: LandFilterParams) => {
        setFilterParams(params);
    }, []);

    // 챗봇에서 필터 정보와 매물 데이터 받기
    const handleChatbotRecommend = useCallback(async (data: ChatbotRecommendData) => {
        console.log('[handleChatbotRecommend] 📥 데이터 수신:', {
            landIds: data.landIds?.length,
            filterInfo: data.filterInfo?.summary,
            properties: data.properties?.length
        });
        
        // ★★★ 필터 정보 업데이트 → useEffect가 자동으로 매물 조회 ★★★
        setChatbotFilterInfo(data.filterInfo);
        
        // 챗봇 필터 모드 자동 활성화
        setShowChatbotFilter(true);

        // RAG에서 properties가 있으면 우선 사용 (더 정확한 결과)
        if (data.properties && data.properties.length > 0) {
            console.log('[handleChatbotRecommend] ✅ RAG에서 properties 받음:', data.properties.length, '개');

            // 챗봇 응답의 properties에서 ID 추출
            const propertyIds = data.properties
                .slice(0, 20)
                .map((p: any) => p.id || p.land_num)
                .filter(Boolean);

            if (propertyIds.length > 0) {
                try {
                    // 백엔드 API로 완전한 Land 데이터 조회
                    const fullLandData = await fetchLandsByIds(propertyIds);
                    console.log('[handleChatbotRecommend] ✅ 완전한 Land 데이터:', fullLandData.length, '개');
                    
                    if (fullLandData.length > 0) {
                        setChatbotProperties(fullLandData);
                        // 이미 데이터가 있으므로 prevFilterRef 업데이트하여 중복 호출 방지
                        if (data.filterInfo?.details) {
                            prevFilterRef.current = JSON.stringify(data.filterInfo.details);
                        }
                        return;
                    }
                } catch (error) {
                    console.error('[handleChatbotRecommend] ❌ Land 데이터 조회 실패:', error);
                }
            }
        }
        
        // RAG 결과가 없으면 useEffect에서 자동으로 API 호출됨
        console.log('[handleChatbotRecommend] ⚠️ RAG 결과 없음 → useEffect에서 API 호출 예정');
    }, []);

    // 챗봇 대화 시작 시 - 더 이상 자동으로 필터 모드 전환하지 않음
    // 사용자가 직접 토글하거나, 챗봇이 추천 결과를 줄 때만 전환
    const handleChatStart = useCallback(() => {
        // 아무것도 하지 않음 - 사용자가 직접 토글하도록
        console.log('[handleChatStart] 챗봇 대화 시작 (필터 모드 유지)');
    }, []);

    // 챗봇 필터 토글
    const handleToggleChatbotFilter = useCallback(() => {
        setShowChatbotFilter((prev: boolean) => !prev);
    }, []);

    return (
        <div className="max-w-[1440px] mx-auto px-8 py-8">
            {/* 2컬럼 그리드 레이아웃 - 반반 */}
            <div className="grid grid-cols-2 gap-8 isolate">
                {/* 좌측: 필터 + 매물 리스트 */}
                <main className="space-y-6 z-0">
                    {/* ★★★ 챗봇 필터 모드일 때 ★★★ */}
                    {showChatbotFilter ? (
                        <>
                            {/* 챗봇 필터 UI */}
                            <ChatbotFilter
                                filterInfo={chatbotFilterInfo}
                                onToggle={handleToggleChatbotFilter}
                            />
                            
                            {/* 챗봇 추천 매물 리스트 (별도 데이터 소스) */}
                            <LandList
                                chatbotProperties={chatbotProperties}
                                showChatbotFilter={true}
                                isLoading={isLoadingChatbotLands}
                            />
                        </>
                    ) : (
                        <>
                            {/* ★★★ 일반 필터 모드일 때 ★★★ */}
                            {/* 일반 필터 UI */}
                            <LandListFilter
                                onFilterChange={handleFilterChange}
                                chatbotFilterInfo={chatbotFilterInfo}
                                onToggleChatbotFilter={handleToggleChatbotFilter}
                            />
                            
                            {/* 일반 매물 리스트 (API 필터링) */}
                            <LandList
                                filterParams={filterParams}
                                showChatbotFilter={false}
                            />
                        </>
                    )}
                </main>

                {/* 우측: 챗봇 영역 (sticky 고정) */}
                <aside className="sticky top-24 h-fit max-h-[calc(100vh-7rem)] z-10">
                    <Chatbot
                        onChatbotRecommend={handleChatbotRecommend}
                        onChatStart={handleChatStart}
                    />
                </aside>
            </div>
        </div>
    );
}
