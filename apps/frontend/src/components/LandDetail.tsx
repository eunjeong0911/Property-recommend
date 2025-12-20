/**
 * LandDetail 컴포넌트
 * 
 * 매물 상세정보를 표시하는 컴포넌트
 */

'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
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
    const [showPriceTooltip, setShowPriceTooltip] = useState(false);

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

    // 옵션 목록 (DB에서 해당되는 것만 표시)
    const getAvailableOptions = () => {
        const options: { id: string; name: string; icon: string }[] = [];
        const descriptionText = (land.description || '').toLowerCase();
        const additionalText = (land.additional_options || '').toLowerCase();
        const optionsText = `${descriptionText} ${additionalText}`;

        if (optionsText.includes('에어컨') || optionsText.includes('냉방')) {
            options.push({ id: 'aircon', name: '에어컨', icon: '/assets/land_details/airconditional.png' });
        }
        if (optionsText.includes('난방') || land.heating_method) {
            options.push({ id: 'heating', name: '난방', icon: '/assets/land_details/heating.png' });
        }
        if (land.elevator === '있음' || optionsText.includes('엘리베이터')) {
            options.push({ id: 'elevator', name: '엘리베이터', icon: '/assets/land_details/elevator.png' });
        }
        if (optionsText.includes('반려동물') || optionsText.includes('애완동물') || optionsText.includes('펫')) {
            options.push({ id: 'pet', name: '반려동물', icon: '/assets/land_details/animal.png' });
        }
        if (optionsText.includes('인덕션')) {
            options.push({ id: 'induction', name: '인덕션', icon: '/assets/land_details/induction.png' });
        }
        if (optionsText.includes('가스레인지') || optionsText.includes('가스')) {
            options.push({ id: 'gas', name: '가스레인지', icon: '/assets/land_details/induction.png' });
        }
        if (optionsText.includes('전자레인지')) {
            options.push({ id: 'microwave', name: '전자레인지', icon: '/assets/land_details/microwave_oven.png' });
        }
        if (optionsText.includes('신발장') || additionalText.includes('신발장')) {
            options.push({ id: 'shoes', name: '신발장', icon: '/assets/land_details/shoes.png' });
        }

        return options;
    };

    const availableOptions = getAvailableOptions();

    // 레이더 차트용 더미 데이터 (실제 데이터로 교체 가능)
    const radarData = {
        교통: 75,
        편의: 60,
        치안: 80,
        환경: 70,
        교육: 65
    };

    // 주소에서 구 정보 추출
    const extractDistrict = (address: string | undefined) => {
        if (!address) return '서울특별시';
        const match = address.match(/서울[특별시]*\s*(\S+구)/);
        return match ? `서울특별시 ${match[1]}` : '서울특별시';
    };

    return (
        <div className="space-y-6">
            {/* 헤더 섹션: 매물번호, 주소, 가격 */}
            <div className="p-6">
                <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <p className="text-sm text-gray-500 mb-1">매물번호 {land.land_num}</p>
                        <h1 className="text-xl font-bold text-slate-800 mb-2">{land.address || '주소 정보 없음'}</h1>

                        {/* 가격 정보 (주소 바로 아래) */}
                        <div className="flex items-center gap-3 mb-3">
                            <span className="text-2xl font-bold text-blue-600">{land.price || '-'}</span>

                            {/* 가격 분류 배지 + 물음표 툴팁 */}
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

                                    {/* 가격 분류 설명 툴팁 */}
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

            {/* 이미지 + 레이더 차트 (동일 크기) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 이미지 캐러셀 */}
                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
                    <div className="relative aspect-square bg-gray-100 group">
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
                                width={40}
                                height={40}
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
                </div>

                {/* 레이더 차트 */}
                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 flex flex-col justify-center">
                    <h3 className="font-bold text-slate-800 mb-4 text-center">주변 환경 분석</h3>
                    <div className="flex justify-center items-center flex-1">
                        <div className="relative w-64 h-64">
                            <svg viewBox="0 0 200 200" className="w-full h-full">
                                {/* 배경 다각형 (5각형) */}
                                <polygon
                                    points="100,20 180,70 155,160 45,160 20,70"
                                    fill="none"
                                    stroke="#e5e7eb"
                                    strokeWidth="1"
                                />
                                <polygon
                                    points="100,40 160,80 140,150 60,150 40,80"
                                    fill="none"
                                    stroke="#e5e7eb"
                                    strokeWidth="1"
                                />
                                <polygon
                                    points="100,60 140,90 125,140 75,140 60,90"
                                    fill="none"
                                    stroke="#e5e7eb"
                                    strokeWidth="1"
                                />
                                <polygon
                                    points="100,80 120,100 110,130 90,130 80,100"
                                    fill="none"
                                    stroke="#e5e7eb"
                                    strokeWidth="1"
                                />

                                {/* 데이터 다각형 */}
                                <polygon
                                    points={`
                                        100,${100 - radarData.교통 * 0.8}
                                        ${100 + radarData.편의 * 0.76},${100 - radarData.편의 * 0.24}
                                        ${100 + radarData.치안 * 0.47},${100 + radarData.치안 * 0.62}
                                        ${100 - radarData.환경 * 0.47},${100 + radarData.환경 * 0.62}
                                        ${100 - radarData.교육 * 0.76},${100 - radarData.교육 * 0.24}
                                    `}
                                    fill="rgba(59, 130, 246, 0.3)"
                                    stroke="#3b82f6"
                                    strokeWidth="2"
                                />

                                {/* 축 라벨 */}
                                <text x="100" y="12" textAnchor="middle" fontSize="12" fill="#374151" fontWeight="600">교통</text>
                                <text x="188" y="72" textAnchor="start" fontSize="12" fill="#374151" fontWeight="600">편의</text>
                                <text x="160" y="175" textAnchor="middle" fontSize="12" fill="#374151" fontWeight="600">치안</text>
                                <text x="40" y="175" textAnchor="middle" fontSize="12" fill="#374151" fontWeight="600">환경</text>
                                <text x="12" y="72" textAnchor="end" fontSize="12" fill="#374151" fontWeight="600">교육</text>
                            </svg>
                        </div>
                    </div>

                    {/* 레이더 차트 범례 */}
                    <div className="grid grid-cols-5 gap-2 mt-4 text-xs text-center">
                        {Object.entries(radarData).map(([key, value]) => (
                            <div key={key} className="flex flex-col items-center">
                                <span className="text-blue-600 font-bold">{value}</span>
                                <span className="text-gray-500">{key}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 2컬럼 레이아웃: 핵심정보 / 계약및 매물정보 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 핵심정보 */}
                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                    <div className="bg-slate-700 text-white px-4 py-2 rounded-t-2xl">
                        <h3 className="font-bold text-sm">핵심정보</h3>
                    </div>
                    <div className="p-4">
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
                                <span className="text-gray-500">현관유형</span>
                                <span className="font-medium text-slate-800">복도식</span>
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

            {/* 옵션 및 주거 정보 (해당 옵션이 있는 경우에만 표시) */}
            {availableOptions.length > 0 && (
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
            )}

            {/* 상세 설명 섹션 */}
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

            {/* 중개사 정보 */}
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
                                        {land.broker.trust_score === 'A' ? '골드' : land.broker.trust_score === 'B' ? '실버' : '브론즈'} ({land.broker.trust_grade})
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
