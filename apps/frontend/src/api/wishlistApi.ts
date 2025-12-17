// apps/frontend/src/api/wishlistApi.ts
import axiosInstance from '@/lib/axios'

export interface WishlistItem {
  id: number
  listing_id: string
  memo?: string | null
  created_at: string
  updated_at: string
}

// 내 찜 목록 조회
export async function fetchWishlist(): Promise<WishlistItem[]> {
  const res = await axiosInstance.get('/api/users/wishlist/')
  return res.data as WishlistItem[]
}

// 찜 추가
export async function addWishlist(listingId: number | string): Promise<void> {
  await axiosInstance.post('/api/users/wishlist/', {
    listing_id: String(listingId),
  })
}

// 찜 삭제
export async function removeWishlist(listingId: number | string): Promise<void> {
  await axiosInstance.delete(`/api/users/wishlist/${listingId}/`)
}
