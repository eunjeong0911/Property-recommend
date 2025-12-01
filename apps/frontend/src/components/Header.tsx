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
import { useStore } from '@/store/useStore'

export default function Header() {
  const pathname = usePathname()
  const { user, setUser } = useStore()

  // 로그인 페이지에서는 Header를 표시하지 않음
  if (pathname === '/login') {
    return null
  }

  return (
    <header className="bg-white/30 backdrop-blur-md border-b border-white/20 py-4">
      <div className="max-w-7xl mx-auto px-4 flex justify-between items-center">
        {/* 로고 */}
        <Link
          href="/"
          className="text-2xl font-bold text-blue-600 hover:text-blue-700 transition-colors"
        >
          Ondo House
        </Link>

        {/* 버튼 영역 */}
        <div className="flex gap-4">
          {/* 커뮤니티 버튼 */}
          <Link
            href="/community"
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors font-medium"
          >
            커뮤니티
          </Link>

          {/* 온도 상세보기 버튼 */}
          <Link
            href="/temperature"
            className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition-colors font-medium"
          >
            온도 상세보기
          </Link>

          {/* 마이페이지 버튼 (로그인 상태일 때) */}
          {user && (
            <Link
              href="/my"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
            >
              마이페이지
            </Link>
          )}

          {/* 로그인 버튼 (비로그인 상태일 때 - 가장 오른쪽) */}
          {!user && (
            <Link
              href="/login"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
            >
              로그인
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
