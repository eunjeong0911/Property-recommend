/**
 * LandDetail 컴포넌트
 * 
 * 매물 상세정보를 표시하는 컴포넌트
 * 
 * 주요 기능:
 * - 매물 기본 정보 (월세, 보증금, 관리비, 공급면적, 전용면적, 방/화장실 수, 주거 형태 등)
 * - 부동산 정보 (연락처, 전화번호, 주소)
 * - 상세내용 텍스트
 * 
 * - LandImage import
 */

'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Temperature from './Temperature';
import { useParticleEffect } from '../hooks/useParticleEffect';
import { Land } from '../types/land';
import { fetchLandById } from '../api/landApi';

interface LandDetailProps {
    landId: string;
}

export default function LandDetail({ landId }: LandDetailProps) {
    const [land, setLand] = useState<Land | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [liked, setLiked] = useState(false);
    const { triggerEffect } = useParticleEffect();

    useEffect(() => {
        const loadLand = async () => {
            try {
                setLoading(true);
                const data = await fetchLandById(landId);
                setLand(data);
            } catch (err) {
                console.error('Failed to fetch land details:', err);
                setError('매물 정보를 불러오는데 실패했습니다.');
            } finally {
                setLoading(false);
            }
        };

        if (landId) {
            loadLand();
        }
    }, [landId]);

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-[400px]">
                <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    if (error || !land) {
        return (
            <div className="flex justify-center items-center min-h-[400px] text-red-500">
                {error || '매물을 찾을 수 없습니다.'}
            </div>
        );
    }

    const images = land.images && land.images.length > 0
        ? land.images
        : [land.image || '/images/placeholder.jpg'];

    const handlePrevImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
        triggerEffect(e.currentTarget as HTMLElement);
    };

    const handleNextImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
        triggerEffect(e.currentTarget as HTMLElement);
    };

    const handleLike = (e: React.MouseEvent) => {
        e.stopPropagation();
        setLiked(!liked);
        triggerEffect(e.currentTarget as HTMLElement);
    };

    return (
        <div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                {/* 왼쪽: 이미지 */}
                <div>
                    <div className="relative aspect-[4/3] bg-gray-200 rounded-lg overflow-hidden group">
                        <Image
                            src={images[currentImageIndex]}
                            alt={land.title}
                            fill
                            sizes="(max-width: 768px) 100vw, 50vw"
                            className="object-cover"
                        />

                        {/* 찜하기 버튼 */}
                        <button
                            onClick={handleLike}
                            className="absolute top-4 right-4 hover:scale-110 transition-transform z-10"
                        >
                            <Image
                                src={liked ? '/icons/whish_on.png' : '/icons/whish_off.png'}
                                alt="찜하기"
                                width={48}
                                height={48}
                            />
                        </button>

                        {/* 이전/다음 버튼 */}
                        {images.length > 1 && (
                            <>
                                <button
                                    onClick={handlePrevImage}
                                    className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full w-10 h-10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10 text-xl"
                                >
                                    ‹
                                </button>
                                <button
                                    onClick={handleNextImage}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full w-10 h-10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10 text-xl"
                                >
                                    ›
                                </button>
                            </>
                        )}

                        {/* 이미지 카운터 */}
                        <div className="absolute bottom-4 right-4 bg-black/60 text-white px-3 py-1 rounded-full text-sm">
                            {currentImageIndex + 1} / {images.length}
                        </div>
                    </div>

                    {/* 부동산 정보 */}
                    <div className="mt-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl p-6">
                        <h3 className="text-lg font-bold mb-4 text-slate-800">부동산 정보</h3>

                        {/* 온도 바 */}
                        <div className="mb-6">
                            <Temperature label="부동산 온도" value={land.temperature} />
                        </div>

                        <div className="space-y-3">
                            <div className="flex items-center gap-2">
                                <span className="w-20 text-gray-600 text-sm">중개사무소</span>
                                <p className="font-medium text-slate-800">{land.agent_info?.name || '-'}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-20 text-gray-600 text-sm">전화번호</span>
                                <p className="font-medium text-slate-800">{land.agent_info?.phone || '-'}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-20 text-gray-600 text-sm">대표자</span>
                                <p className="font-medium text-slate-800">{land.agent_info?.representative || '-'}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-20 text-gray-600 text-sm">주소</span>
                                <p className="font-medium text-slate-800">{land.agent_info?.address || '-'}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 오른쪽: 정보 */}
                <div className="flex flex-col">
                    {/* 가격 정보 */}
                    <div className="mb-6">
                        <h1 className="text-3xl font-bold text-slate-800">{land.price}</h1>
                    </div>

                    {/* 매물 정보 */}
                    <div className="rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl p-6 flex-1">
                        <h3 className="text-lg font-bold mb-4 text-slate-800">매물 상세 정보</h3>
                        <div className="space-y-3">
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">매물번호</span>
                                <p className="font-medium text-slate-800">{land.land_num || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">지번주소</span>
                                <p className="font-medium text-slate-800">{land.address || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">건축물 용도</span>
                                <p className="font-medium text-slate-800">{land.building_type || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">공급면적</span>
                                <p className="font-medium text-slate-800">{land.area_supply || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">전용면적</span>
                                <p className="font-medium text-slate-800">{land.area_exclusive || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">층수</span>
                                <p className="font-medium text-slate-800">{land.floor || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">방향</span>
                                <p className="font-medium text-slate-800">{land.direction || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">방/욕실 수</span>
                                <p className="font-medium text-slate-800">{land.room_count || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">주차</span>
                                <p className="font-medium text-slate-800">{land.parking || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">입주가능일</span>
                                <p className="font-medium text-slate-800">{land.move_in_date || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">관리비</span>
                                <p className="font-medium text-slate-800">{land.maintenance_fee || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">난방방식</span>
                                <p className="font-medium text-slate-800">{land.heating_method || '-'}</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-600 text-sm w-32">엘리베이터</span>
                                <p className="font-medium text-slate-800">{land.elevator || '-'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 하단: 상세내용 (전체 너비) */}
            <div className="rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl p-6">
                <h3 className="text-xl font-bold mb-4 text-slate-800">상세내용</h3>
                <p className="text-slate-700 whitespace-pre-line leading-relaxed">
                    {land.description || '상세 설명이 없습니다.'}
                </p>
            </div>

        </div>
    );
}
