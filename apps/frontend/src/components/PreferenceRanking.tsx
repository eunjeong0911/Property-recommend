"use client";

import { useState } from "react";
import { useParticleEffect } from "../hooks/useParticleEffect";

const JOBS = ["직장인", "학생", "취준생", "프리랜서", "자영업"];
const FEATURES = ["주변공원", "편의시설", "역세권", "치안/안전", "허위매물"];
const RANKS = [1, 2, 3];

interface Props {
    onSubmit: (data: { job: string; priorities: Record<string, number> }) => Promise<void>;
}

export default function PreferenceRanking({ onSubmit }: Props) {
    const [job, setJob] = useState(JOBS[0]);
    // Store rank for each feature: { "주변공원": 1, "편의시설": 2, ... }
    const [priorities, setPriorities] = useState<Record<string, number | undefined>>({});
    const { triggerEffect } = useParticleEffect();

    const handleCheck = (feature: string, rank: number, event: React.ChangeEvent<HTMLInputElement>) => {
        triggerEffect(event.target);
        setPriorities((prev: Record<string, number | undefined>) => {
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

    const handleJobChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        triggerEffect(e.target);
        setJob(e.target.value);
    };

    const handleSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
        triggerEffect(e.currentTarget);
        const cleanPriorities: Record<string, number> = {};
        Object.entries(priorities).forEach(([k, v]) => {
            if (v !== undefined) cleanPriorities[k] = v;
        });
        await onSubmit({ job, priorities: cleanPriorities });
    };

    return (
        <div className="w-full max-w-4xl mx-auto p-8 rounded-3xl border-2 border-white/40 bg-gradient-to-b from-sky-100/95 to-blue-200/95 backdrop-blur-xl shadow-2xl">
            <h2 className="text-2xl font-bold mb-8 text-slate-800">매물 선호도 조사</h2>

            {/* Job Selection */}
            <div className="mb-10">
                <div className="flex items-center mb-4">
                    <span className="bg-blue-500 text-white font-bold rounded-full w-8 h-8 flex items-center justify-center mr-3 shadow-lg shadow-blue-500/30">01</span>
                    <h3 className="text-lg font-bold text-slate-800">직업</h3>
                </div>
                <div className="ml-11 p-6 border border-white/40 rounded-2xl bg-white/40 backdrop-blur-sm shadow-sm">
                    <label className="block font-bold mb-2 text-slate-700">직업</label>
                    <select
                        value={job}
                        onChange={handleJobChange}
                        className="w-full max-w-xs p-2.5 border border-white/40 rounded-xl bg-white/60 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700"
                    >
                        {JOBS.map(j => <option key={j} value={j}>{j}</option>)}
                    </select>
                </div>
            </div>

            {/* Priority Matrix */}
            <div className="mb-10">
                <div className="flex items-center mb-4">
                    <span className="bg-blue-500 text-white font-bold rounded-full w-8 h-8 flex items-center justify-center mr-3 shadow-lg shadow-blue-500/30">02</span>
                    <h3 className="text-lg font-bold text-slate-800">매물 선택 우선순위 (3순위까지)</h3>
                    <span className="ml-2 text-sm text-slate-500">*해당 우선순위는 매물 추천에 반영됩니다.(추후에 변경 가능합니다)</span>
                </div>

                <div className="ml-11 overflow-x-auto rounded-2xl border border-white/40 bg-white/40 backdrop-blur-sm shadow-sm">
                    <table className="w-full text-center border-collapse">
                        <thead>
                            <tr className="border-b border-white/40 bg-white/20">
                                <th className="p-4 text-slate-700"></th>
                                {RANKS.map(r => <th key={r} className="p-4 font-medium text-slate-700">{r}순위</th>)}
                            </tr>
                        </thead>
                        <tbody>
                            {FEATURES.map(feature => (
                                <tr key={feature} className="border-b border-white/40 last:border-b-0 hover:bg-white/30 transition-colors">
                                    <td className="p-4 text-left font-medium text-slate-700">{feature}</td>
                                    {RANKS.map(rank => (
                                        <td key={rank} className="p-4">
                                            <input
                                                type="checkbox"
                                                className="w-5 h-5 rounded border-white/60 text-blue-600 focus:ring-blue-500 bg-white/60 cursor-pointer"
                                                checked={priorities[feature] === rank}
                                                onChange={(e) => handleCheck(feature, rank, e)}
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
                    className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-bold shadow-[0_0_15px_rgba(37,99,235,0.4)] transition-all duration-200 hover:scale-105 active:scale-95"
                >
                    완료
                </button>
            </div>
        </div>
    );
}
