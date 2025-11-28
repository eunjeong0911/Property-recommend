/**
 * CommunityCard 컴포넌트
 *
 * 커뮤니티 게시글 카드 컴포넌트
 *
 * 주요 기능:
 * - 게시글 작성자 프로필 이미지와 이름 표시
 * - 게시글 제목 표시
 * - 게시글 내용 미리보기
 * - 작성 날짜 표시
 * - 여러 게시글은 옆으로 스와이프하면서 표시
 * - 좋아요 수 아이콘과 함께 표시
 * - 댓글 수 아이콘과 함께 표시
 * - 카드 클릭 시 CommunityDetailModal 열기
 */

'use client'

import type { MouseEvent } from 'react'

interface Post {
  id: string
  author: {
    name: string
    profileImage?: string
  }
  title: string
  content: string
  createdAt: Date
  likes: number
  comments: number
  region?: string
  dong?: string
  complexName?: string
  isOwner: boolean
  isLiked?: boolean
}

interface CommunityCardProps {
  post: Post
  onClick: (post: Post) => void
  onToggleLike: (postId: string) => void
}

export default function CommunityCard({ post, onClick, onToggleLike }: CommunityCardProps) {
  // 날짜 포맷 함수
  const formatDate = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const diffMinutes = Math.floor(diff / (1000 * 60))
    const diffHours = Math.floor(diff / (1000 * 60 * 60))
    const diffDays = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (diffMinutes < 1) return '방금 전'
    if (diffMinutes < 60) return `${diffMinutes}분 전`
    if (diffHours < 24) return `${diffHours}시간 전`
    if (diffDays < 7) return `${diffDays}일 전`

    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
  }

  const handleLikeClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    onToggleLike(post.id)
  }

  return (
    <div
      onClick={() => onClick(post)}
      className="bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow cursor-pointer overflow-hidden"
    >
      <div className="p-4">
        {/* 제목 */}
        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 text-base">
          {post.title}
        </h3>

        {/* 내용 미리보기 */}
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {post.content}
        </p>

        {/* 지역 태그 (행정동 커뮤니티인 경우) */}
        {post.region && (
          <div className="mb-3 flex flex-wrap gap-1.5">
            <span className="inline-block px-2 py-1 bg-orange-50 text-orange-600 text-xs font-medium rounded">
              {post.region}
            </span>
            {post.dong && (
              <span className="inline-block px-2 py-1 bg-orange-50 text-orange-600 text-xs font-medium rounded">
                {post.dong}
              </span>
            )}
            {post.complexName && (
              <span className="inline-block px-2 py-1 bg-blue-50 text-blue-600 text-xs font-medium rounded">
                {post.complexName}
              </span>
            )}
          </div>
        )}

        {/* 하단 정보 */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          {/* 작성자 정보 */}
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gray-200 overflow-hidden flex-shrink-0">
              {post.author.profileImage ? (
                <img
                  src={post.author.profileImage}
                  alt={post.author.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-500">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              )}
            </div>
            <span className="text-xs text-gray-600">{post.author.name}</span>
            <span className="text-xs text-gray-400">·</span>
            <span className="text-xs text-gray-400">{formatDate(post.createdAt)}</span>
          </div>

          {/* 좋아요 & 댓글 수 */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleLikeClick}
              className={`flex items-center gap-1 text-xs font-medium transition-colors ${
                post.isLiked ? 'text-red-600' : 'text-gray-500 hover:text-red-500'
              }`}
              aria-pressed={post.isLiked}
              aria-label="좋아요"
            >
              <svg
                className="w-4 h-4"
                fill={post.isLiked ? 'currentColor' : 'none'}
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
              <span>{post.likes}</span>
            </button>
            <div className="flex items-center gap-1 text-gray-500">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <span className="text-xs">{post.comments}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
