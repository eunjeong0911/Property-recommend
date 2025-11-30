'use client'

import { Inter } from 'next/font/google'
import { usePathname } from 'next/navigation'
import './globals.css'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import Chatbot from '@/components/Chatbot'

import Aurora from '@/components/Aurora'

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
                <div className="fixed inset-0 -z-10 bg-[#F0F8FF]">
                    <Aurora
                        colorStops={['#90CAF9', '#80DEEA', '#E1F5FE']}
                        speed={0.5}
                    />
                </div>
                <div className="relative z-10">
                    <Header />
                    {children}
                    <Footer />
                    {!isLoginPage && <Chatbot />}
                </div>
            </body>
        </html>
    )
}
