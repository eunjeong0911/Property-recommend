/**
 * LandDetail 컴포넌트
 * 
 * 매물 상세정보를 표시하는 컴포넌트
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import { Land } from '../types/land';
import { fetchLandById } from '../api/landApi';
import { recordListingView } from '../api/historyApi';

interface LandDetailProps {
    landId: string;
}

export default function LandDetail({ landId }: LandDetailProps) {
    const [land, setLand] = useState<Land | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [liked, setLiked] = useState(false);
    const [showPriceTooltip, setShowPriceTooltip] = useState(false);
    const [maxScrollDepth, setMaxScrollDepth] = useState(0);
    const maxScrollDepthRef = useRef(0);

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

    // 스크롤 깊이 추적
    useEffect(() => {
        const handleScroll = () => {
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            const scrollTop = window.scrollY;

            // 현재 스크롤 위치를 퍼센트로 계산
            const scrollPercentage = Math.round(
                ((scrollTop + windowHeight) / documentHeight) * 100
            );

            // 최대 스크롤 깊이 업데이트 (state와 ref 모두)
            const newMaxDepth = Math.max(maxScrollDepthRef.current, Math.min(scrollPercentage, 100));
            maxScrollDepthRef.current = newMaxDepth;
            setMaxScrollDepth(newMaxDepth);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // 매물 조회 이력 추적
    useEffect(() => {
        const startTime = Date.now();

        // 컴포넌트 언마운트 시 총 조회 시간 및 스크롤 깊이 저장
        return () => {
            const totalViewDuration = Math.floor((Date.now() - startTime) / 1000);
            // 최소 1초 이상 조회한 경우만 기록
            if (totalViewDuration >= 1) {
                // ref에서 최종 스크롤 깊이 가져오기
                recordListingView(landId, totalViewDuration, maxScrollDepthRef.current);
            }
        };
    }, [landId]); // maxScrollDepth 제거!

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

    // 이미지가 없으면 기본 placeholder 사용
    const defaultPlaceholder = '/images/placeholder.svg';
    const images = land.images && land.images.length > 0
        ? land.images
        : [land.image || defaultPlaceholder];

    const handlePrevImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
    };

    const handleNextImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
    };

    const handleLike = (e: React.MouseEvent) => {
        e.stopPropagation();
        setLiked(!liked);
    };

    // 신뢰도 등급에 따른 아이콘 반환
    const getTrustBadgeImage = (score: string | null | undefined) => {
        switch (score) {
            case 'A': return '/assets/land_broker/gold.png';
            case 'B': return '/assets/land_broker/silver.png';
            case 'C': return '/assets/land_broker/bronze.png';
            default: return null;
        }
    };

    // 가격 분류 레이블 배지 색상
    const getPriceBadgeColor = (label: string | undefined) => {
        switch (label) {
            case '저렴': return 'text-green-600';
            case '적정': return 'text-blue-600';
            case '비쌈': return 'text-red-600';
            default: return 'text-gray-600';
        }
    };

    // 관리비 파싱 함수 - "~만원" 형태로 추출
    const parseMaintenanceFee = (fee: string | undefined): string => {
        if (!fee || fee === '-') return '-';
        const match = fee.match(/(\d+)\s*만\s*원/);
        if (match) {
            return `${match[1]}만원`;
        }
        return fee;
    };

    // listing_info에서 카테고리별 데이터 추출 및 파싱
    const getCategorizedFacilities = () => {
        const listingInfo = land.listing_info || {};
        // 문자열을 배열로 변환하고 괄호, 따옴표 제거하는 헬퍼 함수
        const parseToArray = (value: any): string[] => {
            if (!value) return [];

            // 이미 배열이면 그대로 반환
            if (Array.isArray(value)) return value;

            // 문자열이면 쉼표로 분리하고 정리
            if (typeof value === 'string') {
                return value
                    .split(',')
                    .map(item => item
                        .trim()
                        .replace(/[\[\]()'"]/g, '') // 괄호, 따옴표 제거
                        .trim()
                    )
                    .filter(item => item.length > 0); // 빈 문자열 제거
            }

            return [];
        };
        return {
            heating: parseToArray(listingInfo['난방방식']),
            cooling: parseToArray(listingInfo['냉방시설']),
            living: parseToArray(listingInfo['생활시설']),
            security: parseToArray(listingInfo['보안시설']),
            facilities: parseToArray(listingInfo['기타시설'])
        };
    };
    // additional_options 파싱 (배열 또는 문자열)
    const getAdditionalOptions = () => {
        if (!land.additional_options) return [];

        // 이미 배열이면 그대로 반환
        if (Array.isArray(land.additional_options)) {
            return land.additional_options;
        }

        // 문자열이면 쉼표로 분리
        if (typeof land.additional_options === 'string') {
            return land.additional_options
                .split(',')
                .map((opt: string) => opt
                    .trim()
                    .replace(/[\[\]()'"]/g, '') // 괄호, 따옴표 제거
                    .trim()
                )
                .filter((opt: string) => opt.length > 0); // 빈 문자열 제거
        }

        return [];
    };

    const availableOptions = getAvailableOptions();

    // 주소에서 구 정보 추출
    const extractDistrict = (address: string | undefined) => {
        if (!address) return '서울특별시';
        const match = address.match(/서울[특별시]*\s*(\S+구)/);
        return match ? `서울특별시 ${match[1]}` : '서울특별시';
    };

    return (
        <div className="space-y-6">
            {/* 헤더 섹션: 매물번호, 주소, 가격 */}
            <div className="p-4">
                <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <p className="text-sm text-gray-500 mb-1">매물번호 {land.land_num}</p>
                        <h1 className="text-xl font-bold text-slate-800 mb-2">{land.address || '주소 정보 없음'}</h1>

                        <div className="flex items-center gap-3 mb-3">
                            <span className="text-2xl font-bold text-blue-600">{land.price || '-'}</span>

                            {land.price_prediction?.prediction_label_korean && (
                                <div className="relative inline-flex items-center gap-2">
                                    <span className={`px-3 py-1 rounded-lg text-sm font-bold ${land.price_prediction.prediction_label_korean === '저렴'
                                        ? 'bg-green-500 text-white'
                                        : land.price_prediction.prediction_label_korean === '적정'
                                            ? 'bg-blue-500 text-white'
                                            : 'bg-red-500 text-white'
                                        }`}>
                                        {land.price_prediction.prediction_label_korean}
                                    </span>
                                    <button
                                        className="w-5 h-5 rounded-full bg-gray-200 text-gray-600 text-xs font-bold hover:bg-gray-300 transition-colors"
                                        onMouseEnter={() => setShowPriceTooltip(true)}
                                        onMouseLeave={() => setShowPriceTooltip(false)}
                                    >
                                        ?
                                    </button>

                                    {showPriceTooltip && (
                                        <div className="absolute top-full left-0 mt-2 w-72 bg-white rounded-lg shadow-xl border border-gray-200 p-4 z-50">
                                            <p className="text-sm text-slate-700">
                                                해당 매물은 서울특별시 법정동 건물용도별 평당가로 분석했을 때 <strong className={getPriceBadgeColor(land.price_prediction.prediction_label_korean)}>
                                                    '{land.price_prediction.prediction_label_korean}'
                                                </strong>에 해당합니다.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* 이미지 + 부동산 온도 지수 (2컬럼) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
                    <div className="relative aspect-square bg-gray-100 group">
                        <Image
                            src={images[currentImageIndex]}
                            alt={land.title}
                            fill
                            sizes="(max-width: 768px) 100vw, 50vw"
                            className="object-cover"
                        />

                        <button
                            onClick={handleLike}
                            className="absolute top-4 right-4 hover:scale-110 transition-transform z-10"
                        >
                            <Image
                                src={liked ? '/icons/whish_on.png' : '/icons/whish_off.png'}
                                alt="찜하기"
                                width={40}
                                height={40}
                            />
                        </button>

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

                        <div className="absolute bottom-4 right-4 bg-black/60 text-white px-3 py-1 rounded-full text-sm">
                            {currentImageIndex + 1} / {images.length}
                        </div>
                    </div>
                </div>

                {/* 부동산 온도 지수 */}
                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden flex flex-col">
                    <div className="bg-slate-700 text-white px-4 py-3">
                        <h3 className="font-bold flex items-center gap-2">
                            <span className="text-xl">🌡️</span>
                            <span>부동산 온도</span>
                        </h3>
                    </div>
                    <div className="p-6 flex-1 flex flex-col justify-around space-y-7">
                        {[
                            { id: 'safety', label: '안전 온도', value: land.temperatures?.safety || 36.5, icon: '🛡️', desc: '치안 및 인프라' },
                            { id: 'convenience', label: '편의 온도', value: land.temperatures?.convenience || 36.5, icon: '🛒', desc: '생활 밀접 시설' },
                            { id: 'pet', label: '반려동물 온도', value: land.temperatures?.pet || 36.5, icon: '🐾', desc: '반려견 산책 및 병원' },
                            { id: 'traffic', label: '교통 온도', value: land.temperatures?.traffic || 36.5, icon: '🚇', desc: '대중교통 접근성' },
                            { id: 'culture', label: '문화 온도', value: land.temperatures?.culture || 36.5, icon: '🏛️', desc: '문화 및 예술 시설' },
                        ].map((temp) => (
                            <div key={temp.id} className="group cursor-default">
                                <div className="flex justify-between items-end mb-2">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-gray-50 flex items-center justify-center text-xl shadow-sm border border-gray-100 group-hover:scale-110 transition-transform duration-300">
                                            {temp.icon}
                                        </div>
                                        <div>
                                            <div className="font-bold text-slate-700">{temp.label}</div>
                                            <div className="text-[10px] text-gray-400">{temp.desc}</div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className={`text-xl font-black ${temp.value >= 39 ? 'text-red-500' :
                                            temp.value >= 35 ? 'text-orange-500' :
                                                'text-blue-500'
                                            }`}>
                                            {temp.value.toFixed(1)}
                                        </span>
                                        <span className="text-xs text-gray-400 ml-1">°C</span>
                                    </div>
                                </div>
                                <div className="h-3.5 bg-gray-100 rounded-full p-[2px] shadow-inner overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-1000 ease-out relative bg-gradient-to-r from-blue-400 via-yellow-400 to-red-500"
                                        style={{
                                            width: `${Math.min(100, Math.max(0, temp.value))}%`,
                                            backgroundSize: `${100 / Math.max(0.01, temp.value / 100)}% 100%`
                                        }}
                                    >
                                        <div className="absolute top-0 right-0 w-8 h-full bg-white/20 skew-x-[-20deg] animate-pulse"></div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 2컬럼 레이아웃: 핵심정보 / 계약 및 매물정보 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 핵심정보 */}
                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm flex flex-col">
                    <div className="bg-slate-700 text-white px-4 py-2 rounded-t-2xl">
                        <h3 className="font-bold text-sm">핵심정보</h3>
                    </div>
                    <div className="p-4 flex-1">
                        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">거래유형</span>
                                <span className="font-medium text-slate-800">{land.transaction_type || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">관리비</span>
                                <span className="font-medium text-slate-800">{parseMaintenanceFee(land.maintenance_fee)}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">건물형태/용도</span>
                                <span className="font-medium text-slate-800">{land.building_type || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">공급면적/전용</span>
                                <span className="font-medium text-slate-800">{land.area_supply || '-'} / {land.area_exclusive || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">방/욕실</span>
                                <span className="font-medium text-slate-800">{land.room_count || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">해당층/전체층</span>
                                <span className="font-medium text-slate-800">{land.floor || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">방향</span>
                                <span className="font-medium text-slate-800">{land.direction || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">방거실형태</span>
                                <span className="font-medium text-slate-800">{land.listing_info?.['방거실형태'] || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">주차</span>
                                <span className="font-medium text-slate-800">{land.parking || '-'}</span>
                            </div>
                        </div>
                    </div>
                </div>

            {/* 계약 및 매물정보 */}
            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                <div className="bg-slate-700 text-white px-4 py-2 rounded-t-2xl">
                    <h3 className="font-bold text-sm">계약 및 매물정보</h3>
                </div>
                <div className="p-4">
                    <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                        <div className="flex justify-between border-b border-gray-100 pb-1">
                            <span className="text-gray-500">입주가능일</span>
                            <span className="font-medium text-slate-800">{land.move_in_date || '-'}</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-1">
                            <span className="text-gray-500">사용승인일</span>
                            <span className="font-medium text-slate-800">{land.approval_date || '-'}</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-1">
                            <span className="text-gray-500">전세자금대출</span>
                            <span className="font-medium text-slate-800">{land.jeonse_loan || '-'}</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-1">
                            <span className="text-gray-500">전입신고</span>
                            <span className="font-medium text-slate-800">{land.move_in_report || '-'}</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-1">
                            <span className="text-gray-500">현입주고객</span>
                            <span className="font-medium text-slate-800">가능</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-1">
                            <span className="text-gray-500">융자금</span>
                            <span className="font-medium text-slate-800">없음</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-1">
                            <span className="text-gray-500">위반건축물</span>
                            <span className="font-medium text-slate-800">아님</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
                {/* 계약 및 매물정보 */}
                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm flex flex-col">
                    <div className="bg-slate-700 text-white px-4 py-2 rounded-t-2xl">
                        <h3 className="font-bold text-sm">계약 및 매물정보</h3>
                    </div>
                    <div className="p-4 flex-1">
                        <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">입주가능일</span>
                                <span className="font-medium text-slate-800">{land.move_in_date || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">사용승인일</span>
                                <span className="font-medium text-slate-800">{land.approval_date || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">전세자금대출</span>
                                <span className="font-medium text-slate-800">{land.jeonse_loan || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">전입신고</span>
                                <span className="font-medium text-slate-800">{land.move_in_report || '-'}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">현입주고객</span>
                                <span className="font-medium text-slate-800">가능</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">융자금</span>
                                <span className="font-medium text-slate-800">없음</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                <span className="text-gray-500">위반건축물</span>
                                <span className="font-medium text-slate-800">아님</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 생활 및 옵션정보 */ }
    {
        (categorizedFacilities.heating.length > 0 ||
            categorizedFacilities.cooling.length > 0 ||
            categorizedFacilities.living.length > 0 ||
            categorizedFacilities.security.length > 0 ||
            categorizedFacilities.facilities.length > 0 ||
            additionalOptions.length > 0) && (
            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                <div className="bg-slate-700 text-white px-4 py-2 rounded-t-2xl">
                    <h3 className="font-bold text-sm">생활 및 옵션정보</h3>
                </div>
                <div className="p-6 space-y-6">
                    {/* 난방방식 */}
                    {categorizedFacilities.heating.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <Image src="/assets/land_details/heating.png" alt="난방방식" width={24} height={24} />
                                <h4 className="font-semibold text-slate-800">난방방식</h4>
                            </div>
                            <div className="flex flex-wrap gap-2 ml-8">
                                {categorizedFacilities.heating.map((item: string, idx: number) => (
                                    <span key={idx} className="px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-sm">
                                        {item}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 냉방시설 */}
                    {categorizedFacilities.cooling.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <Image src="/assets/land_details/cooling.png" alt="냉방시설" width={24} height={24} />
                                <h4 className="font-semibold text-slate-800">냉방시설</h4>
                            </div>
                            <div className="flex flex-wrap gap-2 ml-8">
                                {categorizedFacilities.cooling.map((item: string, idx: number) => (
                                    <span key={idx} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
                                        {item}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 생활시설 */}
                    {categorizedFacilities.living.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <Image src="/assets/land_details/life.png" alt="생활시설" width={24} height={24} />
                                <h4 className="font-semibold text-slate-800">생활시설</h4>
                            </div>
                            <div className="flex flex-wrap gap-2 ml-8">
                                {categorizedFacilities.living.map((item: string, idx: number) => (
                                    <span key={idx} className="px-3 py-1 bg-teal-50 text-teal-700 rounded-full text-sm">
                                        {item}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 보안시설 */}
                    {categorizedFacilities.security.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <Image src="/assets/land_details/security.png" alt="보안시설" width={24} height={24} />
                                <h4 className="font-semibold text-slate-800">보안시설</h4>
                            </div>
                            <div className="flex flex-wrap gap-2 ml-8">
                                {categorizedFacilities.security.map((item: string, idx: number) => (
                                    <span key={idx} className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm">
                                        {item}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 기타시설 */}
                    {categorizedFacilities.facilities.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <Image src="/assets/land_details/facilities.png" alt="기타시설" width={24} height={24} />
                                <h4 className="font-semibold text-slate-800">기타시설</h4>
                            </div>
                            <div className="flex flex-wrap gap-2 ml-8">
                                {categorizedFacilities.facilities.map((item: string, idx: number) => (
                                    <span key={idx} className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm">
                                        {item}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
            {/* 옵션 및 주거 정보 */}
            {
                availableOptions.length > 0 && (
                    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                        <div className="bg-slate-700 text-white px-4 py-2 rounded-t-2xl">
                            <h3 className="font-bold text-sm">생활 및 주변 정보</h3>
                        </div>
                        <div className="p-4">
                            <div className="grid grid-cols-4 md:grid-cols-8 gap-4">
                                {availableOptions.map((option) => (
                                    <div key={option.id} className="flex flex-col items-center gap-2">
                                        <div className="w-12 h-12 rounded-lg bg-gray-50 border border-gray-200 flex items-center justify-center">
                                            <Image src={option.icon} alt={option.name} width={28} height={28} />
                                        </div>
                                        <span className="text-xs text-gray-600 text-center">{option.name}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )
            }

                    {/* 추가옵션 */}
                    {additionalOptions.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <Image src="/assets/land_details/options.png" alt="추가옵션" width={24} height={24} />
                                <h4 className="font-semibold text-slate-800">추가옵션</h4>
                            </div>
                            <div className="flex flex-wrap gap-2 ml-8">
                                {additionalOptions.map((option: string, idx: number) => (
                                    <span key={idx} className="px-3 py-1 bg-gray-50 text-gray-700 rounded-full text-sm border border-gray-200">
                                        {option}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        )
    }

    {/* 상세 설명 섹션 */ }
    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
        <div className="bg-slate-700 text-white px-4 py-2 rounded-t-2xl">
            <h3 className="font-bold text-sm">상세 설명</h3>
        </div>
        <div className="p-4">
            <p className="text-slate-700 whitespace-pre-line leading-relaxed text-sm">
                {land.description || '상세 설명이 없습니다.'}
            </p>
        </div>
    </div>

    {/* 중개사 정보 */ }
    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
        <div className="bg-slate-700 text-white px-4 py-2 rounded-t-2xl">
            <h3 className="font-bold text-sm">중개사 정보</h3>
        </div>
        <div className="p-4">
            <div className="flex items-start gap-4">
                <div className="flex-1 space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                        <span className="text-gray-500 w-24">중개사무소</span>
                        <span className="font-semibold text-slate-800">{land.broker?.office_name || '-'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-gray-500 w-24">대표자</span>
                        <span className="font-semibold text-slate-800">{land.broker?.representative || '-'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-gray-500 w-24">연락처</span>
                        <span className="font-semibold text-slate-800">{land.broker?.phone || '-'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-gray-500 w-24">중개사무소 주소</span>
                        <span className="font-semibold text-slate-800 text-xs">{land.broker?.address || '-'}</span>
                    </div>

                    {/* 신뢰도 등급 표시 + PNG 아이콘 */}
                    {land.broker?.trust_score && (
                        <div className="flex items-center gap-2 pt-2 border-t border-gray-200">
                            <span className="text-gray-500 w-24">신뢰도</span>
                            {getTrustBadgeImage(land.broker.trust_score) && (
                                <Image
                                    src={getTrustBadgeImage(land.broker.trust_score)!}
                                    alt={`${land.broker.trust_score}`}
                                    width={36}
                                    height={36}
                                    className="object-contain"
                                />
                            )}
                            <span className={`px-3 py-1 rounded-full text-sm font-bold ${land.broker.trust_score === 'A' ? 'bg-yellow-500 text-white' :
                                land.broker.trust_score === 'B' ? 'bg-gray-400 text-white' :
                                    'bg-amber-700 text-white'
                                }`}>
                                {land.broker.trust_score === 'A' ? '골드' : land.broker.trust_score === 'B' ? '실버' : '브론즈'}
                            </span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    </div>
        </div >
                            {land.broker?.trust_score && (
                                <div className="flex items-center gap-2 pt-2 border-t border-gray-200">
                                    <span className="text-gray-500 w-24">신뢰도</span>
                                    {getTrustBadgeImage(land.broker.trust_score) && (
                                        <Image
                                            src={getTrustBadgeImage(land.broker.trust_score)!}
                                            alt={`${land.broker.trust_score}`}
                                            width={36}
                                            height={36}
                                            className="object-contain"
                                        />
                                    )}
                                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${land.broker.trust_score === 'A' ? 'bg-yellow-500 text-white' :
                                        land.broker.trust_score === 'B' ? 'bg-gray-400 text-white' :
                                            'bg-amber-700 text-white'
                                        }`}>
                                        {land.broker.trust_score === 'A' ? '골드' : land.broker.trust_score === 'B' ? '실버' : '브론즈'}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div >
    );
}
