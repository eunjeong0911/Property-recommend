/**
 * RegionFilter 컴포넌트
 *
 * 지역 필터 컴포넌트
 *
 * 주요 기능:
 * - 자치구 선택 드롭다운
 * - 행정동 선택 드롭다운
 * - 단지 입력
 * - 선택된 지역 정보 관리
 */

'use client'

import { useEffect, useMemo, useState } from 'react'
import Button from './Button'

const SEOUL_DONGS: Record<string, string[]> = {
  강남구: ['개포동', '논현동', '대치동', '도곡동', '삼성동', '세곡동', '신사동', '압구정동', '역삼동', '일원동', '자곡동', '청담동'],
  강동구: ['강일동', '고덕동', '길동', '둔촌동', '명일동', '상일동', '성내동', '암사동', '천호동']
}

export interface RegionFilterValues {
  region?: string
  dong?: string
  complexName?: string
}

interface RegionFilterProps {
  onFilterChange: (filter: RegionFilterValues) => void
  initialValues?: RegionFilterValues
  showButtons?: boolean
  autoUpdate?: boolean
  showTitle?: boolean
}

export default function RegionFilter({
  onFilterChange,
  initialValues,
  showButtons = true,
  autoUpdate = false,
  showTitle = true
}: RegionFilterProps) {
  const [region, setRegion] = useState<string>(initialValues?.region || '')
  const [dong, setDong] = useState<string>(initialValues?.dong || '')
  const [complexName, setComplexName] = useState<string>(initialValues?.complexName || '')

  useEffect(() => {
    if (initialValues) {
      setRegion(initialValues.region || '')
      setDong(initialValues.dong || '')
      setComplexName(initialValues.complexName || '')
    }
  }, [initialValues])

  const dongOptions = useMemo(() => {
    return region ? SEOUL_DONGS[region] || [] : []
  }, [region])

  const updateFilter = (newRegion: string, newDong: string, newComplexName: string) => {
    if (autoUpdate) {
      const filter: RegionFilterValues = {}
      if (newRegion) filter.region = newRegion
      if (newDong) filter.dong = newDong
      if (newComplexName.trim()) filter.complexName = newComplexName.trim()
      onFilterChange(filter)
    }
  }

  const handleRegionChange = (value: string) => {
    setRegion(value)
    setDong('')
    setComplexName('')
    updateFilter(value, '', '')
  }

  const handleDongChange = (value: string) => {
    setDong(value)
    setComplexName('')
    updateFilter(region, value, '')
  }

  const handleComplexNameChange = (value: string) => {
    setComplexName(value)
    updateFilter(region, dong, value)
  }

  const handleApplyFilter = () => {
    const filter: RegionFilterValues = {}
    if (region) filter.region = region
    if (dong) filter.dong = dong
    if (complexName.trim()) filter.complexName = complexName.trim()
    onFilterChange(filter)
  }

  const handleResetFilter = () => {
    setRegion('')
    setDong('')
    setComplexName('')
    onFilterChange({})
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
      {showTitle && <h3 className="text-lg font-semibold text-gray-900 mb-4">지역 필터</h3>}

      <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 ${showButtons ? 'mb-4' : ''}`}>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            자치구
          </label>
          <select
            value={region}
            onChange={(e) => handleRegionChange(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          >
            <option value="">전체</option>
            {Object.keys(SEOUL_DONGS).map((regionName) => (
              <option key={regionName} value={regionName}>
                {regionName}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            행정동
          </label>
          <select
            value={dong}
            onChange={(e) => handleDongChange(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            disabled={!region}
          >
            <option value="">전체</option>
            {dongOptions.map((dongName) => (
              <option key={dongName} value={dongName}>
                {dongName}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            단지명
          </label>
          <input
            type="text"
            value={complexName}
            onChange={(e) => handleComplexNameChange(e.target.value)}
            placeholder="단지명 입력"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          />
        </div>
      </div>

      {showButtons && (
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={handleResetFilter}>
            초기화
          </Button>
          <Button variant="primary" onClick={handleApplyFilter}>
            적용
          </Button>
        </div>
      )}
    </div>
  )
}
