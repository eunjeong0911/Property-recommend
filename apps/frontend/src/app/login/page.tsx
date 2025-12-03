"use client";

import { useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";
import Login from "@/components/Login";
import { signIn, useSession } from "next-auth/react";
import AuthProvider from "@/components/AuthProvider";

/**
 * LoginPage
 *
 * 로그인 페이지
 *
 * - Login.tsx (로그인 폼)
 */
function LoginContent() {
    const router = useRouter();
    const { data: session, status } = useSession();

    useEffect(() => {
        if (status === 'authenticated' && session?.user) {
            // 로그인 성공 후 리다이렉트 처리
            if (session.user.isNewUser && !session.user.surveyCompleted) {
                router.push('/preferenceSurvey');
            } else {
                router.push('/main');
            }
        }
    }, [status, session, router]);

    if (status === 'authenticated') {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen py-2">
                <p>로그인 중...</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center min-h-screen py-2">
            <Suspense fallback={<div>로딩중...</div>}>
            <Login />
            </Suspense>
            <div className="mt-4">
                <button
                    onClick={() => signIn("google")}
                    className="px-4 py-2 font-bold text-white bg-blue-500 rounded hover:bg-blue-700"
                >
                    Google로 로그인
                </button>
            </div>
        </div>
    );
}

export default function LoginPage() {
    return (
        <AuthProvider>
            <LoginContent />
        </AuthProvider>
    );
}
