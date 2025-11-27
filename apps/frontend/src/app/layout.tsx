'use client'

import { Inter } from 'next/font/google'
import { usePathname } from 'next/navigation'
import './globals.css'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import Chatbot from '@/components/Chatbot'

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
                <Header />
                {children}
                <Footer />
                {!isLoginPage && <Chatbot />}
            </body>
        </html>
    )
}
