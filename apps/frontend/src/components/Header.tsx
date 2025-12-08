/**
 * Header 컴포넌트
 *
 * 상단 헤더 영역을 담당하는 컴포넌트
 *
 * 주요 기능:
 * - 로고 표시 (로고 클릭 시 메인 페이지로 이동)
 * - 네비게이션 메뉴 (커뮤니티)
 * - 사용자 인증 상태 표시
 *   - 비로그인: 로그인 버튼
 *   - 로그인: 마이페이지 링크
 * - 로그인 페이지에서는 Header 숨김
 */

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useSession } from 'next-auth/react'

export default function Header() {
  const pathname = usePathname()
  const { data: session, status } = useSession()

  // 로그인 페이지 여부 확인
  const isLoginPage = pathname === '/login'

  return (
    <header className="bg-gradient-to-r from-slate-800/95 via-slate-900/95 to-slate-800/95 backdrop-blur-md border-b border-slate-700/50 py-4 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 flex justify-between items-center">
        {/* 로고 */}
        <Link
          href="/"
          className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent hover:from-cyan-300 hover:to-blue-300 transition-all"
        >
          Ondo House
        </Link>

        {/* 버튼 영역 */}
        <div className="flex gap-3">
          {/* 서비스 소개 버튼 */}
          <Link
            href="/serviceIns"
            className="px-4 py-2 bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded-lg hover:bg-purple-500/30 hover:text-purple-200 transition-all font-medium text-sm"
          >
            서비스 소개
          </Link>

          {/* 커뮤니티 버튼 */}
          <Link
            href="/community"
            className="px-4 py-2 bg-slate-600/30 text-slate-300 border border-slate-500/30 rounded-lg hover:bg-slate-600/50 hover:text-white transition-all font-medium text-sm"
          >
            커뮤니티
          </Link>

          {/* 온도 상세보기 버튼 */}
          <Link
            href="/temperature"
            className="px-4 py-2 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-lg hover:bg-emerald-500/30 hover:text-emerald-200 transition-all font-medium text-sm"
          >
            온도 상세보기
          </Link>

          {/* 마이페이지 버튼 (로그인 상태일 때) */}
          {session && (
            <Link
              href="/my"
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-500 hover:to-cyan-500 transition-all font-medium text-sm shadow-lg shadow-blue-500/25"
            >
              마이페이지
            </Link>
          )}

          {/* 로그인 버튼 (비로그인 상태이고 로그인 페이지가 아닐 때) */}
          {!session && status !== 'loading' && !isLoginPage && (
            <Link
              href="/login"
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-500 hover:to-cyan-500 transition-all font-medium text-sm shadow-lg shadow-blue-500/25"
            >
              로그인
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
