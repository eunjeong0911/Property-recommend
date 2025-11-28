/**
 * RootPage
 *
 * 기본 진입 시 메인 페이지로 리다이렉트
 */

import { redirect } from 'next/navigation'

export default function RootPage() {
  redirect('/main')
}
