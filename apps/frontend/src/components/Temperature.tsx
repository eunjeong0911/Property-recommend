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
            <span className="text-sm text-gray-700 w-24 flex-shrink-0">{label}</span>
            <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-700 ease-out bg-gradient-to-r from-blue-400 via-blue-500 to-blue-600"
                    style={{ width: `${percentage}%` }}
                />
            </div>
            <span className="text-sm font-medium text-gray-800 w-12 text-right">
                {value.toFixed(1)}
            </span>
        </div>
    );
}
