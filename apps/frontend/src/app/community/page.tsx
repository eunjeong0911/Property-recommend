/**
 * CommunityPage
 * 
 * 커뮤니티 페이지
 * 
 * Header.tsx (헤더)
 * Chatbot.tsx (챗봇)
 * CommunityTab.tsx (커뮤니티)
 * CommunityCard.tsx (커뮤니티 게시글 카드)
 * CommunityDetailModal.tsx (커뮤니티 게시글 상세 모달)
 * CommunityWriteModal.tsx (커뮤니티 게시글 작성 모달)
 * CommunityWriteForm.tsx (커뮤니티 게시글 작성 폼)
 * RegionFilter.tsx (행정동 커뮤니티 게시글 작성할때 지역 필터)
 * Pagination.tsx (페이지네이션)
 * Button.tsx (등록하기 버튼, 작성 버튼)
 * Footer.tsx (푸터)
 * 
 */

'use client'

import { useMemo, useState } from 'react'
import Button from '@/components/Button'
import CommunityCard from '@/components/CommunityCard'
import CommunityDetailModal from '@/components/CommunityDetailModal'
import CommunityTab from '@/components/CommunityTab'
import CommunityWriteModal from '@/components/CommunityWriteModal'
import Pagination from '@/components/Pagination'
import RegionFilter, { type RegionFilterValues } from '@/components/RegionFilter'
import type { CommunityWriteFormValues } from '@/components/CommunityWriteForm'
import { useCommunityStore } from '@/store/useCommunityStore'

interface CommunityPost {
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

export default function CommunityPage() {
  const {
    activeTab,
    setActiveTab,
    freePosts,
    regionPosts,
    addPost,
    updatePost,
    deletePost,
    toggleLike,
    selectedPost,
    setSelectedPost,
    isDetailModalOpen,
    openDetailModal,
    closeDetailModal,
    isWriteModalOpen,
    openWriteModal,
    closeWriteModal,
    editingPost,
    setEditingPost
  } = useCommunityStore((state) => ({
    activeTab: state.activeTab,
    setActiveTab: state.setActiveTab,
    freePosts: state.freePosts,
    regionPosts: state.regionPosts,
    addPost: state.addPost,
    updatePost: state.updatePost,
    deletePost: state.deletePost,
    toggleLike: state.toggleLike,
    selectedPost: state.selectedPost,
    setSelectedPost: state.setSelectedPost,
    isDetailModalOpen: state.isDetailModalOpen,
    openDetailModal: state.openDetailModal,
    closeDetailModal: state.closeDetailModal,
    isWriteModalOpen: state.isWriteModalOpen,
    openWriteModal: state.openWriteModal,
    closeWriteModal: state.closeWriteModal,
    editingPost: state.editingPost,
    setEditingPost: state.setEditingPost
  }))

  const [regionFilter, setRegionFilter] = useState<RegionFilterValues>({})

  const posts = activeTab === 'free' ? freePosts : regionPosts

  const filteredPosts = useMemo(() => {
    if (activeTab === 'free') {
      return posts
    }

    return posts.filter((post) => {
      if (regionFilter.region && post.region !== regionFilter.region) {
        return false
      }
      if (regionFilter.dong && post.dong !== regionFilter.dong) {
        return false
      }
      if (regionFilter.complexName && !post.complexName?.includes(regionFilter.complexName)) {
        return false
      }
      return true
    })
  }, [posts, regionFilter, activeTab])

  const handleFilterChange = (filter: RegionFilterValues) => {
    setRegionFilter(filter)
  }

  const handleWriteClick = () => {
    setEditingPost(null)
    openWriteModal()
  }

  const handleCardClick = (post: CommunityPost) => {
    openDetailModal(post)
  }

  const handleSubmitPost = (values: CommunityWriteFormValues, regionData?: RegionFilterValues) => {
    const basePost = editingPost ?? null

    const payload: CommunityPost = {
      id: basePost?.id ?? Date.now().toString(),
      author: basePost?.author ?? { name: '현재 사용자' },
      title: values.title,
      content: values.content,
      createdAt: basePost?.createdAt ?? new Date(),
      likes: basePost?.likes ?? 0,
      comments: basePost?.comments ?? 0,
      region: regionData?.region,
      dong: regionData?.dong,
      complexName: regionData?.complexName,
      isOwner: true,
      isLiked: basePost?.isLiked ?? false
    }

    if (basePost) {
      updatePost(payload)
      if (selectedPost && selectedPost.id === payload.id) {
        setSelectedPost(payload)
      }
    } else {
      addPost(payload)
    }
  }

  const handleToggleLike = (postId: string) => {
    toggleLike(postId)
  }

  const handleDeletePost = () => {
    if (!selectedPost) return
    deletePost(selectedPost.id)
    closeDetailModal()
  }

  const handleEditSelectedPost = () => {
    if (!selectedPost) return
    setActiveTab(selectedPost.region ? 'region' : 'free')
    setEditingPost(selectedPost)
    closeDetailModal()
    openWriteModal()
  }

  const editingFormValues: CommunityWriteFormValues | undefined = editingPost
    ? {
      title: editingPost.title,
      content: editingPost.content
    }
    : undefined

  const editingRegionData: RegionFilterValues | undefined = editingPost
    ? {
      region: editingPost.region,
      dong: editingPost.dong,
      complexName: editingPost.complexName
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
      </main>

      <CommunityWriteModal
        isOpen={isWriteModalOpen}
        onClose={closeWriteModal}
        title={writeModalTitle}
        initialData={editingFormValues}
        initialRegionData={editingRegionData}
        submitLabel={editingPost ? '수정하기' : '등록하기'}
        showRegionFilter={activeTab === 'region'}
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
