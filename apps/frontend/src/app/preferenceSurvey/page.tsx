/**
 * PreferenceSurveyPage 컴포넌트
 * 
 * 선호도 조사 페이지 (회원가입후 처음 보여주는 화면)
 * 
 * - Header.tsx (헤더)
 * - PreferenceRanking.tsx (선호도 조사)
 * - Footer.tsx (푸터)
 * 
 */
"use client";

import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import AuthProvider from "@/components/AuthProvider";
import PreferenceRanking from "@/components/PreferenceRanking";

function SurveyPageContent() {
    const router = useRouter();
    const { data: session, update } = useSession();

    const handleSurveySubmit = async (data: any) => {
        // console.log("Survey Data:", data);
        // Simulate backend call
        setTimeout(async () => {
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
        <div className="min-h-screen flex flex-col bg-white">
            <main className="flex-grow container mx-auto py-12 px-4">
                <PreferenceRanking onSubmit={handleSurveySubmit} />
            </main>
        </div>
    );
}

export default function PreferenceSurveyPage() {
    return (
        <AuthProvider>
            <SurveyPageContent />
        </AuthProvider>
    );
}
