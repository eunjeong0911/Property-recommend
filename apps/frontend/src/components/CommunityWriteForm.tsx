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

  useEffect(() => {
    setFormValues({
      ...DEFAULT_VALUES,
      ...initialValues
    })
    setErrors({})
  }, [initialValues])

  const handleChange = (field: keyof typeof DEFAULT_VALUES, value: string) => {
    setFormValues((prev) => ({
      ...prev,
      [field]: value
    }))
    setErrors((prev) => ({
      ...prev,
      [field]: undefined
    }))
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
    if (!validate()) {
      return
    }

    const payload: CommunityWriteFormValues = {
      title: formValues.title.trim(),
      content: formValues.content.trim()
    }

    onSubmit(payload)
  }

  const titleHelper = errors.title || (formValues.title.trim() === '' ? '제목을 입력해주세요.' : undefined)
  const contentHelper = errors.content || (formValues.content.trim() === '' ? '내용을 입력해주세요.' : undefined)

  const isSubmitDisabled = !formValues.title.trim() || !formValues.content.trim()

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          제목 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={formValues.title}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="제목을 입력해주세요."
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
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
        <label className="block text-sm font-medium text-gray-700 mb-2">
          내용 <span className="text-red-500">*</span>
        </label>
        <textarea
          value={formValues.content}
          onChange={(e) => handleChange('content', e.target.value)}
          placeholder="이웃과 함께 나누고 싶은 이야기를 자유롭게 작성해주세요."
          rows={12}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
          maxLength={CONTENT_LIMIT}
        />
        <div className="flex justify-between items-center mt-1">
          <p className="text-xs text-gray-500">
            {formValues.content.length}/{CONTENT_LIMIT}
          </p>
          {contentHelper && <p className="text-xs text-red-500">{contentHelper}</p>}
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
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
