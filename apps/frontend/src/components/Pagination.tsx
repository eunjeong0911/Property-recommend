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

interface PaginationProps<T = unknown> {
  items: T[]
  renderItem: (item: T, index: number) => ReactNode
  pageSize?: number
  emptyMessage?: ReactNode
}

const DEFAULT_EMPTY = (
  <div className="bg-white border border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-500">
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

  const handleChange = (page: number) => {
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
          onClick={() => handleChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-1 rounded-md border border-gray-200 text-sm text-gray-600 disabled:text-gray-300 disabled:border-gray-100"
        >
          이전
        </button>

        {Array.from({ length: totalPages }, (_, index) => index + 1).map((page) => (
          <button
            key={page}
            type="button"
            onClick={() => handleChange(page)}
            className={`w-8 h-8 rounded-md text-sm font-medium transition-colors ${
              page === currentPage
                ? 'bg-blue-500 text-white shadow-sm'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            {page}
          </button>
        ))}

        <button
          type="button"
          onClick={() => handleChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-1 rounded-md border border-gray-200 text-sm text-gray-600 disabled:text-gray-300 disabled:border-gray-100"
        >
          다음
        </button>
      </div>
    </div>
  )
}
