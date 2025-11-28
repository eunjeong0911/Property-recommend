/**
 * WishListPage 컴포넌트
 *
 * 찜 리스트 페이지
 *
 * - LandImage.tsx (매물 이미지)
 * - LandList.tsx (매물 목록) -> 체크박스 때문에 현재 사용 X
 * - Pagination.tsx (페이지네이션)
 * - Button.tsx (비교하기 버튼)
 * - Comparison.tsx (매물 비교)
 */

'use client'

import { useState } from 'react'
import SideTab from '@/components/SideTab'
import LandImage from '@/components/LandImage'
import Pagination from '@/components/Pagination'
import Comparison from '@/components/Comparison'
import Button from '@/components/Button'

// 테스트용 찜 매물 데이터
const FAVORITE_LANDS = [
  { id: '1', temperature: 0.4, price: '월세 1,000 / 68' },
  { id: '2', temperature: 0.6, price: '월세 2,000 / 75' },
  { id: '3', temperature: 0.8, price: '월세 1,500 / 60' },
  { id: '4', temperature: 0.5, price: '월세 3,000 / 80' }
]

export default function WishListPage() {
  const [showComparison, setShowComparison] = useState(false)
  const [selectedLands, setSelectedLands] = useState<string[]>([])

  // 매물 선택/해제 핸들러
  const handleSelectLand = (landId: string) => {
    setSelectedLands((prev) => {
      if (prev.includes(landId)) {
        // 이미 선택된 경우 제거
        return prev.filter((id) => id !== landId)
      }
      if (prev.length < 3) {
        // 최대 3개까지만 선택 가능
        return [...prev, landId]
      }
      alert('최대 3개까지만 선택할 수 있습니다.')
      return prev
    })
  }

  // 선택된 매물 데이터 가져오기
  const getSelectedLandData = () => {
    return selectedLands
      .map((id) => FAVORITE_LANDS.find((land) => land.id === id)!)
      .filter(Boolean)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex gap-6">
        {/* 좌측 사이드 탭 */}
        <SideTab />

        {/* 우측 컨텐츠 영역 */}
        <div className="flex-1">
          <h1 className="text-3xl font-bold mb-6">찜 매물 목록</h1>

          {!showComparison ? (
            <>
              {/* 선택 안내 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-sm text-blue-800">
                  비교할 매물을 선택하세요 (최대 3개) - 현재 {selectedLands.length}개 선택됨
                </p>
              </div>

              {/* 찜한 매물 목록 - Pagination으로 관리 */}
              <Pagination
                items={FAVORITE_LANDS}
                pageSize={4}
                renderItem={(land) => (
                  <div className="inline-block w-1/4 p-2">
                    <div className="relative">
                      {/* 체크박스 */}
                      <div className="absolute top-2 left-2 z-10">
                        <input
                          type="checkbox"
                          checked={selectedLands.includes(land.id)}
                          onChange={() => handleSelectLand(land.id)}
                          className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                        />
                      </div>
                      <LandImage
                        key={land.id}
                        id={land.id}
                        temperature={land.temperature}
                        price={land.price}
                      />
                    </div>
                  </div>
                )}
                emptyMessage={
                  <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                    <p className="text-gray-600">찜한 매물이 없습니다.</p>
                  </div>
                }
              />

              {/* 비교하기 버튼 */}
              <div className="flex justify-center mt-8">
                <Button
                  variant="primary"
                  onClick={() => setShowComparison(true)}
                  disabled={selectedLands.length < 2}
                >
                  매물 비교하기 ({selectedLands.length}/3)
                </Button>
              </div>
            </>
          ) : (
            <>
              {/* 매물 비교 */}
              <Comparison lands={getSelectedLandData()} />

              {/* 목록으로 돌아가기 버튼 */}
              <div className="flex justify-center mt-8">
                <Button
                  variant="secondary"
                  onClick={() => setShowComparison(false)}
                >
                  목록으로 돌아가기
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
