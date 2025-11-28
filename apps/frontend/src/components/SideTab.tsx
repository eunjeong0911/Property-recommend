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

interface SideTabProps {
  activeTab: 'mypage' | 'favorites'
  onTabChange: (tab: 'mypage' | 'favorites') => void
}

export default function SideTab({ activeTab, onTabChange }: SideTabProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 w-64">
      <div className="flex flex-col gap-2">
        {/* 마이페이지 탭 */}
        <button
          onClick={() => onTabChange('mypage')}
          className={`
            px-6 py-3 font-medium text-sm rounded-md transition-all text-left
            ${activeTab === 'mypage'
              ? 'bg-blue-500 text-white shadow-sm'
              : 'text-gray-600 hover:bg-gray-50'
            }
          `}
        >
          마이페이지
        </button>

        {/* 찜 매물 보기 탭 */}
        <button
          onClick={() => onTabChange('favorites')}
          className={`
            px-6 py-3 font-medium text-sm rounded-md transition-all text-left
            ${activeTab === 'favorites'
              ? 'bg-blue-500 text-white shadow-sm'
              : 'text-gray-600 hover:bg-gray-50'
            }
          `}
        >
          찜 매물 보기
        </button>
      </div>
    </div>
  )
}
