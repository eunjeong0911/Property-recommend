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
    <div className="bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md rounded-2xl border-2 border-white/40 shadow-lg p-4 mb-6">
      {showTitle && <h3 className="text-base font-semibold text-slate-800 mb-3">지역 필터</h3>}

      <div className={`grid grid-cols-1 md:grid-cols-3 gap-3 ${showButtons ? 'mb-3' : ''}`}>
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1.5">
            자치구
          </label>
          <select
            value={region}
            onChange={(e) => handleRegionChange(e.target.value)}
            className="w-full px-3 py-2 border border-white/40 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/60 backdrop-blur-sm text-slate-700"
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
          <label className="block text-xs font-medium text-slate-700 mb-1.5">
            행정동
          </label>
          <select
            value={dong}
            onChange={(e) => handleDongChange(e.target.value)}
            className="w-full px-3 py-2 border border-white/40 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/60 backdrop-blur-sm text-slate-700 disabled:bg-white/30 disabled:text-slate-400"
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
          <label className="block text-xs font-medium text-slate-700 mb-1.5">
            단지명
          </label>
          <input
            type="text"
            value={complexName}
            onChange={(e) => handleComplexNameChange(e.target.value)}
            placeholder="단지명 입력"
            className="w-full px-3 py-2 border border-white/40 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/60 backdrop-blur-sm text-slate-700 placeholder-slate-400"
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
