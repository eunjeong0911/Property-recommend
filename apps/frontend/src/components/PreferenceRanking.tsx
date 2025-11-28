"use client";

import { useState } from "react";

const JOBS = ["직장인", "학생", "취준생", "프리랜서", "자영업"];
const FEATURES = ["주변공원", "편의시설", "대학가", "인구밀집도", "치안/안전", "허위매물"];
const RANKS = [1, 2, 3, 4, 5];

interface Props {
    onSubmit: (data: { job: string; priorities: Record<string, number> }) => Promise<void>;
}

export default function PreferenceRanking({ onSubmit }: Props) {
    const [job, setJob] = useState(JOBS[0]);
    // Store rank for each feature: { "주변공원": 1, "편의시설": 2, ... }
    const [priorities, setPriorities] = useState<Record<string, number | undefined>>({});

    const handleCheck = (feature: string, rank: number) => {
        setPriorities((prev) => {
            const newPriorities = { ...prev };

            // If clicking the same cell, toggle off
            if (newPriorities[feature] === rank) {
                delete newPriorities[feature];
                return newPriorities;
            }

            // 1. Remove any other feature that currently holds this rank (One feature per rank)
            Object.keys(newPriorities).forEach((f) => {
                if (newPriorities[f] === rank) {
                    delete newPriorities[f];
                }
            });

            // 2. Set the new rank for this feature (One rank per feature)
            newPriorities[feature] = rank;

            return newPriorities;
        });
    };

    const handleSubmit = async () => {
        const cleanPriorities: Record<string, number> = {};
        Object.entries(priorities).forEach(([k, v]) => {
            if (v !== undefined) cleanPriorities[k] = v;
        });
        await onSubmit({ job, priorities: cleanPriorities });
    };

    return (
        <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-2xl font-bold mb-8">매물 선호도 조사</h2>

            {/* Job Selection */}
            <div className="mb-10">
                <div className="flex items-center mb-4">
                    <span className="bg-yellow-400 text-white font-bold rounded-full w-8 h-8 flex items-center justify-center mr-3">01</span>
                    <h3 className="text-lg font-bold">직업</h3>
                </div>
                <div className="ml-11 p-6 border rounded-lg bg-white">
                    <label className="block font-bold mb-2">직업</label>
                    <select
                        value={job}
                        onChange={(e) => setJob(e.target.value)}
                        className="w-full max-w-xs p-2 border rounded-md"
                    >
                        {JOBS.map(j => <option key={j} value={j}>{j}</option>)}
                    </select>
                </div>
            </div>

            {/* Priority Matrix */}
            <div className="mb-10">
                <div className="flex items-center mb-4">
                    <span className="bg-yellow-400 text-white font-bold rounded-full w-8 h-8 flex items-center justify-center mr-3">02</span>
                    <h3 className="text-lg font-bold">매물 선택 우선순위 (5순위까지)</h3>
                    <span className="ml-2 text-sm text-gray-500">*해당 우선순위는 매물 추천에 반영됩니다.(추후에 변경 가능합니다)</span>
                </div>

                <div className="ml-11 overflow-x-auto">
                    <table className="w-full text-center border-collapse">
                        <thead>
                            <tr>
                                <th className="p-4"></th>
                                {RANKS.map(r => <th key={r} className="p-4 font-medium">{r}순위</th>)}
                            </tr>
                        </thead>
                        <tbody>
                            {FEATURES.map(feature => (
                                <tr key={feature} className="border-b last:border-b-0">
                                    <td className="p-4 text-left font-medium">{feature}</td>
                                    {RANKS.map(rank => (
                                        <td key={rank} className="p-4">
                                            <input
                                                type="checkbox"
                                                className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                checked={priorities[feature] === rank}
                                                onChange={() => handleCheck(feature, rank)}
                                            />
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="flex justify-end">
                <button
                    onClick={handleSubmit}
                    className="px-8 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-bold"
                >
                    완료
                </button>
            </div>
        </div>
    );
}
