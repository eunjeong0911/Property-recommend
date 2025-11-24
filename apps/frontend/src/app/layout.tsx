import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Real Estate AI - 부동산 AI 추천',
  description: 'AI 기반 부동산 매물 검색 및 추천 서비스',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
