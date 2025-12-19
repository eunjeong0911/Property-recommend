/**
 * Comparison 컴포넌트
 *
 * 매물 비교 컴포넌트
 *
 * 주요 기능:
 * - 두 개 이상의 매물을 나란히 비교 표시 (최대 3개)
 * - LLM 기반 비교 분석 (ML 예측 포함)
 * - 마크다운 렌더링
 *
 * 사용 컴포넌트:
 * - LandImage: 매물 사진 표시
 * - ReactMarkdown: 마크다운 렌더링
 */

'use client'

import { useState, useEffect } from 'react'
import LandImage from './LandImage'
import { compareProperties, type PropertyData } from '@/api/compareApi'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [comparisonResult, setComparisonResult] = useState<{
    summary: string
    properties: PropertyData[]
  } | null>(null)

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

  // LLM 비교 분석 호출
  useEffect(() => {
    async function fetchComparison() {
      try {
        setLoading(true)
        setError(null)

        // land_id 추출
        const landIds = compareData.map(land => parseInt(land.id))

        // API 호출
        const result = await compareProperties(landIds)
        setComparisonResult(result)
      } catch (err) {
        console.error('비교 분석 실패:', err)
        setError(err instanceof Error ? err.message : '비교 분석에 실패했습니다.')
      } finally {
        setLoading(false)
      }
    }

    fetchComparison()
  }, [compareData])

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
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">위치</span>
                  <span className="font-semibold text-right max-w-[60%] truncate" title={land.address}>{land.address}</span>
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
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">입주가능일</span>
                  <span className="font-semibold">{land.moveInDate}</span>
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
              {/* 실거래가 판단 (구 AI 가격 예측) */}
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

      {/* AI 비교 분석 영역 */}
      <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 shadow-lg">
        <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            AI 비교 분석
          </span>
        </h3>

        {loading && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="w-16 h-16 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-gray-600 text-lg font-medium">AI가 매물을 분석하고 있습니다...</p>
            <p className="text-gray-500 text-sm mt-2">잠시만 기다려주세요 (약 5-10초 소요)</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6">
            <p className="text-red-600 font-medium">⚠️ {error}</p>
            <p className="text-red-500 text-sm mt-2">다시 시도해주세요.</p>
          </div>
        )}

        {!loading && !error && comparisonResult && (
          <div className="prose prose-sm max-w-none leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // 테이블 스타일링 - 컴팩트
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto my-4">
                    <table className="min-w-full border-collapse border border-gray-300 text-sm" {...props} />
                  </div>
                ),
                thead: ({ node, ...props }) => (
                  <thead className="bg-blue-100" {...props} />
                ),
                th: ({ node, ...props }) => (
                  <th className="border border-gray-300 px-3 py-2 text-left font-bold text-gray-700 whitespace-nowrap" {...props} />
                ),
                td: ({ node, ...props }) => (
                  <td className="border border-gray-300 px-3 py-2 whitespace-nowrap" {...props} />
                ),
                // 헤딩 스타일링 - 컴팩트
                h2: ({ node, ...props }) => (
                  <h2 className="text-xl font-bold mt-5 mb-2 text-gray-800 border-b border-blue-300 pb-1" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-lg font-bold mt-4 mb-2 text-gray-700" {...props} />
                ),
                // 문단 - 컴팩트
                p: ({ node, ...props }) => (
                  <p className="my-1 text-gray-700 leading-snug" {...props} />
                ),
                // 리스트 스타일링 - 컴팩트
                ul: ({ node, ...props }) => (
                  <ul className="list-disc list-inside space-y-1 my-2 text-sm" {...props} />
                ),
                li: ({ node, ...props }) => (
                  <li className="text-gray-700" {...props} />
                ),
                // 강조 텍스트
                strong: ({ node, ...props }) => (
                  <strong className="font-bold text-blue-700" {...props} />
                ),
                // 수평선 - 컴팩트
                hr: ({ node, ...props }) => (
                  <hr className="my-4 border-t border-gray-300" {...props} />
                ),
              }}
            >
              {comparisonResult.summary}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
