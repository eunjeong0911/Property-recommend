/**
 * CommunityDetailModal 컴포넌트
 *
 * 커뮤니티 게시글 상세보기 모달 컴포넌트
 *
 * 주요 기능:
 * - 작성자 정보 표시 (프로필 이미지, 이름)
 * - 게시글 제목 및 내용 표시
 * - 좋아요 수 및 댓글 수 표시
 * - 해당 작성자에게만 게시글 수정, 삭제 버튼 표시
 * - 댓글 목록 표시 (작성자 프로필, 내용)
 * - 댓글 작성 입력
 * - 댓글 작성자에게만 해당 댓글 수정, 삭제 버튼 표시
 * - 댓글 총 수 표시
 * - 댓글 여러개는 스크롤로 표시
 * - 모달 오른쪽 상단 X 버튼으로 닫기
 **/

'use client'

import { useState, useEffect, useRef } from 'react'
import Button from './Button'

interface Comment {
  id: string
  author: {
    name: string
    profileImage?: string
  }
  content: string
  createdAt: Date
  isOwner: boolean
}

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

interface CommunityDetailModalProps {
  post: Post
  isOpen: boolean
  onClose: () => void
  onEdit?: () => void
  onDelete?: () => void
  onToggleLike?: (postId: string) => void
}

export default function CommunityDetailModal({
  post,
  isOpen,
  onClose,
  onEdit,
  onDelete,
  onToggleLike
}: CommunityDetailModalProps) {
  const [comments, setComments] = useState<Comment[]>([])
  const [newComment, setNewComment] = useState('')
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null)
  const [editingCommentContent, setEditingCommentContent] = useState('')
  const commentsContainerRef = useRef<HTMLDivElement>(null)

  // 모달이 열릴 때 스크롤 방지
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      // 임시 댓글 데이터 로드 (실제로는 API 호출)
      loadComments()
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  // 댓글 로드 함수
  const loadComments = () => {
    // 실제로는 API 호출
    // 빈 배열로 초기화 - 사용자가 작성한 댓글만 표시됨
    setComments([])
  }

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

  // 댓글 작성
  const handleAddComment = () => {
    if (!newComment.trim()) return

    const comment: Comment = {
      id: Date.now().toString(),
      author: { name: '현재 사용자' },
      content: newComment,
      createdAt: new Date(),
      isOwner: true
    }

    setComments(prev => [...prev, comment])
    setNewComment('')
  }

  // 댓글 수정 시작
  const handleStartEditComment = (comment: Comment) => {
    setEditingCommentId(comment.id)
    setEditingCommentContent(comment.content)
  }

  // 댓글 수정 완료
  const handleUpdateComment = (commentId: string) => {
    if (!editingCommentContent.trim()) return

    setComments(prev =>
      prev.map(comment =>
        comment.id === commentId
          ? { ...comment, content: editingCommentContent }
          : comment
      )
    )
    setEditingCommentId(null)
    setEditingCommentContent('')
  }

  // 댓글 삭제
  const handleDeleteComment = (commentId: string) => {
    if (confirm('댓글을 삭제하시겠습니까?')) {
      setComments(prev => prev.filter(comment => comment.id !== commentId))
    }
  }

  // Enter 키로 댓글 작성
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAddComment()
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">게시글 상세</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="모달 닫기"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* 내용 */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* 작성자 정보 */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gray-200 overflow-hidden flex-shrink-0">
                {post.author.profileImage ? (
                  <img
                    src={post.author.profileImage}
                    alt={post.author.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-600">
                    <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}
              </div>
              <div>
                <p className="font-medium text-gray-900">{post.author.name}</p>
                <p className="text-sm text-gray-500">{formatDate(post.createdAt)}</p>
              </div>
            </div>

            {/* 게시글 수정/삭제 버튼 (작성자만) - Button 컴포넌트 사용 */}
            {post.isOwner && (
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={onEdit}>
                  수정
                </Button>
                <Button variant="danger" size="sm" onClick={onDelete}>
                  삭제
                </Button>
              </div>
            )}
          </div>

          {/* 지역 태그 */}
          {post.region && (
            <div className="mb-4 flex flex-wrap gap-2">
              <span className="inline-block px-3 py-1 bg-orange-50 text-orange-600 text-sm font-medium rounded">
                {post.region}
              </span>
              {post.dong && (
                <span className="inline-block px-3 py-1 bg-orange-50 text-orange-600 text-sm font-medium rounded">
                  {post.dong}
                </span>
              )}
              {post.complexName && (
                <span className="inline-block px-3 py-1 bg-blue-50 text-blue-600 text-sm font-medium rounded">
                  {post.complexName}
                </span>
              )}
            </div>
          )}

          {/* 게시글 제목 */}
          <h3 className="text-2xl font-bold text-gray-900 mb-4">{post.title}</h3>

          {/* 게시글 내용 */}
          <p className="text-gray-700 leading-relaxed mb-6 whitespace-pre-wrap">
            {post.content}
          </p>

          {/* 좋아요 & 댓글 수 */}
          <div className="flex items-center gap-6 py-4 border-y border-gray-200 mb-6">
            <button
              onClick={() => onToggleLike?.(post.id)}
              className="flex items-center gap-2 transition-colors hover:text-orange-500 group"
            >
              <svg
                className={`w-5 h-5 transition-colors ${
                  post.isLiked
                    ? 'fill-orange-500 text-orange-500'
                    : 'fill-none text-gray-600 group-hover:text-orange-500'
                }`}
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
              <span className={`font-medium ${post.isLiked ? 'text-orange-500' : 'text-gray-600'}`}>
                {post.likes}
              </span>
            </button>
            <div className="flex items-center gap-2 text-gray-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <span className="font-medium">{comments.length}</span>
            </div>
          </div>

          {/* 댓글 목록 */}
          <div className="space-y-4 mb-6" ref={commentsContainerRef}>
            <h4 className="font-semibold text-gray-900 mb-3">
              댓글 {comments.length}
            </h4>
            {comments.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">
                첫 댓글을 작성해보세요!
              </p>
            ) : (
              comments.map((comment) => (
                <div
                  key={comment.id}
                  className="bg-gray-50 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="w-8 h-8 rounded-full bg-gray-300 overflow-hidden flex-shrink-0">
                        {comment.author.profileImage ? (
                          <img
                            src={comment.author.profileImage}
                            alt={comment.author.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-gray-600">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                              <path
                                fillRule="evenodd"
                                d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </div>
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-sm text-gray-900">
                          {comment.author.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(comment.createdAt)}
                        </p>
                      </div>
                    </div>

                    {/* 댓글 수정/삭제 버튼 (작성자만) */}
                    {comment.isOwner && (
                      <div className="flex gap-2">
                        {editingCommentId === comment.id ? (
                          <>
                            <button
                              onClick={() => handleUpdateComment(comment.id)}
                              className="text-xs text-orange-600 hover:underline"
                            >
                              완료
                            </button>
                            <button
                              onClick={() => setEditingCommentId(null)}
                              className="text-xs text-gray-600 hover:underline"
                            >
                              취소
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => handleStartEditComment(comment)}
                              className="text-xs text-orange-600 hover:underline"
                            >
                              수정
                            </button>
                            <button
                              onClick={() => handleDeleteComment(comment.id)}
                              className="text-xs text-red-600 hover:underline"
                            >
                              삭제
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </div>

                  {/* 댓글 내용 */}
                  {editingCommentId === comment.id ? (
                    <input
                      type="text"
                      value={editingCommentContent}
                      onChange={(e) => setEditingCommentContent(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                      autoFocus
                    />
                  ) : (
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {comment.content}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* 댓글 입력 영역 - Button 컴포넌트 사용 */}
        <div className="p-6 border-t border-gray-200">
          <div className="flex gap-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="댓글을 입력하세요..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <Button
              variant="primary"
              onClick={handleAddComment}
              disabled={!newComment.trim()}
            >
              작성
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
