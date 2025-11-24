import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// API 함수들
export const api = {
  // 매물 관련
  listings: {
    search: (params: any) => apiClient.get('/api/listings/', { params }),
    getById: (id: string) => apiClient.get(`/api/listings/${id}/`),
  },
  
  // 추천 관련
  recommend: {
    getRecommendations: (userId: string) => apiClient.get(`/api/recommend/${userId}/`),
  },
  
  // RAG 챗봇
  chat: {
    sendMessage: (message: string) => apiClient.post('/api/chat/', { message }),
  },
}
