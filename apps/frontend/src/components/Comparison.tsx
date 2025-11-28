/**
 * Comparison 컴포넌트
 *
 * 매물 비교 컴포넌트
 *
 * 주요 기능:
 * - 두 개 이상의 매물을 나란히 비교 표시 (최대 3개)
 * - 매물 이미지 표시
 * - 찜하기 버튼
 * - 매물 정보 표시 (월세, 보증금, 건축물 용도, 공급면적, 해당층/전체층, 방/욕실 수)
 * - AI 비교 분석 영역
 *
 * 사용 컴포넌트:
 * - LandImage: 매물 사진 표시
 */

'use client'

import { useState } from 'react'
import LandImage from './LandImage'

interface LandData {
  id: string
  images?: string[]
  price: string
  deposit?: string
  monthlyRent?: string
  buildingType?: string
  area?: string
  floor?: string
  totalFloor?: string
  rooms?: number
  bathrooms?: number
  temperature?: number
}

interface ComparisonProps {
  lands?: LandData[]
  land1?: LandData
  land2?: LandData
}

export default function Comparison({ lands, land1, land2 }: ComparisonProps) {
  const [likedStates, setLikedStates] = useState<Record<string, boolean>>({})

  // lands prop이 있으면 사용, 없으면 land1, land2 사용 (하위 호환성)
  const compareData = lands && lands.length >= 2 ? lands : (land1 && land2 ? [land1, land2] : [])

  // 매물이 2개 미만일 때
  if (compareData.length < 2) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <h2 className="text-3xl font-bold text-center mb-8">매물 비교</h2>
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <p className="text-gray-600 text-lg">
            비교할 매물을 선택해주세요. 최소 2개의 매물을 선택해야 비교할 수 있습니다.
          </p>
        </div>
      </div>
    )
  }

  const toggleLike = (landId: string) => {
    setLikedStates(prev => ({ ...prev, [landId]: !prev[landId] }))
  }

  // 그리드 컬럼 개수 결정 (2개 또는 3개)
  const gridCols = compareData.length === 2 ? 'grid-cols-2' : 'grid-cols-3'

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h2 className="text-3xl font-bold text-center mb-8">매물 비교</h2>

      {/* 매물 비교 */}
      <div className={`grid ${gridCols} gap-8 mb-8`}>
        {compareData.map((land) => (
          <div key={land.id} className="bg-white rounded-lg shadow-md p-6">
            {/* 매물 이미지 */}
            <LandImage
              id={land.id}
              images={land.images}
              price={land.price}
              temperature={land.temperature}
              onLike={() => toggleLike(land.id)}
              isLiked={likedStates[land.id] || false}
            />

            {/* 매물 정보 */}
            <div className="mt-6 space-y-3">
              {land.deposit && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">보증금</span>
                  <span className="font-semibold">{land.deposit}</span>
                </div>
              )}
              {land.monthlyRent && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">월세</span>
                  <span className="font-semibold">{land.monthlyRent}</span>
                </div>
              )}
              {land.buildingType && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">건축물 용도</span>
                  <span className="font-semibold">{land.buildingType}</span>
                </div>
              )}
              {land.area && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">공급면적</span>
                  <span className="font-semibold">{land.area}</span>
                </div>
              )}
              {land.floor && land.totalFloor && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">층수</span>
                  <span className="font-semibold">{land.floor}층 / 전체 {land.totalFloor}층</span>
                </div>
              )}
              {land.rooms !== undefined && land.bathrooms !== undefined && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">방 / 욕실</span>
                  <span className="font-semibold">{land.rooms}개 / {land.bathrooms}개</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* AI 비교 분석 영역 */}
      <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <span className="text-blue-600">🤖</span>
          AI 비교 분석
        </h3>
        <div className="space-y-3 text-gray-700">
          <p>
            <strong>가격 비교:</strong> 선택한 {compareData.length}개 매물의 가격대를 분석 중입니다.
          </p>
          <p>
            <strong>위치 및 편의성:</strong> 각 매물의 위치와 주변 편의시설을 비교합니다.
          </p>
          <p>
            <strong>추천:</strong> 사용자의 선호도에 맞는 최적의 매물을 추천해드립니다.
          </p>
        </div>
      </div>
    </div>
  )
}
