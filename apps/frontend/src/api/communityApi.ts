/**
 * Community API
 * 
 * 커뮤니티 게시글 및 댓글 관련 API
 */

import axiosInstance from '../lib/axios'

// 게시글 목록 조회
export async function fetchCommunityPosts(params?: {
    board?: 'free' | 'region'
    region?: string
    dong?: string
    complex_name?: string
}) {
    const queryParams = new URLSearchParams()
    if (params?.board) queryParams.append('board', params.board)
    if (params?.region) queryParams.append('region', params.region)
    if (params?.dong) queryParams.append('dong', params.dong)
    if (params?.complex_name) queryParams.append('complex_name', params.complex_name)

    const response = await axiosInstance.get(`/api/community/posts/?${queryParams}`)
    return response.data
}

// 게시글 상세 조회
export async function fetchCommunityPost(postId: string) {
    const response = await axiosInstance.get(`/api/community/posts/${postId}/`)
    return response.data
}

// 게시글 작성
export async function createCommunityPost(data: {
    title: string
    content: string
    board_type: 'free' | 'region'
    region?: string
    dong?: string
    complex_name?: string
}) {
    const response = await axiosInstance.post('/api/community/posts/', data)
    return response.data
}

// 게시글 수정
export async function updateCommunityPost(postId: string, data: {
    title?: string
    content?: string
}) {
    const response = await axiosInstance.patch(`/api/community/posts/${postId}/`, data)
    return response.data
}

// 게시글 삭제
export async function deleteCommunityPost(postId: string) {
    const response = await axiosInstance.delete(`/api/community/posts/${postId}/`)
    return response.data
}

// 게시글 좋아요
export async function toggleCommunityPostLike(postId: string, isLiked: boolean) {
    const method = isLiked ? 'delete' : 'post'
    const response = await axiosInstance[method](`/api/community/posts/${postId}/like/`)
    return response.data
}

// ==================== 댓글 API ====================

// 댓글 목록 조회
export async function fetchComments(postId: string) {
    const response = await axiosInstance.get(`/api/community/posts/${postId}/comments/`)
    return response.data
}

// 댓글 작성
export async function createComment(postId: string, content: string) {
    const response = await axiosInstance.post(`/api/community/posts/${postId}/comments/`, { content })
    return response.data
}

// 댓글 수정
export async function updateComment(postId: string, commentId: string, content: string) {
    const response = await axiosInstance.patch(`/api/community/comments/${commentId}/`, { content })
    return response.data
}

// 댓글 삭제
export async function deleteComment(postId: string, commentId: string) {
    const response = await axiosInstance.delete(`/api/community/comments/${commentId}/`)
    return response.data
}
