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

import { useEffect } from 'react'
import CommunityWriteForm, { CommunityWriteFormValues } from './CommunityWriteForm'

interface CommunityWriteModalProps {
  isOpen: boolean
  onClose: () => void
  activeTab: 'free' | 'region'
  onSubmit: (data: CommunityWriteFormValues, mode: 'free' | 'region') => void
  initialData?: CommunityWriteFormValues
  isEditing?: boolean
}

export default function CommunityWriteModal({
  isOpen,
  onClose,
  activeTab,
  onSubmit,
  initialData,
  isEditing = false
}: CommunityWriteModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isOpen) return null

  const formMode: 'free' | 'region' = initialData?.region ? 'region' : activeTab
  const modalTitle = isEditing
    ? '게시글 수정'
    : formMode === 'free'
      ? '자유게시판 글쓰기'
      : '지역 커뮤니티 글쓰기'

  const handleSubmit = (values: CommunityWriteFormValues) => {
    onSubmit(values, formMode)
    onClose()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">{modalTitle}</h2>
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

        <div className="flex-1 overflow-y-auto p-6">
          <CommunityWriteForm
            mode={formMode}
            initialValues={initialData}
            submitLabel={isEditing ? '수정하기' : '등록하기'}
            onSubmit={handleSubmit}
            onCancel={onClose}
          />
        </div>
      </div>
    </div>
  )
}
