/**
 * Pagination 컴포넌트
 *
 * 페이지네이션을 표시하는 컴포넌트
 *
 * 주요 기능:
 * - 페이지 번호 표시
 * - 이전/다음 페이지 버튼
 * - 현재 페이지 하이라이트
 * - 페이지 클릭 시 페이지 이동
 */

'use client'

import { ReactNode, useEffect, useMemo, useState } from 'react'
import { useParticleEffect } from '../hooks/useParticleEffect'

interface PaginationProps<T = unknown> {
  items: T[]
  renderItem: (item: T, index: number) => ReactNode
  pageSize?: number
  emptyMessage?: ReactNode
}

const DEFAULT_EMPTY = (
  <div className="bg-white/50 border-2 border-white/40 backdrop-blur-md rounded-2xl p-8 text-center text-slate-500 shadow-lg">
    아직 게시글이 없습니다. 첫 번째 글의 주인공이 되어주세요!
  </div>
)

export default function Pagination<T>({
  items,
  renderItem,
  pageSize = 5,
  emptyMessage = DEFAULT_EMPTY
}: PaginationProps<T>) {
  const [currentPage, setCurrentPage] = useState(1)
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize))
  const { triggerEffect } = useParticleEffect()

  useEffect(() => {
    setCurrentPage((prev) => Math.min(prev, totalPages))
  }, [totalPages])

  const currentItems = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return {
      data: items.slice(startIndex, startIndex + pageSize),
      startIndex
    }
  }, [items, currentPage, pageSize])

  const handleChange = (page: number, event?: React.MouseEvent<HTMLButtonElement>) => {
    if (event) triggerEffect(event.currentTarget)
    if (page < 1 || page > totalPages || page === currentPage) return
    setCurrentPage(page)
  }

  if (items.length === 0) {
    return <div className="space-y-4">{emptyMessage}</div>
  }

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        {currentItems.data.map((item, offset) =>
          renderItem(item, currentItems.startIndex + offset)
        )}
      </div>

      <div className="flex items-center justify-center gap-2">
        <button
          type="button"
          onClick={(e) => handleChange(currentPage - 1, e)}
          disabled={currentPage === 1}
          className="px-3 py-1 rounded-full border-2 border-white/40 bg-white/50 text-sm text-slate-600 disabled:text-slate-300 disabled:border-white/20 hover:bg-white/80 transition-all backdrop-blur-sm"
        >
          이전
        </button>
        {Array.from({ length: totalPages }, (_, index) => index + 1).map((page) => (
          <button
            key={page}
            type="button"
            onClick={(e) => handleChange(page, e)}
            className={`w-7 h-7 rounded-full text-xs font-medium transition-all duration-200 border-2 ${page === currentPage
                ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.6)] ring-2 ring-blue-300'
                : 'bg-white/50 border-white/40 text-slate-600 hover:bg-white/80 hover:border-white/80'
              }`}
          >
            {page}
          </button>
        ))}

        <button
          type="button"
          onClick={(e) => handleChange(currentPage + 1, e)}
          disabled={currentPage === totalPages}
          className="px-3 py-1 rounded-full border-2 border-white/40 bg-white/50 text-sm text-slate-600 disabled:text-slate-300 disabled:border-white/20 hover:bg-white/80 transition-all backdrop-blur-sm"
        >
          다음
        </button>
      </div>
    </div>
  )
}
