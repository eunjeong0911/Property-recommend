/**
 * SideTab 컴포넌트
 *
 * 사이드 탭 컴포넌트
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
    <div className="bg-white rounded-lg shadow-sm p-4 w-64">
      <div className="flex flex-col gap-2">
        {NAV_ITEMS.map(({ label, path }) => {
          const isActive = pathname === path

          return (
            <button
              key={path}
              onClick={() => handleNavigate(path)}
              className={`
                px-6 py-3 font-medium text-sm rounded-md transition-all text-left
                ${isActive
                  ? 'bg-blue-500 text-white shadow-sm'
                  : 'text-gray-600 hover:bg-gray-50'
                }
              `}
            >
              {label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
