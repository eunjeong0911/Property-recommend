/**
 * RegionFilter 컴포넌트
 *
 * 지역 필터 컴포넌트 - 커스텀 드롭다운 사용
 *
 * 주요 기능:
 * - 자치구 선택 드롭다운
 * - 행정동 선택 드롭다운
 * - 단지 입력
 * - 선택된 지역 정보 관리
 * - 검색 기능
 */

'use client'

import { useEffect, useMemo, useState, useRef } from 'react'
import Button from './Button'

// 서울특별시 행정동 목록 (자치구별) - LandListFilter와 동일한 데이터
const SEOUL_DONGS: Record<string, string[]> = {
  '강남구': ['역삼동', '삼성동', '대치동', '청담동', '논현동', '압구정동', '신사동', '개포동', '세곡동', '일원동', '수서동', '도곡동'],
  '강동구': ['명일동', '고덕동', '상일동', '길동', '둔촌동', '암사동', '성내동', '천호동', '강일동'],
  '강북구': ['미아동', '번동', '수유동', '우이동'],
  '강서구': ['염창동', '등촌동', '화곡동', '가양동', '마곡동', '내발산동', '외발산동', '공항동', '방화동'],
  '관악구': ['봉천동', '신림동', '남현동'],
  '광진구': ['중곡동', '능동', '구의동', '광장동', '자양동', '화양동'],
  '구로구': ['신도림동', '구로동', '가리봉동', '고척동', '개봉동', '오류동', '궁동', '온수동', '천왕동', '항동'],
  '금천구': ['가산동', '독산동', '시흥동'],
  '노원구': ['월계동', '공릉동', '하계동', '상계동', '중계동'],
  '도봉구': ['쌍문동', '방학동', '창동', '도봉동'],
  '동대문구': ['용신동', '제기동', '전농동', '답십리동', '장안동', '청량리동', '회기동', '휘경동', '이문동'],
  '동작구': ['노량진동', '상도동', '흑석동', '사당동', '대방동', '신대방동'],
  '마포구': ['공덕동', '아현동', '도화동', '용강동', '대흥동', '염리동', '신수동', '서강동', '서교동', '합정동', '망원동', '연남동', '성산동', '상암동'],
  '서대문구': ['충현동', '천연동', '신촌동', '연희동', '홍제동', '홍은동', '북아현동', '북가좌동', '남가좌동'],
  '서초구': ['서초동', '잠원동', '반포동', '방배동', '양재동', '내곡동'],
  '성동구': ['왕십리도선동', '왕십리동', '마장동', '사근동', '행당동', '응봉동', '금호동', '옥수동', '성수동', '송정동', '용답동'],
  '성북구': ['성북동', '삼선동', '동선동', '돈암동', '안암동', '보문동', '정릉동', '길음동', '종암동', '월곡동', '장위동', '석관동'],
  '송파구': ['잠실동', '신천동', '풍납동', '송파동', '석촌동', '삼전동', '가락동', '문정동', '장지동', '오금동', '방이동', '거여동', '마천동'],
  '양천구': ['목동', '신월동', '신정동'],
  '영등포구': ['영등포동', '영등포본동', '여의도동', '당산동', '도림동', '문래동', '양평동', '신길동', '대림동'],
  '용산구': ['후암동', '용산2가동', '남영동', '청파동', '원효로동', '효창동', '용문동', '한강로동', '이촌동', '이태원동', '한남동', '서빙고동', '보광동'],
  '은평구': ['수색동', '녹번동', '불광동', '갈현동', '구산동', '대조동', '응암동', '역촌동', '신사동', '증산동'],
  '종로구': ['청운효자동', '사직동', '삼청동', '부암동', '평창동', '무악동', '교남동', '가회동', '종로1·2·3·4가동', '종로5·6가동', '이화동', '혜화동', '창신동', '숭인동'],
  '중구': ['소공동', '회현동', '명동', '필동', '장충동', '광희동', '을지로동', '신당동', '다산동', '약수동', '청구동', '신당5동', '동화동', '황학동', '중림동'],
  '중랑구': ['면목동', '상봉동', '중화동', '묵동', '망우동', '신내동']
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

// 커스텀 드롭다운 컴포넌트
function CustomDropdown({
  value,
  options,
  onChange,
  placeholder,
  disabled = false,
  label
}: {
  value: string
  options: string[]
  onChange: (value: string) => void
  placeholder: string
  disabled?: boolean
  label: string
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  // 외부 클릭 감지
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSearchTerm('')
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // 검색 필터링
  const filteredOptions = options.filter(option =>
    option.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleSelect = (option: string) => {
    onChange(option)
    setIsOpen(false)
    setSearchTerm('')
  }

  return (
    <div ref={dropdownRef} className="relative">
      <label className="block text-sm font-semibold text-slate-700 mb-2">
        {label}
      </label>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`relative w-full px-4 py-3 pr-10 border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#16375B]/20 bg-white text-left font-medium transition-all ${disabled
          ? 'border-slate-200 text-slate-400 cursor-not-allowed bg-slate-50'
          : 'border-slate-200 text-slate-800 hover:border-[#16375B]/50 hover:shadow-md focus:border-[#16375B]'
          }`}
        style={{ fontSize: '15px' }}
      >
        <span className={value ? 'text-slate-800' : 'text-slate-500'}>
          {value || placeholder}
        </span>
        <div className={`absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none transition-transform ${isOpen ? 'rotate-180' : ''}`}>
          <svg className={`w-5 h-5 ${disabled ? 'text-slate-400' : 'text-[#16375B]'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* 드롭다운 메뉴 */}
      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-2 bg-white border-2 border-[#16375B]/20 rounded-xl shadow-2xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          {/* 검색 입력 */}
          {options.length > 5 && (
            <div className="p-3 border-b border-slate-100">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="검색..."
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#16375B]/20 focus:border-[#16375B]"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          )}

          {/* 옵션 리스트 */}
          <div className="max-h-60 overflow-y-auto">
            {/* 전체 옵션 */}
            <button
              type="button"
              onClick={() => handleSelect('')}
              className={`w-full px-4 py-2.5 text-left text-sm transition-colors ${!value
                ? 'bg-[#16375B] text-white font-semibold'
                : 'text-slate-700 hover:bg-slate-50'
                }`}
            >
              전체
            </button>

            {filteredOptions.length > 0 ? (
              filteredOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => handleSelect(option)}
                  className={`w-full px-4 py-2.5 text-left text-sm transition-colors ${value === option
                    ? 'bg-[#16375B] text-white font-semibold'
                    : 'text-slate-700 hover:bg-slate-50'
                    }`}
                >
                  {option}
                </button>
              ))
            ) : (
              <div className="px-4 py-6 text-center text-sm text-slate-400">
                검색 결과가 없습니다
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
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
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 mb-6">
      {showTitle && (
        <h3 className="text-lg font-bold text-slate-900 mb-4">지역 필터</h3>
      )}

      <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 ${showButtons ? 'mb-4' : ''}`}>
        {/* 자치구 선택 */}
        <CustomDropdown
          value={region}
          options={Object.keys(SEOUL_DONGS)}
          onChange={handleRegionChange}
          placeholder="전체"
          label="자치구"
        />

        {/* 행정동 선택 */}
        <CustomDropdown
          value={dong}
          options={dongOptions}
          onChange={handleDongChange}
          placeholder="전체"
          disabled={!region}
          label="행정동"
        />

        {/* 단지명 입력 */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            단지명
          </label>
          <div className="relative group">
            <input
              type="text"
              value={complexName}
              onChange={(e) => handleComplexNameChange(e.target.value)}
              placeholder="단지명 입력"
              className="w-full px-4 py-3 pr-10 border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#16375B]/20 focus:border-[#16375B] bg-white text-slate-800 font-medium placeholder-slate-400 transition-all hover:border-[#16375B]/50 hover:shadow-md"
              style={{ fontSize: '15px' }}
            />
            {complexName && (
              <button
                onClick={() => handleComplexNameChange('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-[#16375B] hover:bg-slate-100 rounded-full transition-all"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {showButtons && (
        <div className="flex justify-end gap-3 pt-2">
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
