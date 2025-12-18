/**
 * CommunityWriteModal 컴포넌트
 *
 * 커뮤니티 게시글 작성/수정 모달 컴포넌트
 *
 * 주요 기능:
 * - 모달 오버레이 및 바디 스크롤 잠금
 * - CommunityWriteForm 포함
 * - 등록/수정 완료 시 상위 콜백 실행
 */

'use client'

import { useEffect, useState } from 'react'
import CommunityWriteForm, { CommunityWriteFormValues } from './CommunityWriteForm'
import RegionFilter, { RegionFilterValues } from './RegionFilter'

interface CommunityWriteModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CommunityWriteFormValues, regionData?: RegionFilterValues) => void
  initialData?: CommunityWriteFormValues
  initialRegionData?: RegionFilterValues
  title?: string
  submitLabel?: string
  showRegionFilter?: boolean
}

export default function CommunityWriteModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  initialRegionData,
  title = '글쓰기',
  submitLabel = '등록하기',
  showRegionFilter = false
}: CommunityWriteModalProps) {
  const [regionData, setRegionData] = useState<RegionFilterValues>(initialRegionData || {})

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      setRegionData(initialRegionData || {})
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, initialRegionData])

  if (!isOpen) return null

  const handleRegionFilterChange = (filter: RegionFilterValues) => {
    setRegionData(filter)
  }

  const handleSubmit = async (values: CommunityWriteFormValues) => {
    if (showRegionFilter) {
      if (!regionData.region || !regionData.dong || !regionData.complexName) {
        alert('지역 및 단지를 모두 선택해주세요.')
        return
      }
      await onSubmit(values, regionData)
    } else {
      await onSubmit(values)
    }
    onClose()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="rounded-3xl bg-white shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="text-xl font-bold text-slate-900">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-all"
            aria-label="모달 닫기"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 내용 */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {showRegionFilter && (
            <div className="mb-6">
              <RegionFilter
                onFilterChange={handleRegionFilterChange}
                initialValues={initialRegionData}
                showButtons={false}
                autoUpdate={true}
                showTitle={false}
              />
            </div>
          )}

          <CommunityWriteForm
            initialValues={initialData}
            submitLabel={submitLabel}
            onSubmit={handleSubmit}
            onCancel={onClose}
          />
        </div>
      </div>
    </div>
  )
}
