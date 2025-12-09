/**
 * Temperature 컴포넌트
 * 
 * 온도 정보를 표시하는 컴포넌트
 * 
 * 주요 기능:
 * - 온도 바 표시
 */

'use client';

import { useState, useEffect } from 'react';
import { useParticleEffect } from '../hooks/useParticleEffect';

interface TemperatureProps {
    label: string;
    value: number;
    maxValue?: number;
}

export default function Temperature({ label, value, maxValue = 1 }: TemperatureProps) {
    const [animatedValue, setAnimatedValue] = useState(0);
    const percentage = (animatedValue / maxValue) * 100;
    const { triggerEffect } = useParticleEffect();

    useEffect(() => {
        const timer = setTimeout(() => {
            setAnimatedValue(value);
        }, 100);

        return () => clearTimeout(timer);
    }, [value]);

    const handleClick = (e: React.MouseEvent) => {
        triggerEffect(e.currentTarget as HTMLElement);
    };

    return (
        <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={handleClick}
        >
            <span className="text-sm font-medium text-slate-700 w-24 flex-shrink-0">{label}</span>
            <div className="flex-1 bg-white/60 rounded-full h-2.5 overflow-hidden border border-purple-200/40 shadow-inner">
                <div
                    className="h-full rounded-full transition-all duration-1000 ease-out bg-gradient-to-r from-purple-500 via-blue-500 to-cyan-400 shadow-sm"
                    style={{ width: `${percentage}%` }}
                />
            </div>
            <span className="text-sm font-bold text-slate-800 w-12 text-right">
                {value.toFixed(1)}
            </span>
        </div>
    );
}
