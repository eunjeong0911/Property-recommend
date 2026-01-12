'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { signOut, useSession } from 'next-auth/react'
import SideTab from '@/components/SideTab'
import Profile from '@/components/Profile'
import PreferenceRanking from '@/components/PreferenceRanking'
import Button from '@/components/Button'
import LoadingSpinner from '@/components/LoadingSpinner'
import axiosInstance from '@/lib/axios'
import type { PreferenceSummary, PreferenceSurveyPayload, UserProfile } from '@/types/user'

export default function MyPage() {
  const router = useRouter()
  const { data: session, status } = useSession()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [preference, setPreference] = useState<PreferenceSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSavingPreference, setIsSavingPreference] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [isDeletingAccount, setIsDeletingAccount] = useState(false)
  const [isUpdatingProfileImage, setIsUpdatingProfileImage] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.replace('/login')
    }
  }, [status, router])

  useEffect(() => {
    const fetchInitialData = async () => {
      if (status !== 'authenticated') {
        return
      }

      setIsLoading(true)
      setError(null)
      try {
        const [userResponse, preferenceResponse] = await Promise.all([
          axiosInstance.get('/api/users/me/'),
          axiosInstance.get('/api/users/preference-survey/'),
        ])

        const userData: UserProfile = userResponse.data
        const preferenceData = preferenceResponse.data || {}

        setProfile(userData)
        const resolvedJob = preferenceData.job || userData.job_type || null
        setPreference({
          job: resolvedJob,
          priorities: preferenceData.priorities ?? {},
          completedAt: preferenceData.survey?.created_at ?? null,
        })
      } catch (fetchError: any) {
        console.error(fetchError)
        setError('마이페이지 정보를 불러오지 못했습니다.')
        if (fetchError?.response?.status === 401) {
          await signOut({ callbackUrl: '/login' })
        }
      } finally {
        setIsLoading(false)
      }
    }

    fetchInitialData()
  }, [status])

  const handlePreferenceSubmit = useCallback(async (data: PreferenceSurveyPayload) => {
    setIsSavingPreference(true)
    try {
      const response = await axiosInstance.post('/api/users/preference-survey/', data)
      setPreference({
        job: response.data.user?.job_type ?? data.job,
        priorities: response.data.survey?.priorities ?? data.priorities,
        completedAt: response.data.survey?.created_at ?? null,
      })
      alert('선호도가 저장되었습니다.')
    } catch (submitError) {
      console.error(submitError)
      alert('선호도 저장에 실패했습니다. 잠시 후 다시 시도해주세요.')
    } finally {
      setIsSavingPreference(false)
    }
  }, [])

  const handleLogout = useCallback(async () => {
    if (!confirm('로그아웃 하시겠습니까?')) {
      return
    }
    setIsLoggingOut(true)
    await signOut({ callbackUrl: '/' })
  }, [])

  const handleDeleteAccount = useCallback(async () => {
    if (!confirm('정말로 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
      return
    }
    setIsDeletingAccount(true)
    try {
      await axiosInstance.delete('/api/users/me/')
      alert('계정이 삭제되었습니다.')
      await signOut({ callbackUrl: '/' })
    } catch (deleteError) {
      console.error(deleteError)
      alert('계정 삭제에 실패했습니다. 잠시 후 다시 시도해주세요.')
      setIsDeletingAccount(false)
    }
  }, [])

  const handleProfileImageChange = useCallback(async (dataUri: string | null) => {
    setIsUpdatingProfileImage(true)
    try {
      const payload = { profile_image_upload: dataUri ?? '' }
      const response = await axiosInstance.patch('/api/users/me/update/', payload)
      setProfile(response.data)
    } catch (error) {
      console.error(error)
      alert('프로필 이미지를 저장하는 데 실패했습니다. 잠시 후 다시 시도해주세요.')
      throw error
    } finally {
      setIsUpdatingProfileImage(false)
    }
  }, [])

  const profileName = useMemo(() => {
    if (profile?.first_name || profile?.last_name) {
      const nameParts = [profile?.first_name, profile?.last_name].filter(
        (value): value is string => Boolean(value)
      )
      const fullName = nameParts.join(' ').trim()
      if (fullName) {
        return fullName
      }
    }
    return session?.user?.name || profile?.username || profile?.email || undefined
  }, [profile, session])

  const profileEmail = profile?.email || session?.user?.email || undefined
  const profileImage = profile?.profile_image_data || profile?.profile_image || session?.user?.image || null

  if (status === 'loading' || isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <SideTab />
        <LoadingSpinner message="마이페이지 정보를 불러오고 있습니다..." />
      </div>
    )
  }

  if (status !== 'authenticated') {
    return null
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* 가로 탭 */}
      <SideTab />

      {/* 메인 컨텐츠 */}
      <div>
        {error && (
          <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        <Profile
          name={profileName}
          email={profileEmail}
          image={profileImage}
          onLogout={handleLogout}
          isLoggingOut={isLoggingOut}
          onChangeProfileImage={handleProfileImageChange}
          isUpdatingProfileImage={isUpdatingProfileImage}
        />
        <PreferenceRanking
          onSubmit={handlePreferenceSubmit}
          initialJob={preference?.job || profile?.job_type || null}
          initialPriorities={preference?.priorities}
          submitLabel="선호도 저장"
          isSubmitting={isSavingPreference}
        />
        <div className="w-full max-w-4xl mx-auto mt-6 flex justify-end px-2">
          <button
            onClick={handleDeleteAccount}
            disabled={isDeletingAccount}
            className="text-sm text-slate-400 hover:text-red-500 hover:underline transition-colors duration-200 flex items-center gap-1"
          >
            {isDeletingAccount ? (
              '계정 삭제 중...'
            ) : (
              <>
                <span>계정 탈퇴</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
