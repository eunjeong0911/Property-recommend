/**
 * LandList 컴포넌트
 * 
 * 매물 목록을 표시하는 컴포넌트
 * 
 * 주요 기능:
 * - 매물 4개씩 3줄로 총 12개 표시
 * - 페이지네이션 기능
 * - 매물 정보 표시 (ex. 월세 5,000만원/35만원 )
 * - 매물 선택 기능
 * 
 * 사용 컴포넌트:
 * - LandImage: 매물 사진 표시
 */

'use client';

import { useEffect, useState } from 'react';
import LandImage from './LandImage';
import { Land, LandFilterParams } from '../types/land';
import { fetchLands } from '../api/landApi';

interface LandListProps {
    filterParams?: LandFilterParams;
}

const ITEMS_PER_PAGE = 12; // 4개 x 3줄

export default function LandList({ filterParams }: LandListProps) {
    const [lands, setLands] = useState<Land[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState<number>(1);

    useEffect(() => {
        const loadLands = async () => {
            try {
                setLoading(true);
                const data = await fetchLands(filterParams);
                setLands(data);
                setError(null);
                setCurrentPage(1); // 필터 변경 시 첫 페이지로
            } catch (err) {
                console.error('Failed to fetch lands:', err);
                setError('매물 정보를 불러오는데 실패했습니다.');
            } finally {
                setLoading(false);
            }
        };

        loadLands();
    }, [filterParams]);

    // 페이지네이션 계산
    const totalPages = Math.ceil(lands.length / ITEMS_PER_PAGE);
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const currentLands = lands.slice(startIndex, endIndex);

    const handlePrevPage = () => {
        setCurrentPage(prev => Math.max(1, prev - 1));
    };

    const handleNextPage = () => {
        setCurrentPage(prev => Math.min(totalPages, prev + 1));
    };

    const handlePageClick = (page: number) => {
        setCurrentPage(page);
    };

    if (loading) {
        return (
            <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-visible min-h-[300px] flex items-center justify-center">
                <div className="text-slate-600 flex flex-col items-center gap-2">
                    <div className="w-8 h-8 border-4 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                    <p>매물 정보를 불러오는 중...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-visible min-h-[300px] flex items-center justify-center">
                <div className="text-red-500 text-center">
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    if (lands.length === 0) {
        return (
            <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-visible min-h-[300px] flex items-center justify-center">
                <div className="text-slate-600 text-center">
                    <p>조건에 맞는 매물이 없습니다.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 매물 목록 */}
            <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-visible">
                <div className="grid grid-cols-4 gap-6">
                    {currentLands.map((land) => (
                        <LandImage
                            key={land.id}
                            id={String(land.id)}
                            images={land.image ? [land.image] : undefined}
                            temperature={land.temperature}
                            price={land.price}
                        />
                    ))}
                </div>
            </div>

            {/* 세련된 페이지네이션 */}
            {totalPages > 1 && (
                <div className="flex flex-col items-center gap-4">
                    <div className="inline-flex items-center gap-1 p-2 rounded-2xl bg-slate-50 border border-slate-200 shadow-sm">
                        {/* 처음으로 버튼 */}
                        <button
                            onClick={() => handlePageClick(1)}
                            disabled={currentPage === 1}
                            className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-500 disabled:text-slate-300 disabled:cursor-not-allowed hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
                            title="처음으로"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                            </svg>
                        </button>

                        {/* 이전 버튼 */}
                        <button
                            onClick={handlePrevPage}
                            disabled={currentPage === 1}
                            className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-500 disabled:text-slate-300 disabled:cursor-not-allowed hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
                            title="이전"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                        </button>

                        {/* 구분선 */}
                        <div className="w-px h-6 bg-slate-200 mx-1"></div>

                        {/* 페이지 번호 */}
                        <div className="flex gap-1">
                            {(() => {
                                const currentGroup = Math.ceil(currentPage / 10);
                                const startPage = (currentGroup - 1) * 10 + 1;
                                const endPage = Math.min(currentGroup * 10, totalPages);
                                
                                const pages = [];
                                
                                if (startPage > 1) {
                                    pages.push(
                                        <button
                                            key="first"
                                            onClick={() => handlePageClick(1)}
                                            className="w-10 h-10 rounded-xl text-sm font-medium text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
                                        >
                                            1
                                        </button>
                                    );
                                    if (startPage > 2) {
                                        pages.push(
                                            <span key="dots-start" className="w-10 h-10 flex items-center justify-center text-slate-400 text-sm">...</span>
                                        );
                                    }
                                }
                                
                                for (let page = startPage; page <= endPage; page++) {
                                    pages.push(
                                        <button
                                            key={page}
                                            onClick={() => handlePageClick(page)}
                                            className={`w-10 h-10 rounded-xl text-sm font-semibold transition-all duration-200 ${
                                                currentPage === page
                                                    ? 'bg-slate-800 text-white shadow-sm'
                                                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'
                                            }`}
                                        >
                                            {page}
                                        </button>
                                    );
                                }
                                
                                if (endPage < totalPages) {
                                    if (endPage < totalPages - 1) {
                                        pages.push(
                                            <span key="dots-end" className="w-10 h-10 flex items-center justify-center text-slate-400 text-sm">...</span>
                                        );
                                    }
                                    pages.push(
                                        <button
                                            key="last"
                                            onClick={() => handlePageClick(totalPages)}
                                            className="w-10 h-10 rounded-xl text-sm font-medium text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
                                        >
                                            {totalPages}
                                        </button>
                                    );
                                }
                                
                                return pages;
                            })()}
                        </div>

                        {/* 구분선 */}
                        <div className="w-px h-6 bg-slate-200 mx-1"></div>

                        {/* 다음 버튼 */}
                        <button
                            onClick={handleNextPage}
                            disabled={currentPage === totalPages}
                            className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-500 disabled:text-slate-300 disabled:cursor-not-allowed hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
                            title="다음"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        </button>

                        {/* 끝으로 버튼 */}
                        <button
                            onClick={() => handlePageClick(totalPages)}
                            disabled={currentPage === totalPages}
                            className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-500 disabled:text-slate-300 disabled:cursor-not-allowed hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
                            title="끝으로"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                            </svg>
                        </button>
                    </div>

                    {/* 페이지 정보 */}
                    <div className="text-sm text-slate-500">
                        총 <span className="font-semibold text-slate-700">{lands.length}</span>개 매물 중{' '}
                        <span className="font-semibold text-blue-600">{currentPage}</span> / {totalPages} 페이지
                    </div>
                </div>
            )}
        </div>
    );
}
