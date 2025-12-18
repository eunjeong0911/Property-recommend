'use client'

import { Inter } from 'next/font/google'
import { usePathname } from 'next/navigation'
import './globals.css'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import AuthProvider from '@/components/AuthProvider'
import dynamic from 'next/dynamic'

// 무거운 컴포넌트들을 lazy loading으로 변경하여 초기 로딩 성능 개선
const Aurora = dynamic(() => import('@/components/Aurora'), {
    ssr: false, // 서버 사이드 렌더링 비활성화
    loading: () => <div className="w-full h-full bg-[#F0F8FF]" /> // 로딩 중 기본 배경색
})

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const pathname = usePathname()
    const isLoginPage = pathname === '/login'

    return (
        <html lang="ko">
            <body className={inter.className}>
                <AuthProvider>
                    <div className="min-h-screen bg-[#F0F8FF]">
                        <div className="relative z-10">
                            <Header />
                            {children}
                            <Footer />
                        </div>
                    </div>
                </AuthProvider>
            </body>
        </html>
    )
}
