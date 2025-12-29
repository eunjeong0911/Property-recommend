/**
 * LandListFilter 컴포넌트 - PropTech Bank-Level Design
 *
 * 매물 목록 필터링 컴포넌트
 *
 * 주요 기능:
 * - 자치구 선택
 * - 행정동 선택 (자치구 선택 시 활성화)
 * - 거래유형 선택
 * - 건물유형 선택
 * - 필터 초기화
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { LandFilterParams } from '../types/land';

// 초기 필터 상태 (SSR과 클라이언트 일치를 위해 고정값 사용)
const INITIAL_FILTER = {
    selectedRegion: '',
    selectedDong: '',
    selectedTransaction: '',
    selectedBuilding: '',
};

// 서울특별시 25개 자치구
const SEOUL_DISTRICTS = [
    '강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구',
    '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구',
    '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구'
];

// 서울특별시 행정동 목록 (자치구별)
const DONG_MAP: Record<string, string[]> = {
    '강남구': ['역삼동', '삼성동', '대치동', '청담동', '논현동', '압구정동', '신사동', '개포동', '세곡동', '일원동', '수서동', '도곡동'],
    '강동구': ['명일동', '고덕동', '상일동', '길동', '둔촌동', '암사동', '성내동', '천호동', '강일동'],
    '강북구': ['미아동', '번동', '수유동', '우이동'],
    '강서구': ['염창동', '등촌동', '화곡동', '가양동', '마곡동', '내발산동', '외발산동', '공항동', '방화동'],
    '관악구': ['봉천동', '신림동', '남현동'],
    '광진구': ['중곡동', '능동', '구의동', '광장동', '자양동', '화양동'],
    '구로구': ['신도림동', '구로동', '가리봉동', '고척동', '개봉동', '오류동', '궁동', '온수동', '천왕동', '항동'],
    '금천구': ['가산동', '독산동', '시흥동'],
    '노원구': ['월계동', '공릉동', '하계동', '상계동', '중계동'],
    '도봉구': ['쌍문동', '방학동', '창동', '도봉동'],
    '동대문구': ['용신동', '제기동', '전농동', '답십리동', '장안동', '청량리동', '회기동', '휘경동', '이문동'],
    '동작구': ['노량진동', '상도동', '흑석동', '사당동', '대방동', '신대방동'],
    '마포구': ['공덕동', '아현동', '도화동', '용강동', '대흥동', '염리동', '신수동', '서강동', '서교동', '합정동', '망원동', '연남동', '성산동', '상암동'],
    '서대문구': ['충현동', '천연동', '신촌동', '연희동', '홍제동', '홍은동', '북아현동', '북가좌동', '남가좌동'],
    '서초구': ['서초동', '잠원동', '반포동', '방배동', '양재동', '내곡동'],
    '성동구': ['왕십리도선동', '왕십리동', '마장동', '사근동', '행당동', '응봉동', '금호동', '옥수동', '성수동', '송정동', '용답동'],
    '성북구': ['성북동', '삼선동', '동선동', '돈암동', '안암동', '보문동', '정릉동', '길음동', '종암동', '월곡동', '장위동', '석관동'],
    '송파구': ['잠실동', '신천동', '풍납동', '송파동', '석촌동', '삼전동', '가락동', '문정동', '장지동', '오금동', '방이동', '거여동', '마천동'],
    '양천구': ['목동', '신월동', '신정동'],
    '영등포구': ['영등포동', '영등포본동', '여의도동', '당산동', '도림동', '문래동', '양평동', '신길동', '대림동'],
    '용산구': ['후암동', '용산2가동', '남영동', '청파동', '원효로동', '효창동', '용문동', '한강로동', '이촌동', '이태원동', '한남동', '서빙고동', '보광동'],
    '은평구': ['수색동', '녹번동', '불광동', '갈현동', '구산동', '대조동', '응암동', '역촌동', '신사동', '증산동'],
    '종로구': ['청운효자동', '사직동', '삼청동', '부암동', '평창동', '무악동', '교남동', '가회동', '종로1·2·3·4가동', '종로5·6가동', '이화동', '혜화동', '창신동', '숭인동'],
    '중구': ['소공동', '회현동', '명동', '필동', '장충동', '광희동', '을지로동', '신당동', '다산동', '약수동', '청구동', '신당5동', '동화동', '황학동', '중림동'],
    '중랑구': ['면목동', '상봉동', '중화동', '묵동', '망우동', '신내동']
};

const TRANSACTION_OPTIONS = ['매매', '전세', '월세', '단기임대'];
const BUILDING_OPTIONS = ['아파트', '오피스텔', '빌라주택', '원투룸'];

interface LandListFilterProps {
    onFilterChange?: (params: LandFilterParams) => void;
}

// sessionStorage에서 필터 값 로드
const loadFilterFromStorage = () => {
    if (typeof window === 'undefined') return null;
    try {
        const saved = sessionStorage.getItem('landListFilter');
        return saved ? JSON.parse(saved) : null;
    } catch {
        return null;
    }
};

export default function LandListFilter({ onFilterChange }: LandListFilterProps) {
    // SSR과 클라이언트 일치를 위해 초기값은 고정값 사용
    const [selectedRegion, setSelectedRegion] = useState<string>(INITIAL_FILTER.selectedRegion);
    const [selectedDong, setSelectedDong] = useState<string>(INITIAL_FILTER.selectedDong);
    const [selectedTransaction, setSelectedTransaction] = useState<string>(INITIAL_FILTER.selectedTransaction);
    const [selectedBuilding, setSelectedBuilding] = useState<string>(INITIAL_FILTER.selectedBuilding);
    const [isMounted, setIsMounted] = useState(false);

    // 이전 자치구 값을 추적
    const prevRegionRef = useRef<string>(selectedRegion);

    // 클라이언트 마운트 후 sessionStorage에서 값 로드
    useEffect(() => {
        setIsMounted(true);
        const savedFilter = loadFilterFromStorage();
        if (savedFilter) {
            setSelectedRegion(savedFilter.selectedRegion || '');
            setSelectedDong(savedFilter.selectedDong || '');
            setSelectedTransaction(savedFilter.selectedTransaction || '');
            setSelectedBuilding(savedFilter.selectedBuilding || '');
            prevRegionRef.current = savedFilter.selectedRegion || '';
        }
    }, []);

    // 필터 변경 시 sessionStorage에 저장 (마운트 후에만)
    useEffect(() => {
        if (!isMounted) return;

        const filterData = {
            selectedRegion,
            selectedDong,
            selectedTransaction,
            selectedBuilding,
        };

        sessionStorage.setItem('landListFilter', JSON.stringify(filterData));
    }, [selectedRegion, selectedDong, selectedTransaction, selectedBuilding, isMounted]);

    // 필터 변경 시 부모 컴포넌트에 알림
    useEffect(() => {
        if (onFilterChange) {
            onFilterChange({
                region: selectedRegion,
                dong: selectedDong,
                transaction_type: selectedTransaction,
                building_type: selectedBuilding,
            });
        }
    }, [selectedRegion, selectedDong, selectedTransaction, selectedBuilding, onFilterChange]);

    // 자치구가 실제로 변경되면 행정동 초기화
    useEffect(() => {
        // 이전 값과 현재 값이 다르고, 이전 값이 빈 문자열이 아닐 때만 초기화
        // (초기 로드 시에는 prevRegionRef가 초기값이므로 초기화되지 않음)
        if (prevRegionRef.current !== selectedRegion && prevRegionRef.current !== '') {
            setSelectedDong('');
        }
        // 현재 값을 이전 값으로 저장
        prevRegionRef.current = selectedRegion;
    }, [selectedRegion]);

    const handleReset = () => {
        setSelectedRegion('');
        setSelectedDong('');
        setSelectedTransaction('');
        setSelectedBuilding('');

        // sessionStorage에서도 삭제
        if (typeof window !== 'undefined') {
            sessionStorage.removeItem('landListFilter');
        }
    };

    const dongList = selectedRegion ? (DONG_MAP[selectedRegion] || []) : [];

    return (
        <div className="bg-white border border-[var(--color-border-light)] rounded-xl p-6 shadow-[var(--shadow-md)]">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-[var(--color-primary)]">매물 필터</h3>
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

            <div className="flex items-end gap-4">
                {/* 자치구 선택 */}
                <div className="flex-1 space-y-2">
                    <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                        자치구
                    </label>
                    <select
                        value={selectedRegion}
                        onChange={(e) => setSelectedRegion(e.target.value)}
                        className="w-full px-4 py-2.5 border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition-all"
                    >
                        <option value="">전체</option>
                        {SEOUL_DISTRICTS.map((district) => (
                            <option key={district} value={district}>
                                {district}
                            </option>
                        ))}
                    </select>
                </div>

                {/* 행정동 선택 */}
                <div className="flex-1 space-y-2">
                    <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                        행정동
                    </label>
                    <select
                        value={selectedDong}
                        onChange={(e) => setSelectedDong(e.target.value)}
                        disabled={!selectedRegion || dongList.length === 0}
                        className="w-full px-4 py-2.5 border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent disabled:bg-[var(--color-bg-secondary)] disabled:cursor-not-allowed transition-all"
                    >
                        <option value="">
                            {selectedRegion ? '전체' : '선택'}
                        </option>
                        {dongList.map((dong) => (
                            <option key={dong} value={dong}>
                                {dong}
                            </option>
                        ))}
                    </select>
                </div>

                {/* 거래유형 드롭다운 */}
                <div className="flex-1 space-y-2">
                    <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                        거래유형
                    </label>
                    <select
                        value={selectedTransaction}
                        onChange={(e) => setSelectedTransaction(e.target.value)}
                        className="w-full px-4 py-2.5 border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition-all"
                    >
                        <option value="">전체</option>
                        {TRANSACTION_OPTIONS.map((option) => (
                            <option key={option} value={option}>
                                {option}
                            </option>
                        ))}
                    </select>
                </div>

                {/* 건물용도 드롭다운 */}
                <div className="flex-1 space-y-2">
                    <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                        건물용도
                    </label>
                    <select
                        value={selectedBuilding}
                        onChange={(e) => setSelectedBuilding(e.target.value)}
                        className="w-full px-4 py-2.5 border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition-all"
                    >
                        <option value="">전체</option>
                        {BUILDING_OPTIONS.map((option) => (
                            <option key={option} value={option}>
                                {option}
                            </option>
                        ))}
                    </select>
                </div>
            </div>
        </div>
    );
}
