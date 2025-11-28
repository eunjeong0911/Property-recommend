/**
 * LandListFilter 컴포넌트
 * 
 * 매물 리스트 필터링 컴포넌트
 * 
/**
 * LandListFilter 컴포넌트
 *
 * 매물 리스트 필터링 컴포넌트
 *
 * 주요 기능:
 * - 지역 선택 드롭다운
 * - 거주 형태 선택 드롭다운
 * - 가격 범위 선택 드롭다운
 * - 방의 개수 선택 드롭다운
 * - 초기화 버튼
 */

'use client';

import { useState } from 'react';
import { Search, ChevronDown, X } from 'lucide-react';

export default function LandListFilter() {
    const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
    const [selectedRegion, setSelectedRegion] = useState<string>('지역');
    const [selectedTransaction, setSelectedTransaction] = useState<string>('거래유형');
    const [selectedBuilding, setSelectedBuilding] = useState<string>('건물유형');

    const regionOptions = ['서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'];
    const transactionOptions = ['매매', '전세', '월세'];
    const buildingOptions = ['아파트', '오피스텔', '빌라', '원룸', '투룸'];

    const toggleDropdown = (name: string) => {
        setActiveDropdown(prev => (prev === name ? null : name));
    };

    const handleSelect = (type: 'region' | 'transaction' | 'building', value: string) => {
        if (type === 'region') {
            setSelectedRegion(value);
        } else if (type === 'transaction') {
            setSelectedTransaction(value);
        } else {
            setSelectedBuilding(value);
        }
        setActiveDropdown(null);
    };

    const handleReset = () => {
        setSelectedRegion('지역');
        setSelectedTransaction('거래유형');
        setSelectedBuilding('건물유형');
    };

    return (
        <div className="flex flex-col gap-4 p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl relative z-20">
            {/* 검색 및 필터 상단 */}
            <div className="flex gap-2">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                        type="text"
                        placeholder="아파트, 지역, 학교명으로 검색"
                        className="w-full pl-10 pr-4 py-2 bg-white/50 border border-white/40 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 placeholder-gray-500 text-gray-800"
                    />
                </div>
                <button
                    onClick={handleReset}
                    className="p-2 border border-white/40 rounded-xl hover:bg-white/50 transition-colors bg-white/30 text-gray-600 text-sm px-4"
                >
                    초기화
                </button>
            </div>

            {/* 필터 옵션들 (드롭다운) */}
            <div className="flex gap-3">
                {/* 지역 드롭다운 */}
                <div className="relative">
                    <button
                        onClick={() => toggleDropdown('region')}
                        className={`
                            flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 border
                            ${selectedRegion !== '지역'
                                ? 'bg-blue-500 text-white border-blue-500 shadow-md'
                                : 'bg-white/40 text-gray-700 border-white/40 hover:bg-white/60 hover:border-blue-300'
                            }
                        `}
                    >
                        {selectedRegion}
                        <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${activeDropdown === 'region' ? 'rotate-180' : ''}`} />
                    </button>

                    {activeDropdown === 'region' && (
                        <div className="absolute top-full left-0 mt-2 w-32 max-h-60 overflow-y-auto bg-white/90 backdrop-blur-md border border-white/40 rounded-xl shadow-xl z-50 scrollbar-hide">
                            {regionOptions.map((option) => (
                                <button
                                    key={option}
                                    onClick={() => handleSelect('region', option)}
                                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                                >
                                    {option}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* 거래유형 드롭다운 */}
                <div className="relative">
                    <button
                        onClick={() => toggleDropdown('transaction')}
                        className={`
                            flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 border
                            ${selectedTransaction !== '거래유형'
                                ? 'bg-blue-500 text-white border-blue-500 shadow-md'
                                : 'bg-white/40 text-gray-700 border-white/40 hover:bg-white/60 hover:border-blue-300'
                            }
                        `}
                    >
                        {selectedTransaction}
                        <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${activeDropdown === 'transaction' ? 'rotate-180' : ''}`} />
                    </button>

                    {activeDropdown === 'transaction' && (
                        <div className="absolute top-full left-0 mt-2 w-32 bg-white/90 backdrop-blur-md border border-white/40 rounded-xl shadow-xl overflow-hidden z-50">
                            {transactionOptions.map((option) => (
                                <button
                                    key={option}
                                    onClick={() => handleSelect('transaction', option)}
                                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                                >
                                    {option}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* 건물유형 드롭다운 */}
                <div className="relative">
                    <button
                        onClick={() => toggleDropdown('building')}
                        className={`
                            flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 border
                            ${selectedBuilding !== '건물유형'
                                ? 'bg-blue-500 text-white border-blue-500 shadow-md'
                                : 'bg-white/40 text-gray-700 border-white/40 hover:bg-white/60 hover:border-blue-300'
                            }
                        `}
                    >
                        {selectedBuilding}
                        <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${activeDropdown === 'building' ? 'rotate-180' : ''}`} />
                    </button>

                    {activeDropdown === 'building' && (
                        <div className="absolute top-full left-0 mt-2 w-32 bg-white/90 backdrop-blur-md border border-white/40 rounded-xl shadow-xl overflow-hidden z-50">
                            {buildingOptions.map((option) => (
                                <button
                                    key={option}
                                    onClick={() => handleSelect('building', option)}
                                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                                >
                                    {option}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* 선택된 필터 태그들 */}
            <div className="flex flex-wrap gap-2 min-h-[28px]">
                {selectedRegion !== '지역' && (
                    <span className="px-2 py-1 bg-blue-100/50 text-blue-700 text-xs rounded-lg border border-blue-200/50 flex items-center gap-1">
                        {selectedRegion} <X className="w-3 h-3 cursor-pointer" onClick={() => setSelectedRegion('지역')} />
                    </span>
                )}
                {selectedTransaction !== '거래유형' && (
                    <span className="px-2 py-1 bg-blue-100/50 text-blue-700 text-xs rounded-lg border border-blue-200/50 flex items-center gap-1">
                        {selectedTransaction} <X className="w-3 h-3 cursor-pointer" onClick={() => setSelectedTransaction('거래유형')} />
                    </span>
                )}
                {selectedBuilding !== '건물유형' && (
                    <span className="px-2 py-1 bg-blue-100/50 text-blue-700 text-xs rounded-lg border border-blue-200/50 flex items-center gap-1">
                        {selectedBuilding} <X className="w-3 h-3 cursor-pointer" onClick={() => setSelectedBuilding('건물유형')} />
                    </span>
                )}
            </div>
        </div>
    );
}
