/**
 * ChatbotList 컴포넌트 - 챗봇 추천 매물 전용 리스트
 * 
 * LandList에서 챗봇 관련 코드를 분리하여 독립적으로 동작
 * 
 * 주요 기능:
 * - AI 추천 매물 순위 표시
 * - 찜 버튼
 * - 페이지네이션
 * - 일반 리스트로 전환 버튼
 */

'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Land } from '../types/land';
import { fetchWishlist, addWishlist, removeWishlist } from '../api/wishlistApi';
import { useSession } from 'next-auth/react';

interface ChatbotListProps {
    chatbotProperties: Land[];
    isLoading?: boolean;
    onToggle?: () => void;  // 일반 리스트로 전환
}

const ITEMS_PER_PAGE = 5;

export default function ChatbotList({ chatbotProperties, isLoading, onToggle }: ChatbotListProps) {
    const router = useRouter();
    const { data: session } = useSession();
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [currentPageGroup, setCurrentPageGroup] = useState<number>(0);
    const [favorites, setFavorites] = useState<Set<number>>(new Set());

    // 챗봇 매물이 변경되면 페이지 리셋
    useEffect(() => {
        setCurrentPage(1);
        setCurrentPageGroup(0);
    }, [chatbotProperties]);

    // 로그인된 사용자 기준으로 DB에 있는 찜 목록 불러오기
    useEffect(() => {
        const loadFavoritesFromServer = async () => {
            if (!session) {
                setFavorites(new Set());
                return;
            }
            try {
                const wishlist = await fetchWishlist();
                const ids = wishlist.map(item => Number(item.listing_id));
                setFavorites(new Set(ids));
            } catch (err) {
                console.error('Failed to fetch wishlist:', err);
            }
        };

        loadFavoritesFromServer();
    }, [session]);

    // 페이지네이션 계산
    const totalPages = Math.ceil(chatbotProperties.length / ITEMS_PER_PAGE);
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const currentLands = chatbotProperties.slice(startIndex, endIndex);

    // 페이지 그룹 계산 (10개씩)
    const PAGES_PER_GROUP = 10;
    const totalPageGroups = Math.ceil(totalPages / PAGES_PER_GROUP);
    const startPage = currentPageGroup * PAGES_PER_GROUP + 1;
    const endPage = Math.min(startPage + PAGES_PER_GROUP - 1, totalPages);
    const visiblePages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);

    const handlePageClick = (page: number) => {
        setCurrentPage(page);
    };

    const handlePrevGroup = () => {
        if (currentPageGroup > 0) {
            setCurrentPageGroup(currentPageGroup - 1);
            setCurrentPage((currentPageGroup - 1) * PAGES_PER_GROUP + 1);
        }
    };

    const handleNextGroup = () => {
        if (currentPageGroup < totalPageGroups - 1) {
            setCurrentPageGroup(currentPageGroup + 1);
            setCurrentPage((currentPageGroup + 1) * PAGES_PER_GROUP + 1);
        }
    };

    const toggleFavorite = async (landId: number, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!session) {
            router.push('/login');
            return;
        }
        const isFavorite = favorites.has(landId);

        // 낙관적 업데이트
        setFavorites(prev => {
            const next = new Set(prev);
            if (isFavorite) {
                next.delete(landId);
            } else {
                next.add(landId);
            }
            return next;
        });

        try {
            if (isFavorite) {
                await removeWishlist(landId);
            } else {
                await addWishlist(landId);
            }
        } catch (error) {
            console.error('Failed to toggle wishlist:', error);
            // 실패 시 롤백
            setFavorites(prev => {
                const next = new Set(prev);
                if (isFavorite) {
                    next.add(landId);
                } else {
                    next.delete(landId);
                }
                return next;
            });
        }
    };

    const handleCardClick = (landId: number) => {
        router.push(`/landDetail/${landId}`);
    };

    // 로딩 상태
    if (isLoading) {
        return (
            <div className="bg-white border border-[var(--color-border-light)] rounded-xl p-8 shadow-[var(--shadow-md)] min-h-[400px] flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-[var(--color-text-secondary)]">AI가 매물을 찾고 있습니다...</p>
                </div>
            </div>
        );
    }

    // 매물 없음
    if (chatbotProperties.length === 0) {
        return (
            <div className="bg-white border border-[var(--color-border-light)] rounded-xl p-8 shadow-[var(--shadow-md)] min-h-[400px] flex items-center justify-center">
                <div className="text-center max-w-md">
                    <div className="mb-6 flex justify-center">
                        <div className="w-20 h-20 rounded-full bg-purple-100 flex items-center justify-center">
                            <span className="text-4xl">🤖</span>
                        </div>
                    </div>
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                        AI 추천 매물이 없습니다
                    </h3>
                    <p className="text-sm text-[var(--color-text-secondary)] mb-6">
                        챗봇에게 원하는 조건을 말씀해주세요<br />
                        맞춤 매물을 추천해드릴게요
                    </p>
                    {onToggle && (
                        <button
                            onClick={onToggle}
                            className="px-4 py-2 text-sm font-medium text-[var(--color-primary)] border border-[var(--color-primary)] rounded-lg hover:bg-[var(--color-primary-light)] transition-colors"
                        >
                            일반 매물 보기
                        </button>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="bg-white border border-[var(--color-border-light)] rounded-xl p-6 shadow-[var(--shadow-md)]">
                {/* 헤더 */}
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-purple-600">
                        🤖 AI 추천 매물
                    </h3>
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-[var(--color-text-tertiary)]">
                            총 {chatbotProperties.length}개
                        </span>
                        {onToggle && (
                            <button
                                onClick={onToggle}
                                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[var(--color-primary)] border border-[var(--color-primary)] rounded-lg hover:bg-[var(--color-primary-light)] transition-colors"
                            >
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                </svg>
                                일반 리스트
                            </button>
                        )}
                    </div>
                </div>

                {/* 매물 카드 리스트 */}
                <div className="space-y-4">
                    {currentLands.map((land, index) => (
                        <div
                            key={land.id}
                            onClick={() => handleCardClick(land.id)}
                            className="flex gap-4 p-4 border border-purple-200 rounded-lg hover:border-purple-400 hover:shadow-[var(--shadow-lg)] transition-all cursor-pointer property-card-animate bg-gradient-to-r from-purple-50 to-white"
                            style={{ animationDelay: `${index * 50}ms` }}
                        >
                            {/* 썸네일 이미지 */}
                            <div className="relative w-40 h-32 flex-shrink-0 bg-[var(--color-bg-secondary)] rounded-lg overflow-hidden">
                                {/* 순위 배지 */}
                                <div className="absolute top-2 left-2 z-10 w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
                                    <span className="text-white font-bold text-sm">{startIndex + index + 1}</span>
                                </div>
                                {land.image ? (
                                    <Image
                                        src={land.image}
                                        alt={`매물 ${land.id}`}
                                        fill
                                        className="object-cover"
                                    />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-[var(--color-text-tertiary)]">
                                        <svg width="48" height="48" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <circle cx="32" cy="32" r="32" fill="var(--color-bg-tertiary)" />
                                            <path d="M32 20L20 28V44H26V34H38V44H44V28L32 20Z" fill="var(--color-border-dark)" />
                                        </svg>
                                    </div>
                                )}
                            </div>

                            {/* 매물 정보 */}
                            <div className="flex-1 flex flex-col justify-between min-w-0">
                                <div>
                                    <h4 className="text-base font-semibold text-[var(--color-text-primary)] mb-2 truncate">
                                        {land.address || `매물 ${land.id}`}
                                    </h4>
                                    <p className="text-xl font-bold mb-1" style={{ color: '#16375B' }}>
                                        {land.price}
                                    </p>
                                    {(land.deal_type === '단기임대' || land.transaction_type === '단기임대') && (
                                        <p className="text-sm text-[var(--color-text-secondary)] mb-1">
                                            {land.deposit ? `보증금 ${land.deposit.toLocaleString()}만원` : ''}
                                            {land.deposit && land.monthly_rent ? ' / ' : ''}
                                            {land.monthly_rent ? `월세 ${land.monthly_rent.toLocaleString()}만원` : ''}
                                        </p>
                                    )}
                                    <div className="flex gap-3 mt-2 text-xs text-[var(--color-text-tertiary)]">
                                        <span>{land.transaction_type || '매매'}</span>
                                        <span>•</span>
                                        <span>{land.building_type || '아파트'}</span>
                                    </div>
                                </div>
                            </div>

                            {/* 찜 버튼 */}
                            <button
                                onClick={(e) => toggleFavorite(land.id, e)}
                                className="flex-shrink-0 w-10 h-10 rounded-full bg-white border border-[var(--color-border)] hover:border-purple-400 hover:bg-purple-50 flex items-center justify-center transition-all self-start"
                            >
                                <svg
                                    width="20"
                                    height="20"
                                    viewBox="0 0 24 24"
                                    fill={favorites.has(land.id) ? '#E53935' : 'none'}
                                    stroke={favorites.has(land.id) ? '#E53935' : 'var(--color-text-tertiary)'}
                                    strokeWidth="2"
                                    xmlns="http://www.w3.org/2000/svg"
                                >
                                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                                </svg>
                            </button>
                        </div>
                    ))}
                </div>

                {/* 페이지네이션 */}
                {totalPages > 1 && (
                    <div className="flex justify-center items-center gap-2 mt-8 pt-6 border-t border-[var(--color-border-light)]">
                        <button
                            onClick={handlePrevGroup}
                            disabled={currentPageGroup === 0}
                            className="px-3 py-2 rounded-lg text-sm font-medium text-[var(--color-text-secondary)] hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            ◀
                        </button>
                        <button
                            onClick={() => handlePageClick(Math.max(1, currentPage - 1))}
                            disabled={currentPage === 1}
                            className="px-3 py-2 rounded-lg text-sm font-medium text-[var(--color-text-secondary)] hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            이전
                        </button>
                        <div className="flex gap-1">
                            {visiblePages.map((page) => (
                                <button
                                    key={page}
                                    onClick={() => handlePageClick(page)}
                                    className={`w-10 h-10 rounded-lg text-sm font-semibold transition-all ${currentPage === page
                                        ? 'bg-purple-500 text-white shadow-[var(--shadow-md)]'
                                        : 'text-[var(--color-text-secondary)] hover:bg-purple-50'
                                        }`}
                                >
                                    {page}
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={() => handlePageClick(Math.min(totalPages, currentPage + 1))}
                            disabled={currentPage === totalPages}
                            className="px-3 py-2 rounded-lg text-sm font-medium text-[var(--color-text-secondary)] hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            다음
                        </button>
                        <button
                            onClick={handleNextGroup}
                            disabled={currentPageGroup === totalPageGroups - 1}
                            className="px-3 py-2 rounded-lg text-sm font-medium text-[var(--color-text-secondary)] hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            ▶
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
