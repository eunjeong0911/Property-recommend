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

// 서울 구 목록 (DB 데이터 기준)
const SEOUL_DISTRICTS = [
    '강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구',
    '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구',
    '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구'
];

const TRANSACTION_OPTIONS = ['매매', '전세', '월세', '단기임대', '미분류'];
const BUILDING_OPTIONS = ['아파트', '오피스텔', '빌라주택', '원투룸'];

import { LandFilterParams } from '../types/land';

interface LandListFilterProps {
    onFilterChange?: (params: LandFilterParams) => void;
}

export default function LandListFilter({ onFilterChange }: LandListFilterProps) {
    const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
    const [selectedRegion, setSelectedRegion] = useState<string>('');
    const [selectedTransaction, setSelectedTransaction] = useState<string>('');
    const [selectedBuilding, setSelectedBuilding] = useState<string>('');
    const [searchQuery, setSearchQuery] = useState<string>('');

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

    // Notify parent when filters change
    useEffect(() => {
        if (onFilterChange) {
            onFilterChange({
                region: selectedRegion,
                transaction_type: selectedTransaction,
                building_type: selectedBuilding,
                search: searchQuery
            });
        }
    }, [selectedRegion, selectedTransaction, selectedBuilding, searchQuery, onFilterChange]);

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
        setSearchQuery('');
        triggerEffect(event.currentTarget as HTMLElement);
    };

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(e.target.value);
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
                <div className="relative group">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={handleSearchChange}
                        placeholder="주소, 매물번호로 검색해보세요"
                        className="w-full py-3.5 pl-12 pr-4 bg-white/90 border-2 border-white/60 rounded-xl text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-300 focus:bg-white shadow-sm transition-all group-hover:shadow-md"
                    />
                    <div className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-blue-500 transition-colors">
                        <Search className="w-5 h-5" />
                    </div>
                </div>

                {/* Filter Options */}
                <div className="flex flex-wrap gap-2">
                    {/* Region Dropdown (서울 구 목록) */}
                    <div className="relative">
                        <button
                            onClick={(e) => toggleDropdown('region', e)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 transition-all ${activeDropdown === 'region' || selectedRegion
                                ? 'bg-blue-100 border-blue-300 text-blue-700'
                                : 'bg-white/60 border-white/60 text-slate-600 hover:bg-white/80'
                                }`}
                        >
                            <span>{selectedRegion || '서울 구'}</span>
                            <ChevronDown className={`w-4 h-4 transition-transform ${activeDropdown === 'region' ? 'rotate-180' : ''}`} />
                        </button>
                        {activeDropdown === 'region' && (
                            <div className="absolute top-full left-0 mt-2 w-64 bg-white/90 backdrop-blur-sm border border-white/60 rounded-xl shadow-lg p-2 z-50 max-h-80 overflow-y-auto scrollbar-hide">
                                <div className="grid grid-cols-3 gap-1">
                                    {SEOUL_DISTRICTS.map((option) => (
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
                        className="flex items-center gap-1.5 px-4 py-2 rounded-full border-2 border-red-200 bg-white/60 text-red-500 hover:bg-red-50 hover:border-red-300 transition-all text-sm font-medium ml-auto group"
                    >
                        <X className="w-3.5 h-3.5 group-hover:rotate-90 transition-transform" />
                        초기화
                    </button>
                </div>

                {/* Selected Filters Tags */}
                {(selectedRegion || selectedTransaction || selectedBuilding || searchQuery) && (
                    <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-white/40">
                        <span className="text-xs text-slate-500 font-medium">적용된 필터:</span>
                        {searchQuery && (
                            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-emerald-500 to-green-500 text-white text-sm shadow-md hover:shadow-lg transition-shadow">
                                <Search className="w-3 h-3" />
                                {searchQuery}
                                <button onClick={() => setSearchQuery('')} className="hover:bg-white/20 rounded-full p-0.5 transition-colors"><X className="w-3 h-3" /></button>
                            </span>
                        )}
                        {selectedRegion && (
                            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-blue-500 to-blue-600 text-white text-sm shadow-md hover:shadow-lg transition-shadow">
                                📍 {selectedRegion}
                                <button onClick={(e) => removeFilter('region', e)} className="hover:bg-white/20 rounded-full p-0.5 transition-colors"><X className="w-3 h-3" /></button>
                            </span>
                        )}
                        {selectedTransaction && (
                            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-purple-500 to-violet-500 text-white text-sm shadow-md hover:shadow-lg transition-shadow">
                                💰 {selectedTransaction}
                                <button onClick={(e) => removeFilter('transaction', e)} className="hover:bg-white/20 rounded-full p-0.5 transition-colors"><X className="w-3 h-3" /></button>
                            </span>
                        )}
                        {selectedBuilding && (
                            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 text-white text-sm shadow-md hover:shadow-lg transition-shadow">
                                🏠 {selectedBuilding}
                                <button onClick={(e) => removeFilter('building', e)} className="hover:bg-white/20 rounded-full p-0.5 transition-colors"><X className="w-3 h-3" /></button>
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
