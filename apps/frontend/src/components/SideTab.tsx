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
    <div className="bg-white rounded-2xl border-2 border-slate-200 shadow-lg p-4 w-64 h-fit">
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
                  ? 'bg-slate-800 border-slate-700 text-white shadow-[0_0_15px_rgba(51,65,85,0.6)] ring-2 ring-slate-400'
                  : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'
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
