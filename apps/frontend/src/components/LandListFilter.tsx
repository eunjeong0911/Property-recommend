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
 * - 추천 매물 새로고침 버튼
 */

'use client';

import { useState } from 'react';

interface FilterState {
    region: string;
    type: string;
    price: string;
    rooms: string;
}

export default function LandListFilter() {
    const [filters, setFilters] = useState<FilterState>({
        region: '',
        type: '',
        price: '',
        rooms: ''
    });

    const handleFilterChange = (key: keyof FilterState, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const handleReset = () => {
        setFilters({ region: '', type: '', price: '', rooms: '' });
    };

    const handleRefresh = () => {
        console.log('추천 매물 새로고침');
    };

    return (
        <div className="flex items-center gap-3 py-4">
            {/* 지역 */}
            <select
                value={filters.region}
                onChange={(e) => handleFilterChange('region', e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:border-blue-500"
            >
                <option value="">지역</option>
                <option value="금천구">금천구</option>
                <option value="광진구">광진구</option>
            </select>

            {/* 거주형태 */}
            <select
                value={filters.type}
                onChange={(e) => handleFilterChange('type', e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:border-blue-500"
            >
                <option value="">거주형태</option>
                <option value="원룸">원룸</option>
                <option value="투룸">투룸</option>
                <option value="오피스텔">오피스텔</option>
            </select>

            {/* 가격 */}
            <select
                value={filters.price}
                onChange={(e) => handleFilterChange('price', e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:border-blue-500"
            >
                <option value="">가격</option>
                <option value="0-500">~500만원</option>
                <option value="500-1000">500~1000만원</option>
                <option value="1000+">1000만원~</option>
            </select>

            {/* 면적(평) */}
            <select
                value={filters.rooms}
                onChange={(e) => handleFilterChange('rooms', e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:border-blue-500"
            >
                <option value="">면적(평)</option>
                <option value="5">5평</option>
                <option value="7">7평</option>
                <option value="10">10평</option>
                <option value="12">12평</option>
            </select>

            {/* 초기화 */}
            <button
                onClick={handleReset}
                className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 hover:bg-gray-50"
            >
                초기화
            </button>

            {/* 추천 매물 새로고침 */}
            <button
                onClick={handleRefresh}
                className="ml-auto px-6 py-2 border-2 border-gray-800 rounded-full bg-white text-gray-800 font-medium hover:bg-gray-800 hover:text-white transition-colors flex items-center gap-2"
            >
                <span className="text-xl">🔄</span>
                추천 매물 새로고침
            </button>
        </div>
    );
}
