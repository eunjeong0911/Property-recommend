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

interface PaginationProps {
  currentPage: number
  totalPages: number
  onChange: (page: number) => void
}

export default function Pagination({ currentPage, totalPages, onChange }: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, index) => index + 1)

  const handleChange = (page: number) => {
    if (page < 1 || page > totalPages || page === currentPage) return
    onChange(page)
  }

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => handleChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-1 rounded-md border border-gray-200 text-sm text-gray-600 disabled:text-gray-300 disabled:border-gray-100"
      >
        이전
      </button>

      {pages.map((page) => (
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
  )
}
