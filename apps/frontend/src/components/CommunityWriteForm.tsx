/**
 * CommunityWriteForm 컴포넌트
 *
 * 커뮤니티 게시글 작성 폼
 *
 * 주요 기능:
 * - 제목/내용 입력
 * - 지역 게시글일 경우 지역/동/단지명 선택
 * - 기본 검증 및 길이 제한
 */

'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import Button from './Button'

const SEOUL_DONGS: Record<string, string[]> = {
  강남구: ['개포동', '논현동', '대치동', '도곡동', '삼성동', '세곡동', '신사동', '압구정동', '역삼동', '일원동', '자곡동', '청담동'],
  강동구: ['강일동', '고덕동', '길동', '둔촌동', '명일동', '상일동', '성내동', '암사동', '천호동']
}

export interface CommunityWriteFormValues {
  title: string
  content: string
  region?: string
  dong?: string
  complexName?: string
}

interface CommunityWriteFormProps {
  mode: 'free' | 'region'
  initialValues?: CommunityWriteFormValues
  onSubmit: (values: CommunityWriteFormValues) => void
  onCancel?: () => void
  submitLabel?: string
}

const TITLE_LIMIT = 100
const CONTENT_LIMIT = 1000
const COMPLEX_LIMIT = 50

const DEFAULT_VALUES = {
  title: '',
  content: '',
  region: '',
  dong: '',
  complexName: ''
}

export default function CommunityWriteForm({
  mode,
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
      ...initialValues,
      ...(mode === 'free' && { region: '', dong: '', complexName: '' })
    })
    setErrors({})
  }, [initialValues, mode])

  const dongOptions = useMemo(() => {
    return formValues.region ? SEOUL_DONGS[formValues.region] || [] : []
  }, [formValues.region])

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

  const handleRegionChange = (value: string) => {
    setFormValues((prev) => ({
      ...prev,
      region: value,
      dong: ''
    }))
    setErrors((prev) => ({
      ...prev,
      region: undefined,
      dong: undefined
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

    if (mode === 'region') {
      if (!formValues.region) {
        nextErrors.region = '지역을 선택해주세요.'
      }
      if (!formValues.dong) {
        nextErrors.dong = '동을 선택해주세요.'
      }
      if (!formValues.complexName.trim()) {
        nextErrors.complexName = '단지명을 입력해주세요.'
      }
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

    if (mode === 'region') {
      payload.region = formValues.region
      payload.dong = formValues.dong
      payload.complexName = formValues.complexName.trim()
    }

    onSubmit(payload)
  }

  const titleHelper = errors.title || (formValues.title.trim() === '' ? '제목을 입력해주세요.' : undefined)
  const contentHelper = errors.content || (formValues.content.trim() === '' ? '내용을 입력해주세요.' : undefined)
  const regionHelper = errors.region || (mode === 'region' && !formValues.region ? '지역을 선택해주세요.' : undefined)
  const dongHelper = errors.dong || (mode === 'region' && !formValues.dong ? '동을 선택해주세요.' : undefined)
  const complexHelper = errors.complexName || (mode === 'region' && !formValues.complexName.trim() ? '단지명을 입력해주세요.' : undefined)

  const isSubmitDisabled =
    !formValues.title.trim() ||
    !formValues.content.trim() ||
    (mode === 'region' && (!formValues.region || !formValues.dong || !formValues.complexName.trim()))

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      {mode === 'region' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              지역 선택 <span className="text-red-500">*</span>
            </label>
            <select
              value={formValues.region}
              onChange={(e) => handleRegionChange(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            >
              <option value="">지역구를 선택해주세요</option>
              {Object.keys(SEOUL_DONGS).map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </select>
            {regionHelper && <p className="text-xs text-red-500 mt-1">{regionHelper}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              동 선택 <span className="text-red-500">*</span>
            </label>
            <select
              value={formValues.dong}
              onChange={(e) => handleChange('dong', e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              disabled={!formValues.region}
            >
              <option value="">동을 선택해주세요</option>
              {dongOptions.map((dongName) => (
                <option key={dongName} value={dongName}>
                  {dongName}
                </option>
              ))}
            </select>
            {dongHelper && <p className="text-xs text-red-500 mt-1">{dongHelper}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              단지명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formValues.complexName}
              onChange={(e) => handleChange('complexName', e.target.value)}
              placeholder="예: 강남래미안, 잠실주공5단지"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              maxLength={COMPLEX_LIMIT}
            />
            <div className="flex justify-between items-center mt-1">
              <p className="text-xs text-gray-500">
                {formValues.complexName.length}/{COMPLEX_LIMIT}
              </p>
              {complexHelper && <p className="text-xs text-red-500">{complexHelper}</p>}
            </div>
          </div>
        </>
      )}

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
