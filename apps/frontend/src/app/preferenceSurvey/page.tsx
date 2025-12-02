'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { signOut, useSession } from 'next-auth/react'
import axios from 'axios'
import PreferenceRanking from '@/components/PreferenceRanking'
import axiosInstance from '@/lib/axios'
import type { PreferenceSurveyPayload } from '@/types/user'
import useBackendUserGuard from '@/hooks/useBackendUserGuard'

export default function PreferenceSurveyPage() {
  const router = useRouter()
  const { data: session, status, update } = useSession()
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.replace('/login')
    }
  }, [status, router])

  useBackendUserGuard({ enabled: status === 'authenticated' })

  const handleSurveySubmit = async (data: PreferenceSurveyPayload) => {
    setIsSubmitting(true)
    try {
      await axiosInstance.post('/api/users/preference-survey/', data)
      await update({
        ...session,
        user: {
          ...session?.user,
          surveyCompleted: true,
          isNewUser: false,
        },
      })
      alert('선호도 조사가 완료되었습니다. 메인 페이지로 이동합니다.')
      router.push('/main')
    } catch (error) {
      console.error(error)
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        alert('세션이 만료되었거나 계정이 삭제되었습니다. 다시 로그인해주세요.')
        await signOut({ callbackUrl: '/login' })
        return
      }
      alert('설문 정보를 저장하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-500">
        설문 페이지를 준비하고 있습니다...
      </div>
    )
  }

  if (status !== 'authenticated') {
    return null
  }

  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-grow max-w-5xl w-full mx-auto py-12 px-4">
        <PreferenceRanking
          onSubmit={handleSurveySubmit}
          submitLabel="설문 제출"
          isSubmitting={isSubmitting}
        />
      </main>
    </div>
  )
}
