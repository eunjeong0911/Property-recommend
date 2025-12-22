/**
 * SideTab 컴포넌트
 *
 * 가로 탭 컴포넌트 (CommunityTab 스타일)
 *
 * 주요 기능:
 * - 마이페이지 탭
 * - 찜 매물 보기 탭
 */

'use client'

import { useRouter, usePathname } from 'next/navigation'

const NAV_ITEMS = [
  { label: '마이페이지', path: '/my' },
  { label: '찜 매물 보기', path: '/wishList' }
] as const

export default function SideTab() {
  const router = useRouter()
  const pathname = usePathname()

  const handleNavigate = (path: string) => {
    if (pathname === path) return
    router.push(path)
  }

  return (
    <div className="flex gap-2 border-b border-slate-200 mb-6">
      {NAV_ITEMS.map(({ label, path }) => {
        const isActive = pathname === path

        return (
          <button
            key={path}
            onClick={() => handleNavigate(path)}
            className={`
              px-6 py-2.5 font-semibold text-sm rounded-t-lg transition-all duration-200 whitespace-nowrap
              ${isActive
                ? 'bg-[#16375B] text-white shadow-md'
                : 'bg-transparent text-slate-600 hover:bg-slate-50 hover:text-[#16375B]'
              }
            `}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
