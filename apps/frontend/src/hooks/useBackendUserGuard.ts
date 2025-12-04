'use client'

import { useEffect, useState } from 'react'
import { signOut, useSession } from 'next-auth/react'
import axios from 'axios'
import axiosInstance from '@/lib/axios'

interface Options {
  enabled?: boolean
  redirectPath?: string
}

/**
 * Ensures that the authenticated NextAuth user also exists in the backend DB.
 * If the backend responds with 401/404 (deleted user / invalid token) we sign out
 * so the UI falls back to the login button immediately.
 */
export default function useBackendUserGuard({ enabled = true, redirectPath = '/login' }: Options = {}) {
  const { status } = useSession()
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    if (!enabled) return
    if (status !== 'authenticated') return

    let active = true

    const verifyUser = async () => {
      setChecking(true)
      try {
        await axiosInstance.get('/api/users/me/')
      } catch (error) {
        if (!active) return
        if (
          axios.isAxiosError(error) &&
          (error.response?.status === 401 || error.response?.status === 404)
        ) {
          alert('세션이 만료되었거나 계정이 없습니다. 다시 로그인해주세요.')
          await signOut({ callbackUrl: redirectPath })
        } else {
          console.error('Failed to verify backend user:', error)
        }
      } finally {
        if (active) {
          setChecking(false)
        }
      }
    }

    verifyUser()

    return () => {
      active = false
    }
  }, [enabled, redirectPath, status])

  return { checking }
}
