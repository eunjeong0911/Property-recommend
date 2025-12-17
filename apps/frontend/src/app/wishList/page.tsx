/**
 * WishListPage 컴포넌트
 *
 * 찜 리스트 페이지
 *
 * - LandImage.tsx (매물 이미지)
 * - Pagination.tsx (페이지네이션)
 * - Button.tsx (비교하기 버튼)
 * - Comparison.tsx (매물 비교)
 */

'use client'

import { useState, useEffect } from 'react'
import SideTab from '@/components/SideTab'
import LandImage from '@/components/LandImage'
import Pagination from '@/components/Pagination'
import Comparison from '@/components/Comparison'
import Button from '@/components/Button'
import { fetchWishlist } from '@/api/wishlistApi'
import { fetchLandById } from '@/api/landApi'
import { Land } from '@/types/land'

export default function WishListPage() {
  const [showComparison, setShowComparison] = useState(false)
  const [selectedLands, setSelectedLands] = useState<number[]>([])
  const [wishlistLands, setWishlistLands] = useState<Land[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 찜 매물 데이터 로드
  useEffect(() => {
    async function loadWishlist() {
      try {
        setLoading(true)
        setError(null)

        // 1. 찜 목록 가져오기
        const wishlist = await fetchWishlist()

        // 2. 각 찜 매물의 상세 정보 가져오기
        const landPromises = wishlist.map(item =>
          fetchLandById(item.listing_id)
        )
        const lands = await Promise.all(landPromises)

        setWishlistLands(lands)
      } catch (err) {
        console.error('Failed to load wishlist:', err)
        setError('찜 매물을 불러오는데 실패했습니다.')
      } finally {
        setLoading(false)
      }
    }

    loadWishlist()
  }, [])

  // 매물 선택/해제 핸들러
  const handleSelectLand = (landId: number) => {
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

  // 가격 포맷팅 함수
  const formatPrice = (land: Land) => {
    if (land.deal_type === '월세') {
      return `월세 ${land.deposit || 0} / ${land.monthly_rent || 0}`
    } else if (land.deal_type === '전세') {
      return `전세 ${land.deposit || 0}`
    }
    return land.price || '가격 정보 없음'
  }

  // 온도 계산 (가격 예측 정보 기반)
  const getTemperature = (land: Land): number => {
    if (land.price_prediction) {
      const label = land.price_prediction.prediction_label_korean
      if (label === '저렴') return 0.3
      if (label === '적정') return 0.6
      if (label === '비쌈') return 0.9
    }
    return 0.5
  }


  // 선택된 매물 데이터 가져오기 (Comparison 컴포넌트용으로 변환)
  const getSelectedLandData = () => {
    return selectedLands
      .map((id) => {
        const land = wishlistLands.find((l) => l.id === id)
        if (!land) return null

        // Land 타입을 LandData 타입으로 변환
        return {
          id: land.id.toString(),
          images: land.images,
          price: formatPrice(land),
          deposit: land.deposit?.toString(),
          monthlyRent: land.monthly_rent?.toString(),
          buildingType: land.building_type,
          area: land.area_exclusive || land.area_supply,
          floor: land.floor,
        }
      })
      .filter(Boolean) as any[]
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex gap-6">
          <SideTab />
          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-6 text-black">찜 매물 목록</h1>
            <div className="bg-white rounded-lg shadow-sm p-12 text-center">
              <p className="text-gray-600">로딩 중...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex gap-6">
          <SideTab />
          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-6 text-black">찜 매물 목록</h1>
            <div className="bg-red-50 border border-red-200 rounded-lg p-12 text-center">
              <p className="text-red-600">{error}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex gap-6">
        {/* 좌측 사이드 탭 */}
        <SideTab />

        {/* 우측 컨텐츠 영역 */}
        <div className="flex-1">
          <h1 className="text-3xl font-bold mb-6 text-black">찜 매물 목록</h1>

          {!showComparison ? (
            <>
              {/* 선택 안내 */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-2xl p-4 mb-6 shadow-sm">
                <p className="text-sm text-blue-800 font-medium">
                  💡 비교할 매물을 선택하세요 (최대 3개) - 현재 <span className="font-bold text-blue-600">{selectedLands.length}</span>개 선택됨
                </p>
              </div>

              {/* 찜한 매물 목록 - Pagination으로 관리 */}
              <Pagination
                items={wishlistLands}
                pageSize={8}
                renderItem={(land) => (
                  <div className="w-1/4 p-3">
                    <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
                      <div className="relative">
                        {/* 체크박스 */}
                        <div className="absolute top-3 left-3 z-10">
                          <input
                            type="checkbox"
                            checked={selectedLands.includes(land.id)}
                            onChange={() => handleSelectLand(land.id)}
                            className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer shadow-sm"
                          />
                        </div>
                        <LandImage
                          key={land.id}
                          id={land.id.toString()}
                          images={land.images}
                          price={formatPrice(land)}
                          isLiked={true}
                        />
                      </div>
                      {/* 주소 정보 */}
                      <div className="px-3 pb-3">
                        <p className="text-sm text-gray-600 truncate flex items-center gap-1" title={land.address}>
                          <span className="text-blue-500">📍</span>
                          {land.address || '주소 정보 없음'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                emptyMessage={
                  <div className="bg-white/50 border-2 border-white/40 backdrop-blur-md rounded-2xl p-12 text-center shadow-lg">
                    <p className="text-slate-500 text-lg font-medium">찜한 매물이 없습니다.</p>
                    <p className="text-slate-400 text-sm mt-2">마음에 드는 매물을 찜해보세요! ❤️</p>
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
