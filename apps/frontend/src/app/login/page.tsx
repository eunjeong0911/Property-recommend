"use client";

import Login from "@/components/Login";
import { signIn } from "next-auth/react";
import AuthProvider from "@/components/AuthProvider";

/**
 * LoginPage
 *
 * 로그인 페이지
 *
 * - Login.tsx (로그인 폼)
 */
export default function LoginPage() {
    return (
        <AuthProvider>
            <div className="flex flex-col items-center justify-center min-h-screen py-2">
                <Login />
                <div className="mt-4">
                    <button
                        onClick={() => signIn("google")}
                        className="px-4 py-2 font-bold text-white bg-blue-500 rounded hover:bg-blue-700"
                    >
                        Google로 로그인
                    </button>
                </div>
            </div>
        </AuthProvider>
    );
}
