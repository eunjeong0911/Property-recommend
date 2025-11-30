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

interface CommunityTabProps {
  activeTab: 'free' | 'region'
  onTabChange: (tab: 'free' | 'region') => void
}

export default function CommunityTab({ activeTab, onTabChange }: CommunityTabProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm mb-6 p-2">
      <div className="flex gap-2">
        <button
          onClick={() => onTabChange('free')}
          className={`
            flex-1 px-6 py-3 font-medium text-sm rounded-md transition-all
            ${activeTab === 'free'
              ? 'bg-blue-500 text-white shadow-sm'
              : 'text-gray-600 hover:bg-gray-50'
            }
          `}
        >
          자유게시판
        </button>
        <button
          onClick={() => onTabChange('region')}
          className={`
            flex-1 px-6 py-3 font-medium text-sm rounded-md transition-all
            ${activeTab === 'region'
              ? 'bg-blue-500 text-white shadow-sm'
              : 'text-gray-600 hover:bg-gray-50'
            }
          `}
        >
          행정동 커뮤니티
        </button>
      </div>
    </div>
  )
}
