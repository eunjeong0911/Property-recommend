/**
 * PreferenceFilter 컴포넌트
 * 
 * 사용자 선호도 기반 매물 필터링 컴포넌트
 * 
 * 주요 기능:
 * - 버튼 형태의 필터 옵션 선택 (대중교통, 주변 공원, 대학/직장 거리, 편의시설, 치안/안전, 허위매물, 초기화)
 * - 선택된 필터 조건 표시
 */

'use client';

import { useState } from 'react';

interface FilterOption {
    id: string;
    label: string;
    icon: string;
}

interface PreferenceFilterProps {
    onFilterChange?: (filters: string[]) => void;
    initialFilters?: string[];
}

const FILTER_OPTIONS: FilterOption[] = [
    { id: 'transport', label: '대중교통', icon: '🚇' },
    { id: 'park', label: '주변 공원', icon: '🌳' },
    { id: 'distance', label: '대학/직장 거리', icon: '🏢' },
    { id: 'facilities', label: '편의시설', icon: '🏪' },
    { id: 'safety', label: '치안/안전', icon: '⭐' },
    { id: 'fake', label: '허위매물', icon: '🚫' },
];

export default function PreferenceFilter({
    onFilterChange,
    initialFilters = []
}: PreferenceFilterProps) {
    const [selectedFilters, setSelectedFilters] = useState<Set<string>>(
        new Set(initialFilters)
    );

    const handleFilterClick = (filterId: string) => {
        const newFilters = new Set(selectedFilters);

        if (newFilters.has(filterId)) {
            newFilters.delete(filterId);
        } else {
            newFilters.add(filterId);
        }

        setSelectedFilters(newFilters);
        onFilterChange?.(Array.from(newFilters));
    };

    const handleReset = () => {
        setSelectedFilters(new Set());
        onFilterChange?.([]);
    };

    return (
        <div className="flex gap-2 items-center justify-center flex-wrap py-3">
            {FILTER_OPTIONS.map((option) => (
                <button
                    key={option.id}
                    className={`
            flex items-center gap-1.5 px-4 py-2 rounded-full
            border font-medium text-sm whitespace-nowrap
            transition-all duration-200
            ${selectedFilters.has(option.id)
                            ? 'border-blue-500 bg-blue-500 text-white'
                            : 'border-gray-300 text-gray-700 hover:border-blue-500'
                        }
          `}
                    onClick={() => handleFilterClick(option.id)}
                    type="button"
                >
                    <span className="text-base">{option.icon}</span>
                    <span>{option.label}</span>
                </button>
            ))}

            <button
                className={`
          flex items-center gap-1.5 px-4 py-2 rounded-full
          border border-red-400 font-medium text-sm whitespace-nowrap
          transition-all duration-200
          ${selectedFilters.size === 0
                        ? 'opacity-50 cursor-not-allowed text-red-400'
                        : 'text-red-500 hover:bg-red-500 hover:text-white'
                    }
        `}
                onClick={handleReset}
                disabled={selectedFilters.size === 0}
                type="button"
            >
                초기화
            </button>
        </div>
    );
}
