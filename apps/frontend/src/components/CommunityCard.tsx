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
import { useParticleEffect } from '../hooks/useParticleEffect'

interface Post {
  id: string
  boardType: 'free' | 'region'
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

  const handleCardClick = (event: MouseEvent<HTMLDivElement>) => {
    onClick(post)
  }

  const handleLikeClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    onToggleLike(post.id)
  }

  return (
    <div
      onClick={handleCardClick}
      className="group relative rounded-2xl border border-slate-200 bg-white shadow-sm hover:shadow-lg hover:border-[#16375B]/20 transition-all duration-300 cursor-pointer overflow-hidden"
    >
      {/* 왼쪽 액센트 바 */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-[#16375B] to-[#16375B]/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

      <div className="p-5 pl-6">
        {/* 상단: 제목과 지역 태그 */}
        <div className="mb-3">
          <h3 className="font-bold text-slate-900 mb-2 line-clamp-1 text-lg group-hover:text-[#16375B] transition-colors duration-200">
            {post.title}
          </h3>

          {/* 지역 태그 (행정동 커뮤니티인 경우) */}
          {post.region && (
            <div className="flex flex-wrap gap-2 mb-3">
              <span className="inline-flex items-center px-3 py-1 bg-[#16375B]/5 text-[#16375B] text-xs font-semibold rounded-full border border-[#16375B]/10">
                {post.region}
              </span>
              {post.dong && (
                <span className="inline-flex items-center px-3 py-1 bg-[#16375B]/5 text-[#16375B] text-xs font-semibold rounded-full border border-[#16375B]/10">
                  {post.dong}
                </span>
              )}
              {post.complexName && (
                <span className="inline-flex items-center px-3 py-1 bg-[#16375B]/5 text-[#16375B] text-xs font-semibold rounded-full border border-[#16375B]/10">
                  {post.complexName}
                </span>
              )}
            </div>
          )}
        </div>

        {/* 내용 미리보기 */}
        <p className="text-sm text-slate-600 mb-4 line-clamp-2 leading-relaxed">
          {post.content}
        </p>

        {/* 하단 정보 */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-100">
          {/* 작성자 정보 */}
          <div className="flex items-center gap-2.5">
            <div className="relative w-8 h-8 rounded-full bg-gradient-to-br from-[#16375B] to-[#2a4a6f] overflow-hidden flex-shrink-0 ring-2 ring-white shadow-sm">
              {post.author.profileImage ? (
                <img
                  src={post.author.profileImage}
                  alt={post.author.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-white">
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
            <div className="flex flex-col">
              <span className="text-sm text-slate-800 font-semibold">{post.author.name}</span>
              <span className="text-xs text-slate-400">{formatDate(post.createdAt)}</span>
            </div>
          </div>

          {/* 좋아요 & 댓글 수 */}
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={handleLikeClick}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${post.isLiked
                ? 'text-red-500 bg-red-50 hover:bg-red-100'
                : 'text-slate-400 hover:text-red-500 hover:bg-red-50'
                }`}
              aria-pressed={post.isLiked}
              aria-label="좋아요"
            >
              <svg
                className="w-4 h-4"
                fill={post.isLiked ? 'currentColor' : 'none'}
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
              <span className="font-semibold">{post.likes}</span>
            </button>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-400 bg-slate-50">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <span className="text-sm font-semibold">{post.comments}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
