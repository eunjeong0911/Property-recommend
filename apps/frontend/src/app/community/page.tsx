/**
 * CommunityPage
 *
 * 커뮤니티 페이지
 *
 * Header.tsx, Chatbot.tsx, CommunityTab.tsx 등과 함께 동작
 */

'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSession } from 'next-auth/react'
import Button from '@/components/Button'
import CommunityCard from '@/components/CommunityCard'
import CommunityDetailModal from '@/components/CommunityDetailModal'
import CommunityTab from '@/components/CommunityTab'
import CommunityWriteModal from '@/components/CommunityWriteModal'
import Pagination from '@/components/Pagination'
import RegionFilter, { type RegionFilterValues } from '@/components/RegionFilter'
import type { CommunityWriteFormValues } from '@/components/CommunityWriteForm'
import axiosInstance from '@/lib/axios'

type BoardType = 'free' | 'region'

interface CommunityPost {
  id: string
  boardType: BoardType
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

interface ApiCommunityPost {
  id: number
  title: string
  content: string
  author_name?: string
  author_email?: string
  board_type: BoardType
  region?: string | null
  dong?: string | null
  complex_name?: string | null
  like_count: number
  comment_count: number
  created_at: string
  updated_at: string
}

export default function CommunityPage() {
  const { data: session } = useSession()
  const [activeTab, setActiveTab] = useState<BoardType>('free')
  const [posts, setPosts] = useState<CommunityPost[]>([])
  const [selectedPost, setSelectedPost] = useState<CommunityPost | null>(null)
  const [editingPost, setEditingPost] = useState<CommunityPost | null>(null)
  const [isWriteModalOpen, setIsWriteModalOpen] = useState(false)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [regionFilter, setRegionFilter] = useState<RegionFilterValues>({})
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mapApiPost = useCallback(
    (item: ApiCommunityPost): CommunityPost => ({
      id: String(item.id),
      boardType: item.board_type === 'region' ? 'region' : 'free',
      author: { name: item.author_name || '사용자' },
      title: item.title,
      content: item.content,
      createdAt: new Date(item.created_at),
      likes: item.like_count ?? 0,
      comments: item.comment_count ?? 0,
      region: item.region || undefined,
      dong: item.dong || undefined,
      complexName: item.complex_name || undefined,
      isOwner: item.author_email === session?.user?.email,
      isLiked: false,
    }),
    [session?.user?.email]
  )

  const fetchPosts = useCallback(
    async (board: BoardType, filters?: RegionFilterValues) => {
      setIsLoading(true)
      setError(null)
      try {
        const params: Record<string, string> = { board }
        if (board === 'region' && filters) {
          if (filters.region) params.region = filters.region
          if (filters.dong) params.dong = filters.dong
          if (filters.complexName) params.complex_name = filters.complexName
        }
        const response = await axiosInstance.get<ApiCommunityPost[]>('/api/community/posts/', { params })
        const mapped = response.data.map(mapApiPost)
        setPosts(mapped)
        setSelectedPost((prev) => {
          if (!prev) return prev
          const next = mapped.find((post) => post.id === prev.id)
          return next ?? prev
        })
      } catch (fetchError) {
        console.error(fetchError)
        setError('게시글을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.')
      } finally {
        setIsLoading(false)
      }
    },
    [mapApiPost]
  )

  useEffect(() => {
    if (activeTab === 'free') {
      fetchPosts('free')
    }
  }, [activeTab, fetchPosts])

useEffect(() => {
  if (activeTab === 'region') {
    fetchPosts('region', regionFilter)
  }
}, [activeTab, regionFilter, fetchPosts])

  const filteredPosts = useMemo(() => {
    if (activeTab !== 'region') {
      return posts
    }
    return posts.filter((post) => {
      if (regionFilter.region && post.region !== regionFilter.region) return false
      if (regionFilter.dong && post.dong !== regionFilter.dong) return false
      if (regionFilter.complexName && !post.complexName?.includes(regionFilter.complexName)) return false
      return true
    })
  }, [activeTab, posts, regionFilter])

  const handleFilterChange = (filter: RegionFilterValues) => {
    setRegionFilter(filter)
  }

  const handleWriteClick = () => {
    setEditingPost(null)
    setIsWriteModalOpen(true)
  }

  const handleCardClick = (post: CommunityPost) => {
    setSelectedPost(post)
    setIsDetailModalOpen(true)
  }

  const closeWriteModal = () => {
    setIsWriteModalOpen(false)
  }

  const closeDetailModal = () => {
    setIsDetailModalOpen(false)
    setSelectedPost(null)
  }

  const handleSubmitPost = async (values: CommunityWriteFormValues, regionData?: RegionFilterValues) => {
    const targetBoard = editingPost?.boardType ?? activeTab
    if (targetBoard === 'region' && (!regionData?.region || !regionData?.dong || !regionData?.complexName)) {
      alert('지역, 동, 단지명을 모두 선택해주세요.')
      throw new Error('missing region data')
    }

    const payload: Record<string, unknown> = {
      title: values.title,
      content: values.content,
      board_type: targetBoard,
    }

    if (targetBoard === 'region' && regionData) {
      payload.region = regionData.region
      payload.dong = regionData.dong
      payload.complex_name = regionData.complexName
    }

    try {
      if (editingPost) {
        await axiosInstance.patch(`/api/community/posts/${editingPost.id}/`, payload)
      } else {
        await axiosInstance.post('/api/community/posts/', payload)
      }
      setEditingPost(null)
      await fetchPosts(targetBoard, targetBoard === 'region' ? regionFilter : undefined)
    } catch (submitError) {
      console.error(submitError)
      alert('게시글 저장에 실패했습니다. 잠시 후 다시 시도해주세요.')
      throw submitError
    }
  }

  const handleToggleLike = (postId: string) => {
    setPosts((prev) =>
      prev.map((post) =>
        post.id === postId
          ? {
              ...post,
              isLiked: !post.isLiked,
              likes: post.isLiked ? post.likes - 1 : post.likes + 1,
            }
          : post
      )
    )
    setSelectedPost((prev) =>
      prev && prev.id === postId
        ? {
            ...prev,
            isLiked: !prev.isLiked,
            likes: prev.isLiked ? prev.likes - 1 : prev.likes + 1,
          }
        : prev
    )
  }

  const handleDeletePost = async () => {
    if (!selectedPost) return
    if (!confirm('게시글을 삭제하시겠습니까?')) {
      return
    }
    try {
      await axiosInstance.delete(`/api/community/posts/${selectedPost.id}/`)
      closeDetailModal()
      await fetchPosts(activeTab, activeTab === 'region' ? regionFilter : undefined)
    } catch (deleteError) {
      console.error(deleteError)
      alert('게시글 삭제에 실패했습니다.')
    }
  }

  const handleEditSelectedPost = () => {
    if (!selectedPost) return
    setActiveTab(selectedPost.boardType)
    setEditingPost(selectedPost)
    setIsWriteModalOpen(true)
    setIsDetailModalOpen(false)
  }

  const editingFormValues: CommunityWriteFormValues | undefined = editingPost
    ? { title: editingPost.title, content: editingPost.content }
    : undefined

  const editingRegionData: RegionFilterValues | undefined = editingPost
    ? {
        region: editingPost.region,
        dong: editingPost.dong,
        complexName: editingPost.complexName,
      }
    : undefined

  const writeModalTitle = editingPost
    ? '게시글 수정'
    : activeTab === 'free'
      ? '자유게시판 글쓰기'
      : '지역 커뮤니티 글쓰기'

  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8">
        <CommunityTab activeTab={activeTab} onTabChange={setActiveTab} />

        <div className="flex justify-end mb-6">
          <Button variant="primary" onClick={handleWriteClick}>
            글쓰기
          </Button>
        </div>

        {activeTab === 'region' && (
          <RegionFilter onFilterChange={handleFilterChange} />
        )}

        {error && (
          <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="py-20 text-center text-slate-500">게시글을 불러오는 중입니다...</div>
        ) : (
          <Pagination
            items={filteredPosts}
            pageSize={5}
            renderItem={(post) => (
              <CommunityCard
                key={post.id}
                post={post}
                onClick={handleCardClick}
                onToggleLike={handleToggleLike}
              />
            )}
          />
        )}
      </main>

      <CommunityWriteModal
        isOpen={isWriteModalOpen}
        onClose={closeWriteModal}
        title={writeModalTitle}
        initialData={editingFormValues}
        initialRegionData={editingRegionData}
        submitLabel={editingPost ? '수정하기' : '등록하기'}
        showRegionFilter={editingPost?.boardType === 'region' || activeTab === 'region'}
        onSubmit={handleSubmitPost}
      />

      {selectedPost && (
        <CommunityDetailModal
          post={selectedPost}
          isOpen={isDetailModalOpen}
          onClose={closeDetailModal}
          onEdit={handleEditSelectedPost}
          onDelete={handleDeletePost}
          onToggleLike={handleToggleLike}
        />
      )}
    </div>
  )
}
