/**
 * LandList 컴포넌트
 * 
 * 매물 목록을 표시하는 컴포넌트
 * 
 * 주요 기능:
 * - 매물 4개씩 한줄로 목록 표시
 * - 매물 정보 표시 (ex. 월세 5,000만원/35만원 )
 * - 매물 선택 기능
 * 
 * 사용 컴포넌트:
 * - LandImage: 매물 사진 표시
 */

'use client';

import { useEffect, useState } from 'react';
import LandImage from './LandImage';
import { Land, LandFilterParams } from '../types/land';
import { fetchLands } from '../api/landApi';

interface LandListProps {
    filterParams?: LandFilterParams;
}

export default function LandList({ filterParams }: LandListProps) {
    const [lands, setLands] = useState<Land[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadLands = async () => {
            try {
                setLoading(true);
                const data = await fetchLands(filterParams);
                setLands(data);
                setError(null);
            } catch (err) {
                console.error('Failed to fetch lands:', err);
                setError('매물 정보를 불러오는데 실패했습니다.');
            } finally {
                setLoading(false);
            }
        };

        loadLands();
    }, [filterParams]);

    if (loading) {
        return (
            <div className="p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl overflow-visible min-h-[300px] flex items-center justify-center">
                <div className="text-slate-600 flex flex-col items-center gap-2">
                    <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                    <p>매물 정보를 불러오는 중...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl overflow-visible min-h-[300px] flex items-center justify-center">
                <div className="text-red-500 text-center">
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    if (lands.length === 0) {
        return (
            <div className="p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl overflow-visible min-h-[300px] flex items-center justify-center">
                <div className="text-slate-600 text-center">
                    <p>조건에 맞는 매물이 없습니다.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-xl overflow-visible">
            <div className="grid grid-cols-4 gap-6">
                {lands.slice(0, 4).map((land) => (
                    <LandImage
                        key={land.id}
                        id={String(land.id)}
                        images={land.image ? [land.image] : undefined}
                        temperature={land.temperature}
                        price={land.price}
                    />
                ))}
            </div>
        </div>
    );
}
