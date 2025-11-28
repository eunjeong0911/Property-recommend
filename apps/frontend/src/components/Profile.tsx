/**
 * Profile 컴포넌트
 *
 * 사용자 프로필 정보를 표시하는 컴포넌트
 *
 * 주요 기능:
 * - 프로필 이미지 표시
 * - 사용자 이름 표시
 * - 프로필 사진 변경
 * - 로그아웃
 * - 계정 삭제
 */

'use client'

import { useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useStore } from '@/store/useStore'
import Button from './Button'

export default function Profile() {
  const { user, setUser } = useStore()
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 프로필 사진 변경 핸들러
  const handleProfileImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        // 테스트용: 이미지를 base64로 변환해서 저장
        setUser({ ...user, profileImage: reader.result as string })
      }
      reader.readAsDataURL(file)
    }
  }

  // 로그아웃 핸들러
  const handleLogout = () => {
    if (confirm('로그아웃 하시겠습니까?')) {
      setUser(null)
      router.push('/')
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      {/* 프로필 정보 */}
      <div className="flex flex-col items-center mb-6">
        {/* 프로필 이미지 */}
        <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden mb-4">
          {user?.profileImage ? (
            <img
              src={user.profileImage}
              alt="프로필 사진"
              className="w-full h-full object-cover"
            />
          ) : (
            <svg
              className="w-16 h-16 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
          )}
        </div>

        {/* 사용자 이름 */}
        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-800 mb-1">
            {user?.name || user?.email || '사용자'}
          </h3>
          {user?.email && user?.name && (
            <p className="text-sm text-gray-500">{user.email}</p>
          )}
        </div>
      </div>

      {/* 버튼 그룹 */}
      <div className="flex justify-center gap-3">
        {/* 프로필 사진 변경 버튼 */}
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
        >
          프로필 사진 변경
        </Button>

        {/* 로그아웃 버튼 */}
        <Button
          variant="secondary"
          size="sm"
          onClick={handleLogout}
        >
          로그아웃
        </Button>
      </div>
    </div>
  )
}
