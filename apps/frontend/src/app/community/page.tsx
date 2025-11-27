/**
 * CommunityPage
 *
 * 커뮤니티 페이지 컨테이너
 *
 * - 탭 전환
 * - 게시글 리스트 및 상세/작성 모달 연동
 */

'use client'

import Button from '@/components/Button'
import CommunityCard from '@/components/CommunityCard'
import CommunityDetailModal from '@/components/CommunityDetailModal'
import CommunityTab from '@/components/CommunityTab'
import CommunityWriteModal from '@/components/CommunityWriteModal'
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

  const posts = activeTab === 'free' ? freePosts : regionPosts

  const handleWriteClick = () => {
    setEditingPost(null)
    openWriteModal()
  }

  const handleCardClick = (post: CommunityPost) => {
    openDetailModal(post)
  }

  const handleSubmitPost = (values: CommunityWriteFormValues, mode: 'free' | 'region') => {
    const targetMode: 'free' | 'region' = editingPost ? (editingPost.region ? 'region' : 'free') : mode
    const basePost = editingPost ?? null
    const payload: CommunityPost = {
      id: basePost?.id ?? Date.now().toString(),
      author: basePost?.author ?? { name: '현재 사용자' },
      title: values.title,
      content: values.content,
      createdAt: basePost?.createdAt ?? new Date(),
      likes: basePost?.likes ?? 0,
      comments: basePost?.comments ?? 0,
      region: targetMode === 'region' ? values.region : undefined,
      dong: targetMode === 'region' ? values.dong : undefined,
      complexName: targetMode === 'region' ? values.complexName : undefined,
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
        content: editingPost.content,
        region: editingPost.region,
        dong: editingPost.dong,
        complexName: editingPost.complexName
      }
    : undefined

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8">
        <CommunityTab activeTab={activeTab} onTabChange={setActiveTab} />

        <div className="flex justify-end mb-6">
          <Button variant="primary" onClick={handleWriteClick}>
            글쓰기
          </Button>
        </div>

        {posts.length === 0 ? (
          <div className="bg-white border border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-500">
            아직 게시글이 없습니다. 첫 번째 글의 주인공이 되어주세요!
          </div>
        ) : (
          <div className="space-y-4">
            {posts.map((post) => (
              <CommunityCard
                key={post.id}
                post={post}
                onClick={handleCardClick}
                onToggleLike={handleToggleLike}
              />
            ))}
          </div>
        )}
      </main>

      <CommunityWriteModal
        isOpen={isWriteModalOpen}
        onClose={closeWriteModal}
        activeTab={activeTab}
        initialData={editingFormValues}
        isEditing={Boolean(editingPost)}
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
