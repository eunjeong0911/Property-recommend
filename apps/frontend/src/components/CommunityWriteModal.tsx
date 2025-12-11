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
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={onClose}
    >
      <div
        className="rounded-3xl border-2 border-white/40 bg-gradient-to-b from-sky-100/95 to-blue-200/95 backdrop-blur-xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="모달 닫기"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {showRegionFilter && (
            <div className="mb-4">
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
