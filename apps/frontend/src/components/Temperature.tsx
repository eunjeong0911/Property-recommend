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

interface TemperatureProps {
    label: string;
    value: number;
    maxValue?: number;
}

export default function Temperature({ label, value, maxValue = 1 }: TemperatureProps) {
    const [animatedValue, setAnimatedValue] = useState(0);
    const percentage = (animatedValue / maxValue) * 100;

    useEffect(() => {
        const timer = setTimeout(() => {
            setAnimatedValue(value);
        }, 100);

        return () => clearTimeout(timer);
    }, [value]);

    return (
        <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-slate-700 w-24 flex-shrink-0">{label}</span>
            <div className="flex-1 bg-white/50 rounded-full h-2.5 overflow-hidden border border-white/40 shadow-inner">
                <div
                    className="h-full rounded-full transition-all duration-1000 ease-out bg-gradient-to-r from-sky-400 to-blue-500 shadow-sm"
                    style={{ width: `${percentage}%` }}
                />
            </div>
            <span className="text-sm font-bold text-slate-800 w-12 text-right">
                {value.toFixed(1)}
            </span>
        </div>
    );
}
