/**
 * Comparison 컴포넌트
 *
 * 매물 비교 컴포넌트
 *
 * 주요 기능:
 * - 두 개 이상의 매물을 나란히 비교 표시 (최대 3개)
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
  // 추가 필드
  direction?: string
  parking?: string
  heating?: string
  elevator?: string
  moveInDate?: string
  address?: string
  // ML 예측
  pricePredictionLabel?: string
  pricePredictionProb?: number
  // 중개사 신뢰도
  brokerTrustScore?: string
  brokerTrustGrade?: string
}

interface ComparisonProps {
  lands?: LandData[]
  land1?: LandData
  land2?: LandData
}

export default function Comparison({ lands, land1, land2 }: ComparisonProps) {
  // lands prop이 있으면 사용, 없으면 land1, land2 사용 (하위 호환성)
  const compareData = lands && lands.length >= 2 ? lands : (land1 && land2 ? [land1, land2] : [])

  // 찜 목록에서 온 매물이므로 기본값은 모두 true (빨간 하트)
  const [likedStates, setLikedStates] = useState<Record<string, boolean>>(() => {
    const initialStates: Record<string, boolean> = {}
    compareData.forEach(land => {
      initialStates[land.id] = true
    })
    return initialStates
  })

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
        {compareData.map((land, index) => (
          <div key={land.id} className="bg-white rounded-lg shadow-md p-6">
            {/* 매물 번호 라벨 */}
            <div className="mb-3">
              <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-bold">
                매물{index + 1}
              </span>
            </div>

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
              {/* 위치 */}
              {land.address && (
                <div className="border-b pb-2">
                  <span className="text-gray-600 block mb-1">위치</span>
                  <span className="font-semibold text-sm break-words">{land.address}</span>
                </div>
              )}
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
              {land.floor && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">층수</span>
                  <span className="font-semibold">{land.floor}</span>
                </div>
              )}
              {land.rooms && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">방</span>
                  <span className="font-semibold">{land.rooms}</span>
                </div>
              )}
              {land.direction && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">방향</span>
                  <span className="font-semibold">{land.direction}</span>
                </div>
              )}
              {land.parking && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">주차</span>
                  <span className="font-semibold">{land.parking}</span>
                </div>
              )}
              {land.heating && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">난방방식</span>
                  <span className="font-semibold">{land.heating}</span>
                </div>
              )}
              {land.elevator && (
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">엘리베이터</span>
                  <span className="font-semibold">{land.elevator}</span>
                </div>
              )}
              {land.moveInDate && (
                <div className="border-b pb-2">
                  <span className="text-gray-600 block mb-1">입주가능일</span>
                  <span className="font-semibold text-sm">{land.moveInDate}</span>
                </div>
              )}
              {/* 중개사 온도 (신뢰도 위) */}
              {land.temperature !== undefined && (
                <div className="flex justify-between border-b pb-2 bg-orange-50 p-2 rounded">
                  <span className="text-orange-700 font-medium">🌡️ 중개사 온도</span>
                  <span className={`font-bold ${land.temperature >= 70 ? 'text-red-500' :
                    land.temperature >= 50 ? 'text-orange-500' :
                      land.temperature >= 30 ? 'text-yellow-600' :
                        'text-blue-500'
                    }`}>
                    {land.temperature}°C
                  </span>
                </div>
              )}
              {/* 중개사 신뢰도 (온도 아래) */}
              {land.brokerTrustScore && (
                <div className="flex justify-between border-b pb-2 bg-purple-50 p-2 rounded">
                  <span className="text-purple-700 font-medium">🏢 중개사 신뢰도</span>
                  <span className={`font-bold ${land.brokerTrustScore === 'A' ? 'text-green-600' :
                    land.brokerTrustScore === 'B' ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                    {land.brokerTrustScore}등급 {land.brokerTrustGrade ? `(${land.brokerTrustGrade})` : ''}
                  </span>
                </div>
              )}
              {/* 실거래가 판단 */}
              {land.pricePredictionLabel && (
                <div
                  className="flex justify-between border-b pb-2 bg-blue-50 p-2 rounded cursor-help"
                  title="해당 행정동의 건물용도별 평당가 대비 ML 모델이 분석한 결과입니다."
                >
                  <span className="text-blue-700 font-medium">📊 실거래가 판단</span>
                  <span className={`font-bold ${land.pricePredictionLabel === '저렴' ? 'text-green-600' :
                    land.pricePredictionLabel === '적정' ? 'text-blue-600' :
                      'text-red-600'
                    }`}>
                    {land.pricePredictionLabel}
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
