'use client'

import { useEffect, useRef, useState } from 'react'
import Button from './Button'

interface ProfileProps {
  name?: string
  email?: string
  image?: string | null
  onLogout?: () => void
  isLoggingOut?: boolean
  onChangeProfileImage?: (dataUrl: string | null) => Promise<unknown> | void
  isUpdatingProfileImage?: boolean
}

export default function Profile({
  name,
  email,
  image,
  onLogout,
  isLoggingOut = false,
  onChangeProfileImage,
  isUpdatingProfileImage,
}: ProfileProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [previewImage, setPreviewImage] = useState<string | null>(image ?? null)
  const [localUploading, setLocalUploading] = useState(false)
  const isUploading = isUpdatingProfileImage ?? localUploading

  useEffect(() => {
    setPreviewImage(image ?? null)
  }, [image])

  const handleProfileImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onloadend = () => {
      const dataUrl = reader.result as string
      setPreviewImage(dataUrl)

      if (onChangeProfileImage) {
        setLocalUploading(true)
        Promise.resolve(onChangeProfileImage(dataUrl))
          .catch((error) => {
            console.error('프로필 이미지 업로드 실패:', error)
            alert('프로필 이미지를 저장하는 데 실패했습니다.')
            setPreviewImage(image ?? null)
          })
          .finally(() => {
            setLocalUploading(false)
          })
      }
    }
    reader.readAsDataURL(file)
  }

  const handleLogout = () => {
    if (!onLogout) return
    onLogout()
  }

  const displayName = name || email || '사용자'

  return (
    <div className="w-full max-w-4xl mx-auto p-8 rounded-2xl border border-slate-200 bg-white shadow-sm mb-6">
      <div className="flex flex-col items-center mb-6">
        {/* 프로필 이미지 */}
        <div className="relative w-28 h-28 rounded-full bg-gradient-to-br from-[#16375B] to-[#2a4a6f] flex items-center justify-center overflow-hidden mb-5 shadow-lg ring-4 ring-white">
          {previewImage ? (
            <img
              src={previewImage}
              alt="프로필 사진"
              className="w-full h-full object-cover"
            />
          ) : (
            <svg
              className="w-14 h-14 text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
          )}
          {isUploading && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
              <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
            </div>
          )}
        </div>

        {/* 사용자 정보 */}
        <div className="text-center">
          <h3 className="text-2xl font-bold text-slate-900 mb-2">
            {displayName}
          </h3>
          {email && (
            <p className="text-sm text-slate-500 bg-slate-50 px-4 py-1.5 rounded-full inline-block">
              {email}
            </p>
          )}
        </div>
      </div>

      {/* 버튼 그룹 */}
      <div className="flex justify-center gap-3">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleProfileImageChange}
          className="hidden"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
        >
          {isUploading ? '업로드 중...' : '프로필 사진 변경'}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={isLoggingOut}
          onClick={handleLogout}
        >
          {isLoggingOut ? '로그아웃 중...' : '로그아웃'}
        </Button>
      </div>
    </div>
  )
}
