"use client";

import { useEffect, useMemo, useState } from "react";
import { useParticleEffect } from "@/hooks/useParticleEffect";
import type { PreferenceSurveyPayload } from "@/types/user";

const JOB_OPTIONS = [
  { value: "직장인", label: "직장인" },
  { value: "학생", label: "학생" },
  { value: "취준생", label: "취준생" },
  { value: "프리랜서", label: "프리랜서" },
  { value: "자영업", label: "자영업자" },
];
const FEATURES = ["주변 공원", "편의시설", "대중교통", "치안/안전", "허위매물"];
const RANKS = [1, 2, 3];

interface Props {
  onSubmit: (data: PreferenceSurveyPayload) => Promise<void>;
  initialJob?: string | null;
  initialPriorities?: Record<string, number>;
  submitLabel?: string;
  isSubmitting?: boolean;
  disabled?: boolean;
}

export default function PreferenceRanking({
  onSubmit,
  initialJob,
  initialPriorities,
  submitLabel = "선호도 저장",
  isSubmitting = false,
  disabled = false,
}: Props) {
  const [job, setJob] = useState(initialJob || JOB_OPTIONS[0].value);
  const [priorities, setPriorities] = useState<Record<string, number | undefined>>(initialPriorities || {});
  const { triggerEffect } = useParticleEffect();
  const controlDisabled = disabled || isSubmitting;

  useEffect(() => {
    if (initialJob) {
      setJob(initialJob);
    }
  }, [initialJob]);

  useEffect(() => {
    if (initialPriorities) {
      setPriorities(initialPriorities);
    } else {
      setPriorities({});
    }
  }, [initialPriorities]);

  const jobOptions = useMemo(() => {
    if (initialJob && !JOB_OPTIONS.some((option) => option.value === initialJob)) {
      return [{ value: initialJob, label: initialJob }, ...JOB_OPTIONS];
    }
    return JOB_OPTIONS;
  }, [initialJob]);

  const handleCheck = (feature: string, rank: number, event: React.ChangeEvent<HTMLInputElement>) => {
    if (controlDisabled) return;
    triggerEffect(event.target);
    setPriorities((prev: Record<string, number | undefined>) => {
      const newPriorities = { ...prev };

      if (newPriorities[feature] === rank) {
        delete newPriorities[feature];
        return newPriorities;
      }

      Object.keys(newPriorities).forEach((f) => {
        if (newPriorities[f] === rank) {
          delete newPriorities[f];
        }
      });

      newPriorities[feature] = rank;
      return newPriorities;
    });
  };

  const handleJobChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (controlDisabled) return;
    triggerEffect(e.target);
    setJob(e.target.value);
  };

  const handleSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
    if (controlDisabled) return;
    triggerEffect(e.currentTarget);
    const cleanPriorities: Record<string, number> = {};
    Object.entries(priorities).forEach(([key, value]) => {
      if (value !== undefined) {
        cleanPriorities[key] = value;
      }
    });
    await onSubmit({ job, priorities: cleanPriorities });
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-8 rounded-3xl border-2 border-white/40 bg-gradient-to-b from-sky-100/95 to-blue-200/95 backdrop-blur-xl shadow-2xl">
      <h2 className="text-2xl font-bold mb-8 text-slate-800">매물 선호도 조사</h2>

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
            disabled={controlDisabled}
            className="w-full max-w-xs p-2.5 border border-white/40 rounded-xl bg-white/60 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 disabled:bg-gray-100 disabled:text-gray-400"
          >
            {jobOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-10">
        <div className="flex items-center mb-4">
          <span className="bg-blue-500 text-white font-bold rounded-full w-8 h-8 flex items-center justify-center mr-3 shadow-lg shadow-blue-500/30">02</span>
          <h3 className="text-lg font-bold text-slate-800">매물 선택 우선순위 (3위까지)</h3>
          <span className="ml-2 text-sm text-slate-500">* 우선순위는 매물 추천에 반영됩니다.</span>
        </div>

        <div className="ml-11 overflow-x-auto rounded-2xl border border-white/40 bg-white/40 backdrop-blur-sm shadow-sm">
          <table className="w-full text-center border-collapse">
            <thead>
              <tr className="border-b border-white/40 bg-white/20">
                <th className="p-4 text-slate-700"></th>
                {RANKS.map((rank) => (
                  <th key={rank} className="p-4 font-medium text-slate-700">
                    {rank}위
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {FEATURES.map((feature) => (
                <tr key={feature} className="border-b border-white/40 last:border-b-0 hover:bg-white/30 transition-colors">
                  <td className="p-4 text-left font-medium text-slate-700">{feature}</td>
                  {RANKS.map((rank) => (
                    <td key={rank} className="p-4">
                      <input
                        type="checkbox"
                        className="w-5 h-5 rounded border-white/60 text-blue-600 focus:ring-blue-500 bg-white/60 cursor-pointer disabled:cursor-not-allowed"
                        checked={priorities[feature] === rank}
                        disabled={controlDisabled}
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
          disabled={controlDisabled}
          className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-bold shadow-[0_0_15px_rgba(37,99,235,0.4)] transition-all duration-200 hover:scale-105 active:scale-95 disabled:bg-gray-300 disabled:shadow-none disabled:hover:scale-100"
        >
          {isSubmitting ? "저장 중..." : submitLabel}
        </button>
      </div>
    </div>
  );
}
