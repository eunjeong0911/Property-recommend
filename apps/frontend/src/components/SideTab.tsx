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
import { useParticleEffect } from '../hooks/useParticleEffect'

const NAV_ITEMS = [
  { label: '마이페이지', path: '/my' },
  { label: '찜 매물 보기', path: '/wishList' }
] as const

export default function SideTab() {
  const router = useRouter()
  const pathname = usePathname()
  const { triggerEffect } = useParticleEffect()

  const handleNavigate = (path: string, event: React.MouseEvent<HTMLButtonElement>) => {
    triggerEffect(event.currentTarget)
    if (pathname === path) return
    router.push(path)
  }

  return (
    <div className="bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md rounded-2xl border-2 border-white/40 shadow-lg p-4 w-64 h-fit">
      <div className="flex flex-col gap-2">
        {NAV_ITEMS.map(({ label, path }) => {
          const isActive = pathname === path

          return (
            <button
              key={path}
              onClick={(e) => handleNavigate(path, e)}
              className={`
                px-6 py-3 font-medium text-sm rounded-xl transition-all duration-200 text-left border-2
                ${isActive
                  ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.6)] ring-2 ring-blue-300'
                  : 'bg-white/50 border-white/40 text-slate-600 hover:bg-white/80 hover:border-white/80'
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
