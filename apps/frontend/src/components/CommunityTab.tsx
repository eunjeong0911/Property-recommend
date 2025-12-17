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
    <div className="flex gap-2">
      <button
        onClick={(e) => handleTabChange('free', e)}
        className={`
          px-6 py-2.5 font-semibold text-sm rounded-t-lg transition-all duration-200 whitespace-nowrap
          ${activeTab === 'free'
            ? 'bg-[#16375B] text-white'
            : 'bg-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
          }
        `}
      >
        자유게시판
      </button>
      <button
        onClick={(e) => handleTabChange('region', e)}
        className={`
          px-6 py-2.5 font-semibold text-sm rounded-t-lg transition-all duration-200
          ${activeTab === 'region'
            ? 'bg-[#16375B] text-white'
            : 'bg-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
          }
        `}
      >
        행정동 커뮤니티
      </button>
    </div>
  )
}
