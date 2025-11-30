import { create } from 'zustand'

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

interface CommunityState {
  activeTab: 'free' | 'region'
  freePosts: Post[]
  regionPosts: Post[]
  selectedPost: Post | null
  editingPost: Post | null
  isWriteModalOpen: boolean
  isDetailModalOpen: boolean

  setActiveTab: (tab: 'free' | 'region') => void
  addPost: (post: Post) => void
  updatePost: (post: Post) => void
  deletePost: (postId: string) => void
  toggleLike: (postId: string) => void
  setSelectedPost: (post: Post | null) => void
  setEditingPost: (post: Post | null) => void
  openWriteModal: () => void
  closeWriteModal: () => void
  openDetailModal: (post: Post) => void
  closeDetailModal: () => void
  getCurrentPosts: () => Post[]
}

export const useCommunityStore = create<CommunityState>((set, get) => ({
  activeTab: 'free',
  freePosts: [],
  regionPosts: [],
  selectedPost: null,
  editingPost: null,
  isWriteModalOpen: false,
  isDetailModalOpen: false,

  setActiveTab: (tab) => set({ activeTab: tab }),

  addPost: (post) => {
    const { activeTab } = get()
    if (activeTab === 'free') {
      set((state) => ({ freePosts: [post, ...state.freePosts] }))
    } else {
      set((state) => ({ regionPosts: [post, ...state.regionPosts] }))
    }
  },

  updatePost: (post) => {
    const { activeTab } = get()
    if (activeTab === 'free') {
      set((state) => ({
        freePosts: state.freePosts.map((p) => (p.id === post.id ? post : p))
      }))
    } else {
      set((state) => ({
        regionPosts: state.regionPosts.map((p) => (p.id === post.id ? post : p))
      }))
    }
  },

  deletePost: (postId) => {
    const { activeTab } = get()
    if (activeTab === 'free') {
      set((state) => ({
        freePosts: state.freePosts.filter((p) => p.id !== postId)
      }))
    } else {
      set((state) => ({
        regionPosts: state.regionPosts.filter((p) => p.id !== postId)
      }))
    }
  },

  toggleLike: (postId) => {
    const { activeTab, selectedPost } = get()
    const updatePosts = (posts: Post[]) =>
      posts.map((post) => {
        if (post.id === postId) {
          return {
            ...post,
            isLiked: !post.isLiked,
            likes: post.isLiked ? post.likes - 1 : post.likes + 1
          }
        }
        return post
      })

    if (activeTab === 'free') {
      set((state) => ({ freePosts: updatePosts(state.freePosts) }))
    } else {
      set((state) => ({ regionPosts: updatePosts(state.regionPosts) }))
    }

    if (selectedPost && selectedPost.id === postId) {
      set({
        selectedPost: {
          ...selectedPost,
          isLiked: !selectedPost.isLiked,
          likes: selectedPost.isLiked ? selectedPost.likes - 1 : selectedPost.likes + 1
        }
      })
    }
  },

  setSelectedPost: (post) => set({ selectedPost: post }),

  setEditingPost: (post) => set({ editingPost: post }),

  openWriteModal: () => set({ isWriteModalOpen: true }),

  closeWriteModal: () => set({ isWriteModalOpen: false, editingPost: null }),

  openDetailModal: (post) => set({ selectedPost: post, isDetailModalOpen: true }),

  closeDetailModal: () => set({ isDetailModalOpen: false, selectedPost: null }),

  getCurrentPosts: () => {
    const { activeTab, freePosts, regionPosts } = get()
    return activeTab === 'free' ? freePosts : regionPosts
  }
}))
