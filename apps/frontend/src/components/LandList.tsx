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
            <div className="p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl overflow-visible min-h-[300px] flex items-center justify-center">
                <div className="text-slate-600 flex flex-col items-center gap-2">
                    <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                    <p>매물 정보를 불러오는 중...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl overflow-visible min-h-[300px] flex items-center justify-center">
                <div className="text-red-500 text-center">
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    if (lands.length === 0) {
        return (
            <div className="p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl overflow-visible min-h-[300px] flex items-center justify-center">
                <div className="text-slate-600 text-center">
                    <p>조건에 맞는 매물이 없습니다.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 매물 목록 */}
            <div className="p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl overflow-visible">
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

            {/* 페이지네이션 */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2">
                    {/* 이전 버튼 */}
                    <button
                        onClick={handlePrevPage}
                        disabled={currentPage === 1}
                        className={`px-4 py-2 rounded-lg font-medium transition-all ${
                            currentPage === 1
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-white text-blue-600 hover:bg-blue-50 shadow-md hover:shadow-lg'
                        }`}
                    >
                        이전
                    </button>

                    {/* 페이지 번호 (10개씩 묶어서 표시) */}
                    <div className="flex gap-2">
                        {(() => {
                            // 현재 페이지가 속한 그룹 계산 (1-10, 11-20, 21-30, ...)
                            const currentGroup = Math.ceil(currentPage / 10);
                            const startPage = (currentGroup - 1) * 10 + 1;
                            const endPage = Math.min(currentGroup * 10, totalPages);
                            
                            const pages = [];
                            
                            // 이전 그룹이 있으면 "..." 표시
                            if (startPage > 1) {
                                pages.push(
                                    <button
                                        key="prev-group"
                                        onClick={() => handlePageClick(startPage - 1)}
                                        className="w-10 h-10 rounded-lg font-medium bg-white text-slate-700 hover:bg-blue-50 shadow-md hover:shadow-lg transition-all"
                                    >
                                        ...
                                    </button>
                                );
                            }
                            
                            // 현재 그룹의 페이지들 표시
                            for (let page = startPage; page <= endPage; page++) {
                                pages.push(
                                    <button
                                        key={page}
                                        onClick={() => handlePageClick(page)}
                                        className={`w-10 h-10 rounded-lg font-medium transition-all ${
                                            currentPage === page
                                                ? 'bg-blue-600 text-white shadow-lg'
                                                : 'bg-white text-slate-700 hover:bg-blue-50 shadow-md hover:shadow-lg'
                                        }`}
                                    >
                                        {page}
                                    </button>
                                );
                            }
                            
                            // 다음 그룹이 있으면 "..." 표시
                            if (endPage < totalPages) {
                                pages.push(
                                    <button
                                        key="next-group"
                                        onClick={() => handlePageClick(endPage + 1)}
                                        className="w-10 h-10 rounded-lg font-medium bg-white text-slate-700 hover:bg-blue-50 shadow-md hover:shadow-lg transition-all"
                                    >
                                        ...
                                    </button>
                                );
                            }
                            
                            return pages;
                        })()}
                    </div>

                    {/* 다음 버튼 */}
                    <button
                        onClick={handleNextPage}
                        disabled={currentPage === totalPages}
                        className={`px-4 py-2 rounded-lg font-medium transition-all ${
                            currentPage === totalPages
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-white text-blue-600 hover:bg-blue-50 shadow-md hover:shadow-lg'
                        }`}
                    >
                        다음
                    </button>

                    {/* 페이지 정보 */}
                    <div className="ml-4 text-slate-600 font-medium">
                        {currentPage} / {totalPages} 페이지 (총 {lands.length}개)
                    </div>
                </div>
            )}
        </div>
    );
}
