// apps/frontend/src/components/ChatbotFilter.tsx
'use client';

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
        excluded_floors?: string[]
        direction?: string
        options?: string[]  // 세탁기, 에어컨 등 옵션
    }
    search_strategy?: string
}

interface ChatbotFilterProps {
    filterInfo: FilterInfo | null;
    onToggle?: () => void;
}

export default function ChatbotFilter({ filterInfo, onToggle }: ChatbotFilterProps) {
    const handleReset = () => {
        onToggle?.();
    };

    return (
        <div className="bg-white border border-[var(--color-border-light)] rounded-xl p-6 shadow-[var(--shadow-md)]">
            {/* 헤더 - LandListFilter와 동일한 스타일 */}
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-[var(--color-primary)]">
                    🤖 AI 챗봇 필터
                </h3>
                <div className="flex items-center gap-2">
                    {/* 일반 필터로 전환 버튼 */}
                    <button
                        onClick={onToggle}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[var(--color-primary)] border border-[var(--color-primary)] rounded-lg hover:bg-[var(--color-primary-light)] transition-colors"
                    >
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M2 2h12M4 6h8M6 10h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                        일반 필터
                    </button>

                    {/* 초기화 버튼 */}
                    <button
                        onClick={handleReset}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50 hover:border-red-400 transition-colors"
                    >
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="currentColor" strokeWidth="1.5" />
                            <path d="M10 6L6 10M6 6L10 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                        초기화
                    </button>
                </div>
            </div>

            {/* 필터 정보 표시 */}
            {filterInfo && filterInfo.details ? (
                <div className="space-y-4">
                    {/* 검색 조건 요약 */}
                    <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                        <p className="text-sm text-purple-700">{filterInfo.summary}</p>
                    </div>

                    {/* 필터 상세 - LandListFilter와 비슷한 그리드 레이아웃 */}
                    <div className="flex items-end gap-4 flex-wrap">
                        {/* 위치 */}
                        {filterInfo.details.location && (
                            <div className="flex-1 min-w-[120px] space-y-2">
                                <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                                    📍 위치
                                </label>
                                <div className="px-4 py-2.5 border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] bg-gray-50">
                                    {filterInfo.details.location}
                                </div>
                            </div>
                        )}

                        {/* 거래 유형 */}
                        {filterInfo.details.deal_type && (
                            <div className="flex-1 min-w-[100px] space-y-2">
                                <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                                    🏠 거래유형
                                </label>
                                <div className="px-4 py-2.5 border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] bg-gray-50">
                                    {filterInfo.details.deal_type}
                                </div>
                            </div>
                        )}

                        {/* 건물 유형 */}
                        {filterInfo.details.building_type && (
                            <div className="flex-1 min-w-[100px] space-y-2">
                                <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                                    🏢 건물용도
                                </label>
                                <div className="px-4 py-2.5 border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] bg-gray-50">
                                    {filterInfo.details.building_type}
                                </div>
                            </div>
                        )}

                        {/* 가격 조건 */}
                        {(filterInfo.details.max_deposit || filterInfo.details.max_rent) && (
                            <div className="flex-1 min-w-[140px] space-y-2">
                                <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                                    💰 가격조건
                                </label>
                                <div className="px-4 py-2.5 border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] bg-gray-50">
                                    {filterInfo.details.max_deposit && `보증금 ${filterInfo.details.max_deposit}`}
                                    {filterInfo.details.max_deposit && filterInfo.details.max_rent && ' / '}
                                    {filterInfo.details.max_rent && `월세 ${filterInfo.details.max_rent}`}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* 추가 조건들 - 태그 형태 */}
                    <div className="flex flex-wrap gap-2 pt-2">
                        {/* 방향 */}
                        {filterInfo.details.direction && (
                            <span className="px-3 py-1.5 text-xs bg-yellow-50 text-yellow-700 border border-yellow-200 rounded-full">
                                ☀️ {filterInfo.details.direction}
                            </span>
                        )}

                        {/* 시설 */}
                        {filterInfo.details.facilities?.map((facility, idx) => (
                            <span key={`fac-${idx}`} className="px-3 py-1.5 text-xs bg-cyan-50 text-cyan-700 border border-cyan-200 rounded-full">
                                🎯 {facility}
                            </span>
                        ))}

                        {/* 옵션 */}
                        {filterInfo.details.options?.map((option, idx) => (
                            <span key={`opt-${idx}`} className="px-3 py-1.5 text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full">
                                🔧 {option}
                            </span>
                        ))}

                        {/* 제외 조건 */}
                        {filterInfo.details.excluded_floors?.map((floor, idx) => (
                            <span key={`ex-${idx}`} className="px-3 py-1.5 text-xs bg-red-50 text-red-700 border border-red-200 rounded-full">
                                🚫 {floor} 제외
                            </span>
                        ))}

                        {/* 스타일 */}
                        {filterInfo.details.style?.map((s, idx) => (
                            <span key={`sty-${idx}`} className="px-3 py-1.5 text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded-full">
                                ✨ {s}
                            </span>
                        ))}
                    </div>
                </div>
            ) : (
                <div className="p-8 text-center text-gray-500">
                    <p>챗봇과 대화하여 필터 정보를 생성하세요.</p>
                </div>
            )}
        </div>
    );
}
