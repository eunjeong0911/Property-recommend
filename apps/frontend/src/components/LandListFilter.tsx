/**
/**
 * LandListFilter 컴포넌트
 *
 * 매물 목록 필터링 컴포넌트
 *
 * 주요 기능:
 * - 검색어 입력
 * - 필터 옵션 선택 (거래유형, 건물유형, 지역)
 * - 선택된 필터 태그 표시 및 삭제
 * - 필터 초기화
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { Search, X, ChevronDown } from 'lucide-react';
import { useParticleEffect } from '../hooks/useParticleEffect';

const REGION_OPTIONS = ['서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'];
const TRANSACTION_OPTIONS = ['매매', '전세', '월세'];
const BUILDING_OPTIONS = ['아파트', '오피스텔', '빌라', '원룸', '투룸'];

export default function LandListFilter() {
    const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
    const [selectedRegion, setSelectedRegion] = useState<string>('');
    const [selectedTransaction, setSelectedTransaction] = useState<string>('');
    const [selectedBuilding, setSelectedBuilding] = useState<string>('');

    const dropdownRef = useRef<HTMLDivElement>(null);
    const { triggerEffect } = useParticleEffect();

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setActiveDropdown(null);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    const toggleDropdown = (name: string, event: React.MouseEvent<HTMLElement>) => {
        setActiveDropdown(activeDropdown === name ? null : name);
        triggerEffect(event.currentTarget as HTMLElement);
    };

    const handleSelect = (type: 'region' | 'transaction' | 'building', value: string, event: React.MouseEvent<HTMLElement>) => {
        if (type === 'region') setSelectedRegion(value);
        if (type === 'transaction') setSelectedTransaction(value);
        if (type === 'building') setSelectedBuilding(value);
        setActiveDropdown(null);
        triggerEffect(event.currentTarget as HTMLElement);
    };

    const handleReset = (event: React.MouseEvent<HTMLElement>) => {
        setSelectedRegion('');
        setSelectedTransaction('');
        setSelectedBuilding('');
        triggerEffect(event.currentTarget as HTMLElement);
    };

    const removeFilter = (type: 'region' | 'transaction' | 'building', event: React.MouseEvent<HTMLElement>) => {
        event.stopPropagation(); // Prevent dropdown toggle if clicking close inside a button (though these are separate tags)
        if (type === 'region') setSelectedRegion('');
        if (type === 'transaction') setSelectedTransaction('');
        if (type === 'building') setSelectedBuilding('');
        triggerEffect(event.currentTarget as HTMLElement);
    };

    return (
        <div className="p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl relative z-20" ref={dropdownRef}>
            <div className="flex flex-col gap-4">
                {/* Search Bar */}
                <div className="relative">
                    <input
                        type="text"
                        placeholder="지역, 지하철역, 학교 검색"
                        className="w-full py-3 pl-12 pr-4 bg-white/80 border-white/60 border-2 rounded-xl text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent shadow-sm transition-all"
                    />
                    <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
                </div>

                {/* Filter Options */}
                <div className="flex flex-wrap gap-2">
                    {/* Region Dropdown */}
                    <div className="relative">
                        <button
                            onClick={(e) => toggleDropdown('region', e)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 transition-all ${activeDropdown === 'region' || selectedRegion
                                    ? 'bg-blue-100 border-blue-300 text-blue-700'
                                    : 'bg-white/60 border-white/60 text-slate-600 hover:bg-white/80'
                                }`}
                        >
                            <span>{selectedRegion || '지역'}</span>
                            <ChevronDown className={`w-4 h-4 transition-transform ${activeDropdown === 'region' ? 'rotate-180' : ''}`} />
                        </button>
                        {activeDropdown === 'region' && (
                            <div className="absolute top-full left-0 mt-2 w-48 bg-white/90 backdrop-blur-sm border border-white/60 rounded-xl shadow-lg p-2 z-50 max-h-60 overflow-y-auto scrollbar-hide">
                                <div className="grid grid-cols-2 gap-1">
                                    {REGION_OPTIONS.map((option) => (
                                        <button
                                            key={option}
                                            onClick={(e) => handleSelect('region', option, e)}
                                            className={`px-3 py-2 rounded-lg text-sm text-left transition-colors ${selectedRegion === option
                                                    ? 'bg-blue-100 text-blue-700 font-medium'
                                                    : 'text-slate-600 hover:bg-slate-100'
                                                }`}
                                        >
                                            {option}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Transaction Type Dropdown */}
                    <div className="relative">
                        <button
                            onClick={(e) => toggleDropdown('transaction', e)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 transition-all ${activeDropdown === 'transaction' || selectedTransaction
                                    ? 'bg-blue-100 border-blue-300 text-blue-700'
                                    : 'bg-white/60 border-white/60 text-slate-600 hover:bg-white/80'
                                }`}
                        >
                            <span>{selectedTransaction || '거래유형'}</span>
                            <ChevronDown className={`w-4 h-4 transition-transform ${activeDropdown === 'transaction' ? 'rotate-180' : ''}`} />
                        </button>
                        {activeDropdown === 'transaction' && (
                            <div className="absolute top-full left-0 mt-2 w-32 bg-white/90 backdrop-blur-sm border border-white/60 rounded-xl shadow-lg p-2 z-50">
                                <div className="flex flex-col gap-1">
                                    {TRANSACTION_OPTIONS.map((option) => (
                                        <button
                                            key={option}
                                            onClick={(e) => handleSelect('transaction', option, e)}
                                            className={`px-3 py-2 rounded-lg text-sm text-left transition-colors ${selectedTransaction === option
                                                    ? 'bg-blue-100 text-blue-700 font-medium'
                                                    : 'text-slate-600 hover:bg-slate-100'
                                                }`}
                                        >
                                            {option}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Building Type Dropdown */}
                    <div className="relative">
                        <button
                            onClick={(e) => toggleDropdown('building', e)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 transition-all ${activeDropdown === 'building' || selectedBuilding
                                    ? 'bg-blue-100 border-blue-300 text-blue-700'
                                    : 'bg-white/60 border-white/60 text-slate-600 hover:bg-white/80'
                                }`}
                        >
                            <span>{selectedBuilding || '건물유형'}</span>
                            <ChevronDown className={`w-4 h-4 transition-transform ${activeDropdown === 'building' ? 'rotate-180' : ''}`} />
                        </button>
                        {activeDropdown === 'building' && (
                            <div className="absolute top-full left-0 mt-2 w-32 bg-white/90 backdrop-blur-sm border border-white/60 rounded-xl shadow-lg p-2 z-50">
                                <div className="flex flex-col gap-1">
                                    {BUILDING_OPTIONS.map((option) => (
                                        <button
                                            key={option}
                                            onClick={(e) => handleSelect('building', option, e)}
                                            className={`px-3 py-2 rounded-lg text-sm text-left transition-colors ${selectedBuilding === option
                                                    ? 'bg-blue-100 text-blue-700 font-medium'
                                                    : 'text-slate-600 hover:bg-slate-100'
                                                }`}
                                        >
                                            {option}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Reset Button */}
                    <button
                        onClick={handleReset}
                        className="px-4 py-2 rounded-full border-2 border-red-200 bg-white/60 text-red-500 hover:bg-red-50 transition-all text-sm font-medium ml-auto"
                    >
                        초기화
                    </button>
                </div>

                {/* Selected Filters Tags */}
                {(selectedRegion || selectedTransaction || selectedBuilding) && (
                    <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-200/50">
                        {selectedRegion && (
                            <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-blue-500 text-white text-sm shadow-sm">
                                {selectedRegion}
                                <button onClick={(e) => removeFilter('region', e)} className="hover:text-blue-200"><X className="w-3 h-3" /></button>
                            </span>
                        )}
                        {selectedTransaction && (
                            <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-blue-500 text-white text-sm shadow-sm">
                                {selectedTransaction}
                                <button onClick={(e) => removeFilter('transaction', e)} className="hover:text-blue-200"><X className="w-3 h-3" /></button>
                            </span>
                        )}
                        {selectedBuilding && (
                            <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-blue-500 text-white text-sm shadow-sm">
                                {selectedBuilding}
                                <button onClick={(e) => removeFilter('building', e)} className="hover:text-blue-200"><X className="w-3 h-3" /></button>
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
