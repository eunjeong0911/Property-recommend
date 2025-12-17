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
    <div className="w-full max-w-4xl mx-auto p-8 rounded-3xl border-2 border-slate-200 bg-white shadow-lg mb-6">
      <div className="flex flex-col items-center mb-6">
        <div className="w-24 h-24 rounded-full bg-white/40 border-2 border-white/60 flex items-center justify-center overflow-hidden mb-4 shadow-md">
          {previewImage ? (
            <img
              src={previewImage}
              alt="프로필 사진"
              className="w-full h-full object-cover"
            />
          ) : (
            <svg
              className="w-16 h-16 text-white/60"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
          )}
        </div>

        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-800 mb-1">
            {displayName}
          </h3>
          {email && (
            <p className="text-sm text-gray-500">{email}</p>
          )}
        </div>
      </div>

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
