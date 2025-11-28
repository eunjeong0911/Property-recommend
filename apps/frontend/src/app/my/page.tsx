/**
 * MyPage
 *
 * 마이 페이지
 *
 * - SideTab.tsx (좌측 사이드탭)
 * - Profile.tsx (프로필)
 * - PreferenceRanking.tsx (선호도 수정)
 * - Button.tsx (계정삭제, 프로필 사진 변경, 로그아웃 버튼)
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import SideTab from '@/components/SideTab'
import Profile from '@/components/Profile'
import PreferenceRanking from '@/components/PreferenceRanking'
import Button from '@/components/Button'
import { useStore } from '@/store/useStore'

export default function MyPage() {
  const [activeTab, setActiveTab] = useState<'mypage' | 'favorites'>('mypage')
  const { setUser } = useStore()
  const router = useRouter()

  // 선호도 제출 핸들러
  const handlePreferenceSubmit = async (data: { job: string; priorities: Record<string, number> }) => {
    console.log('선호도 저장:', data)
    alert('선호도가 저장되었습니다.')
  }

  // 계정 삭제 핸들러
  const handleDeleteAccount = () => {
    if (confirm('정말로 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
      setUser(null)
      alert('계정이 삭제되었습니다.')
      router.push('/')
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex gap-6">
        {/* 좌측 사이드 탭 */}
        <SideTab activeTab={activeTab} onTabChange={setActiveTab} />

        {/* 우측 컨텐츠 영역 */}
        <div className="flex-1">
          {activeTab === 'mypage' ? (
            <>
              {/* 프로필 */}
              <Profile />
              {/* 선호도 설정 */}
              <PreferenceRanking onSubmit={handlePreferenceSubmit} />

              {/* 계정 삭제 버튼 - 페이지 맨 하단 */}
              <div className="w-full max-w-4xl mx-auto mt-8 flex justify-center">
                <Button
                  variant="danger"
                  size="sm"
                  onClick={handleDeleteAccount}
                >
                  계정 삭제
                </Button>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-2xl font-bold mb-4">찜 매물 보기</h2>
              <p className="text-gray-600">찜한 매물 목록이 여기에 표시됩니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
