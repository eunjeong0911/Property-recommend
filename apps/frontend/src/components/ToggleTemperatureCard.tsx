/**
 * ToggleTemperatureCard 컴포넌트
 *
 * 온도 정보를 카드 형태로 표시하고, 자세히 보기 버튼으로 상세 내용을 토글하는 컴포넌트
 *
 * 주요 기능:
 * - 기본 카드: 아이콘, 제목, 간단한 설명
 * - 자세히 보기 클릭 시 상세 내용 토글
 */

'use client';

import { useState } from 'react';

export interface ToggleTemperatureCardProps {
    icon: string;
    title: string;
    description: string;
    color: string;
    details: {
        subtitle: string;
        howItWorks: string;
        examples: string[];
    };
}

export default function ToggleTemperatureCard({
    icon,
    title,
    description,
    color,
    details
}: ToggleTemperatureCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <div className={`rounded-2xl border-2 border-white/40 bg-gradient-to-br ${color} backdrop-blur-md shadow-lg transition-all duration-300`}>
            {/* 카드 헤더 */}
            <div className="p-6">
                <div className="flex items-center gap-3 mb-3">
                    <span className="text-3xl">{icon}</span>
                    <h3 className="text-xl font-bold text-slate-800">{title}</h3>
                </div>

                <p className="text-slate-700 text-sm mb-4 leading-relaxed">
                    {description}
                </p>

                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="w-full py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors text-sm font-medium"
                >
                    {isExpanded ? '접기 ▲' : '자세히 보기 ▼'}
                </button>
            </div>

            {/* 상세 내용 (토글) */}
            {isExpanded && (
                <div className="px-6 pb-6 border-t border-white/40 pt-6 space-y-4">
                    <div>
                        <h4 className="font-bold text-slate-800 mb-2">{details.subtitle}</h4>
                        <p className="text-sm text-slate-700 leading-relaxed">{details.howItWorks}</p>
                    </div>

                    <div>
                        <h4 className="font-bold text-slate-800 mb-2">주요 고려 사항:</h4>
                        <ul className="space-y-1.5">
                            {details.examples.map((example, index) => (
                                <li key={index} className="flex items-start gap-2 text-sm text-slate-700">
                                    <span className="text-blue-600 mt-0.5">•</span>
                                    <span>{example}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}
        </div>
    );
}
