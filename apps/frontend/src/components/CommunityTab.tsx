/**
 * CommunityTab 컴포넌트
 *
 * 커뮤니티 탭 메뉴 컴포넌트
 *
 * 주요 기능:
 * - 탭 메뉴 표시 (자유게시판, 행정동 커뮤니티)
 * - 탭 선택 시 해당 게시판으로 전환
 * - 선택된 탭 하이라이트 표시
 */

'use client'

import { useParticleEffect } from '../hooks/useParticleEffect'

interface CommunityTabProps {
  activeTab: 'free' | 'region'
  onTabChange: (tab: 'free' | 'region') => void
}

export default function CommunityTab({ activeTab, onTabChange }: CommunityTabProps) {
  const { triggerEffect } = useParticleEffect()

  const handleTabChange = (tab: 'free' | 'region', event: React.MouseEvent<HTMLButtonElement>) => {
    triggerEffect(event.currentTarget)
    onTabChange(tab)
  }

  return (
    <div className="bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md rounded-2xl border-2 border-white/40 shadow-lg mb-6 p-1.5 w-fit mx-auto">
      <div className="flex gap-2">
        <button
          onClick={(e) => handleTabChange('free', e)}
          className={`
            flex-1 px-12 py-2 font-medium text-xs rounded-xl transition-all duration-200 border-2 whitespace-nowrap
            ${activeTab === 'free'
              ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.6)] ring-2 ring-blue-300'
              : 'bg-white/50 border-white/40 text-slate-600 hover:bg-white/80 hover:border-white/80'
            }
          `}
        >
          자유게시판
        </button>
        <button
          onClick={(e) => handleTabChange('region', e)}
          className={`
            flex-1 px-12 py-2 font-medium text-xs rounded-xl transition-all duration-200 border-2
            ${activeTab === 'region'
              ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.6)] ring-2 ring-blue-300'
              : 'bg-white/50 border-white/40 text-slate-600 hover:bg-white/80 hover:border-white/80'
            }
          `}
        >
          행정동
          <br />
          커뮤니티
        </button>
      </div>
    </div>
  )
}
