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

  // 표시할 페이지 번호 계산 (최대 5개)
  const getVisiblePages = () => {
    const maxVisible = 5
    if (totalPages <= maxVisible) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }
    
    let start = Math.max(1, currentPage - 2)
    let end = Math.min(totalPages, start + maxVisible - 1)
    
    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1)
    }
    
    return Array.from({ length: end - start + 1 }, (_, i) => start + i)
  }

  if (items.length === 0) {
    return <div className="space-y-4">{emptyMessage}</div>
  }

  const visiblePages = getVisiblePages()

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        {currentItems.data.map((item, offset) =>
          renderItem(item, currentItems.startIndex + offset)
        )}
      </div>

      {/* 세련된 페이지네이션 */}
      <div className="flex items-center justify-center">
        <div className="inline-flex items-center gap-1 p-2 rounded-2xl bg-white/60 backdrop-blur-md border border-white/40 shadow-lg">
          {/* 처음으로 버튼 */}
          <button
            type="button"
            onClick={(e) => handleChange(1, e)}
            disabled={currentPage === 1}
            className="w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 disabled:text-slate-300 disabled:cursor-not-allowed hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
            title="처음으로"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>

          {/* 이전 버튼 */}
          <button
            type="button"
            onClick={(e) => handleChange(currentPage - 1, e)}
            disabled={currentPage === 1}
            className="w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 disabled:text-slate-300 disabled:cursor-not-allowed hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
            title="이전"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {/* 구분선 */}
          <div className="w-px h-6 bg-slate-200 mx-1"></div>

          {/* 첫 페이지 + ... */}
          {visiblePages[0] > 1 && (
            <>
              <button
                type="button"
                onClick={(e) => handleChange(1, e)}
                className="w-9 h-9 rounded-xl text-sm font-medium text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
              >
                1
              </button>
              {visiblePages[0] > 2 && (
                <span className="w-9 h-9 flex items-center justify-center text-slate-400 text-sm">...</span>
              )}
            </>
          )}

          {/* 페이지 번호들 */}
          {visiblePages.map((page) => (
            <button
              key={page}
              type="button"
              onClick={(e) => handleChange(page, e)}
              className={`
                w-9 h-9 rounded-xl text-sm font-semibold transition-all duration-200
                ${page === currentPage
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/30 scale-105'
                  : 'text-slate-600 hover:bg-blue-50 hover:text-blue-600'
                }
              `}
            >
              {page}
            </button>
          ))}

          {/* ... + 마지막 페이지 */}
          {visiblePages[visiblePages.length - 1] < totalPages && (
            <>
              {visiblePages[visiblePages.length - 1] < totalPages - 1 && (
                <span className="w-9 h-9 flex items-center justify-center text-slate-400 text-sm">...</span>
              )}
              <button
                type="button"
                onClick={(e) => handleChange(totalPages, e)}
                className="w-9 h-9 rounded-xl text-sm font-medium text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
              >
                {totalPages}
              </button>
            </>
          )}

          {/* 구분선 */}
          <div className="w-px h-6 bg-slate-200 mx-1"></div>

          {/* 다음 버튼 */}
          <button
            type="button"
            onClick={(e) => handleChange(currentPage + 1, e)}
            disabled={currentPage === totalPages}
            className="w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 disabled:text-slate-300 disabled:cursor-not-allowed hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
            title="다음"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          {/* 끝으로 버튼 */}
          <button
            type="button"
            onClick={(e) => handleChange(totalPages, e)}
            disabled={currentPage === totalPages}
            className="w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 disabled:text-slate-300 disabled:cursor-not-allowed hover:bg-blue-50 hover:text-blue-600 transition-all duration-200"
            title="끝으로"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      {/* 페이지 정보 */}
      <div className="text-center">
        <span className="text-sm text-slate-500">
          총 <span className="font-semibold text-slate-700">{items.length}</span>개 중{' '}
          <span className="font-semibold text-blue-600">{currentPage}</span> / {totalPages} 페이지
        </span>
      </div>
    </div>
  )
}
