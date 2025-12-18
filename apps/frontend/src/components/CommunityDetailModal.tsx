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
import { fetchComments, createComment, updateComment, deleteComment } from '../api/communityApi'

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
  onCommentCountChange?: (postId: string, newCount: number) => void
}

export default function CommunityDetailModal({
  post,
  isOpen,
  onClose,
  onEdit,
  onDelete,
  onToggleLike,
  onCommentCountChange
}: CommunityDetailModalProps) {
  const [comments, setComments] = useState<Comment[]>([])
  const [newComment, setNewComment] = useState('')
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null)
  const [editingCommentContent, setEditingCommentContent] = useState('')
  const [isLoadingComments, setIsLoadingComments] = useState(false)
  const commentsContainerRef = useRef<HTMLDivElement>(null)

  // 모달이 열릴 때 댓글 로드
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      loadComments()
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, post.id])

  // 댓글 로드 함수
  const loadComments = async () => {
    try {
      setIsLoadingComments(true)
      const data = await fetchComments(post.id)

      // API 응답을 Comment 형태로 변환
      const formattedComments: Comment[] = data.map((comment: any) => ({
        id: comment.id.toString(),
        author: {
          name: comment.author_name || '익명',
          profileImage: comment.author_profile_image
        },
        content: comment.content,
        createdAt: new Date(comment.created_at),
        isOwner: comment.is_owner || false
      }))

      setComments(formattedComments)
    } catch (error) {
      console.error('Failed to load comments:', error)
      // 에러 시 빈 배열 유지
    } finally {
      setIsLoadingComments(false)
    }
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
  const handleAddComment = async (e?: React.MouseEvent) => {
    if (!newComment.trim()) return

    try {
      const data = await createComment(post.id, newComment.trim())

      // 새 댓글을 목록에 추가
      const newCommentObj: Comment = {
        id: data.id.toString(),
        author: {
          name: data.author_name || '현재 사용자',
          profileImage: data.author_profile_image
        },
        content: data.content,
        createdAt: new Date(data.created_at),
        isOwner: true
      }

      setComments(prev => {
        const newComments = [...prev, newCommentObj]
        // 부모 컴포넌트에 댓글 수 업데이트 알림
        onCommentCountChange?.(post.id, newComments.length)
        return newComments
      })
      setNewComment('')

      // 댓글 작성 후 스크롤을 맨 아래로
      setTimeout(() => {
        if (commentsContainerRef.current) {
          commentsContainerRef.current.scrollTop = commentsContainerRef.current.scrollHeight
        }
      }, 100)
    } catch (error) {
      console.error('Failed to create comment:', error)
      alert('댓글 작성에 실패했습니다.')
    }
  }

  // 댓글 수정 시작
  const handleStartEditComment = (comment: Comment, e: React.MouseEvent) => {
    setEditingCommentId(comment.id)
    setEditingCommentContent(comment.content)
  }

  // 댓글 수정 완료
  const handleUpdateComment = async (commentId: string, e: React.MouseEvent) => {
    if (!editingCommentContent.trim()) return

    try {
      await updateComment(post.id, commentId, editingCommentContent.trim())

      setComments(prev =>
        prev.map(comment =>
          comment.id === commentId
            ? { ...comment, content: editingCommentContent.trim() }
            : comment
        )
      )
      setEditingCommentId(null)
      setEditingCommentContent('')
    } catch (error) {
      console.error('Failed to update comment:', error)
      alert('댓글 수정에 실패했습니다.')
    }
  }

  // 댓글 삭제
  const handleDeleteComment = async (commentId: string, e: React.MouseEvent) => {
    if (!confirm('댓글을 삭제하시겠습니까?')) return

    try {
      await deleteComment(post.id, commentId)
      setComments(prev => {
        const newComments = prev.filter(comment => comment.id !== commentId)
        // 부모 컴포넌트에 댓글 수 업데이트 알림
        onCommentCountChange?.(post.id, newComments.length)
        return newComments
      })
    } catch (error) {
      console.error('Failed to delete comment:', error)
      alert('댓글 삭제에 실패했습니다.')
    }
  }

  // Enter 키로 댓글 작성
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAddComment()
    }
  }

  const handleClose = (e?: React.MouseEvent) => {
    onClose()
  }

  const handleEditPost = (e?: React.MouseEvent<HTMLButtonElement>) => {
    onEdit?.()
  }

  const handleDeletePost = (e?: React.MouseEvent<HTMLButtonElement>) => {
    onDelete?.()
  }

  const handleLikePost = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation()
    onToggleLike?.(post.id)
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="rounded-3xl bg-white shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="text-xl font-bold text-slate-900">게시글 상세</h2>
          <button
            onClick={handleClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-all"
            aria-label="모달 닫기"
          >
            <svg
              className="w-5 h-5"
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
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {/* 작성자 정보 */}
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="relative w-12 h-12 rounded-full bg-gradient-to-br from-[#16375B] to-[#2a4a6f] overflow-hidden flex-shrink-0 ring-2 ring-white shadow-md">
                {post.author.profileImage ? (
                  <img
                    src={post.author.profileImage}
                    alt={post.author.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-white">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
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
                <p className="font-semibold text-base text-slate-900">{post.author.name}</p>
                <p className="text-sm text-slate-500">{formatDate(post.createdAt)}</p>
              </div>
            </div>

            {/* 게시글 수정/삭제 버튼 (작성자만) */}
            {post.isOwner && (
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={handleEditPost}>
                  수정
                </Button>
                <Button variant="danger" size="sm" onClick={handleDeletePost}>
                  삭제
                </Button>
              </div>
            )}
          </div>

          {/* 지역 태그 */}
          {post.region && (
            <div className="mb-4 flex flex-wrap gap-2">
              <span className="inline-flex items-center px-3 py-1.5 bg-[#16375B]/5 text-[#16375B] text-xs font-semibold rounded-full border border-[#16375B]/10">
                {post.region}
              </span>
              {post.dong && (
                <span className="inline-flex items-center px-3 py-1.5 bg-[#16375B]/5 text-[#16375B] text-xs font-semibold rounded-full border border-[#16375B]/10">
                  {post.dong}
                </span>
              )}
              {post.complexName && (
                <span className="inline-flex items-center px-3 py-1.5 bg-[#16375B]/5 text-[#16375B] text-xs font-semibold rounded-full border border-[#16375B]/10">
                  {post.complexName}
                </span>
              )}
            </div>
          )}

          {/* 게시글 제목 */}
          <h3 className="text-2xl font-bold text-slate-900 mb-4 leading-tight">{post.title}</h3>

          {/* 게시글 내용 */}
          <p className="text-base text-slate-700 leading-relaxed mb-6 whitespace-pre-wrap">
            {post.content}
          </p>

          {/* 좋아요 & 댓글 수 */}
          <div className="flex items-center gap-4 py-4 border-y border-slate-100 mb-6">
            <button
              onClick={handleLikePost}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${post.isLiked
                ? 'text-red-500 bg-red-50 hover:bg-red-100'
                : 'text-slate-500 hover:text-red-500 hover:bg-red-50'
                }`}
            >
              <svg
                className="w-5 h-5"
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
              <span className="font-semibold text-sm">{post.likes}</span>
            </button>
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-50 text-slate-500">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <span className="font-semibold text-sm">{comments.length}</span>
            </div>
          </div>

          {/* 댓글 목록 */}
          <div className="space-y-4" ref={commentsContainerRef}>
            <h4 className="font-bold text-lg text-slate-900 mb-4">
              댓글 {comments.length}
            </h4>
            {comments.length === 0 ? (
              <div className="text-center py-12 bg-slate-50 rounded-2xl">
                <svg className="w-12 h-12 mx-auto mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p className="text-sm text-slate-500">첫 댓글을 작성해보세요!</p>
              </div>
            ) : (
              comments.map((comment) => (
                <div
                  key={comment.id}
                  className="bg-slate-50 rounded-2xl p-4 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#16375B] to-[#2a4a6f] overflow-hidden flex-shrink-0 ring-2 ring-white shadow-sm">
                        {comment.author.profileImage ? (
                          <img
                            src={comment.author.profileImage}
                            alt={comment.author.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-white">
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
                        <p className="font-semibold text-sm text-slate-900">
                          {comment.author.name}
                        </p>
                        <p className="text-xs text-slate-500">
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
                              onClick={(e) => handleUpdateComment(comment.id, e)}
                              className="text-xs font-medium text-[#16375B] hover:underline"
                            >
                              완료
                            </button>
                            <button
                              onClick={() => setEditingCommentId(null)}
                              className="text-xs font-medium text-slate-500 hover:underline"
                            >
                              취소
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={(e) => handleStartEditComment(comment, e)}
                              className="text-xs font-medium text-[#16375B] hover:underline"
                            >
                              수정
                            </button>
                            <button
                              onClick={(e) => handleDeleteComment(comment.id, e)}
                              className="text-xs font-medium text-red-500 hover:underline"
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
                      className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#16375B] focus:border-transparent bg-white"
                      autoFocus
                    />
                  ) : (
                    <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {comment.content}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* 댓글 입력 영역 */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50">
          <div className="flex gap-3">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="댓글을 입력하세요..."
              className="flex-1 px-4 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#16375B] focus:border-transparent bg-white placeholder-slate-400"
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
