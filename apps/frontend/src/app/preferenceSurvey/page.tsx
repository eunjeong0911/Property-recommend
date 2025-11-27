"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import AuthProvider from "@/components/AuthProvider";

function SurveyForm() {
    const router = useRouter();
    const { data: session, update } = useSession();
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        // TODO: Send data to backend
        // await axios.post('/api/preference', { ... });

        // Simulate backend update
        setTimeout(async () => {
            // Update session to mark survey as completed
            await update({
                ...session,
                user: {
                    ...session?.user,
                    surveyCompleted: true,
                },
            });

            alert("설문조사가 완료되었습니다! 메인 페이지로 이동합니다.");
            router.push("/main");
        }, 1000);
    };

    return (
        <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md mt-10">
            <h1 className="text-2xl font-bold mb-6 text-center">맞춤형 부동산 추천을 위한 설문조사</h1>
            <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                    <label className="block mb-2 font-medium">선호하는 지역</label>
                    <select className="w-full p-2 border rounded">
                        <option>서울</option>
                        <option>경기</option>
                        <option>인천</option>
                    </select>
                </div>

                <div>
                    <label className="block mb-2 font-medium">예산 범위</label>
                    <input type="range" className="w-full" />
                    <div className="flex justify-between text-sm text-gray-500">
                        <span>1억</span>
                        <span>10억+</span>
                    </div>
                </div>

                <div>
                    <label className="block mb-2 font-medium">관심 있는 부동산 유형</label>
                    <div className="space-x-4">
                        <label><input type="checkbox" className="mr-1" /> 아파트</label>
                        <label><input type="checkbox" className="mr-1" /> 오피스텔</label>
                        <label><input type="checkbox" className="mr-1" /> 주택</label>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                    {loading ? "처리 중..." : "제출하기"}
                </button>
            </form>
        </div>
    );
}

export default function PreferenceSurveyPage() {
    return (
        <AuthProvider>
            <div className="min-h-screen bg-gray-50 py-12">
                <SurveyForm />
            </div>
        </AuthProvider>
    );
}
