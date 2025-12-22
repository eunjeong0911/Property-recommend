/**
 * CommunityWriteForm 컴포넌트
 *
 * 커뮤니티 게시글 작성 폼
 *
 * 주요 기능:
 * - 제목 입력 필드
 * - 내용 입력 필드 (텍스트 에리어)
 * - 입력값 유효성 검사
 */

'use client'

import { FormEvent, useEffect, useState } from 'react'
import Button from './Button'

export interface CommunityWriteFormValues {
  title: string
  content: string
}

interface CommunityWriteFormProps {
  initialValues?: CommunityWriteFormValues
  onSubmit: (values: CommunityWriteFormValues) => void
  onCancel?: () => void
  submitLabel?: string
}

const TITLE_LIMIT = 100
const CONTENT_LIMIT = 1000

const DEFAULT_VALUES = {
  title: '',
  content: ''
}

export default function CommunityWriteForm({
  initialValues,
  onSubmit,
  onCancel,
  submitLabel = '등록하기'
}: CommunityWriteFormProps) {
  const [formValues, setFormValues] = useState({
    ...DEFAULT_VALUES,
    ...initialValues
  })
  const [errors, setErrors] = useState<Partial<Record<keyof typeof DEFAULT_VALUES, string>>>({})
  const [hasSubmitted, setHasSubmitted] = useState(false)

  useEffect(() => {
    setFormValues({
      ...DEFAULT_VALUES,
      ...initialValues
    })
    setErrors({})
    setHasSubmitted(false)
  }, [initialValues])

  const handleChange = (field: keyof typeof DEFAULT_VALUES, value: string) => {
    setFormValues((prev) => ({
      ...prev,
      [field]: value
    }))
    // 제출 후에만 실시간 유효성 검사
    if (hasSubmitted) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined
      }))
    }
  }

  const validate = () => {
    const nextErrors: Partial<Record<keyof typeof DEFAULT_VALUES, string>> = {}

    if (!formValues.title.trim()) {
      nextErrors.title = '제목을 입력해주세요.'
    }
    if (!formValues.content.trim()) {
      nextErrors.content = '내용을 입력해주세요.'
    }

    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    setHasSubmitted(true)

    if (!validate()) {
      return
    }

    const payload: CommunityWriteFormValues = {
      title: formValues.title.trim(),
      content: formValues.content.trim()
    }

    onSubmit(payload)
  }

  // 제출 시도 후에만 에러 표시
  const titleHelper = hasSubmitted && errors.title
  const contentHelper = hasSubmitted && errors.content

  const isSubmitDisabled = !formValues.title.trim() || !formValues.content.trim()

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1.5">
          제목 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={formValues.title}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="제목을 입력해주세요."
          className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#16375B]/20 focus:border-[#16375B] bg-slate-50 placeholder-slate-400 text-slate-800"
          maxLength={TITLE_LIMIT}
        />
        <div className="flex justify-between items-center mt-1">
          <p className="text-xs text-gray-500">
            {formValues.title.length}/{TITLE_LIMIT}
          </p>
          {titleHelper && <p className="text-xs text-red-500">{titleHelper}</p>}
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1.5">
          내용 <span className="text-red-500">*</span>
        </label>
        <textarea
          value={formValues.content}
          onChange={(e) => handleChange('content', e.target.value)}
          placeholder="이웃과 함께 나누고 싶은 이야기를 자유롭게 작성해주세요."
          rows={8}
          className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#16375B]/20 focus:border-[#16375B] resize-none bg-slate-50 placeholder-slate-400 text-slate-800"
          maxLength={CONTENT_LIMIT}
        />
        <div className="flex justify-between items-center mt-1">
          <p className="text-xs text-gray-500">
            {formValues.content.length}/{CONTENT_LIMIT}
          </p>
          {contentHelper && <p className="text-xs text-red-500">{contentHelper}</p>}
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-white/40">
        {onCancel && (
          <Button variant="secondary" onClick={onCancel} type="button">
            취소
          </Button>
        )}
        <Button variant="primary" type="submit" disabled={isSubmitDisabled}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
