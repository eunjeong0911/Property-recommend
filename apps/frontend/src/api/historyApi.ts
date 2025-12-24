/**
 * 사용자 이력 관련 API
 * - 매물 조회 이력
 * - 검색 이력
 */

import { getSession } from 'next-auth/react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * 매물 조회 이력 저장
 * @param listingId 매물 ID
 * @param viewDuration 조회 시간(초)
 * @param scrollDepth 스크롤 깊이(%)
 */
export async function recordListingView(
    listingId: string,
    viewDuration?: number,
    scrollDepth?: number
): Promise<void> {
    try {
        // NextAuth 세션에서 토큰 가져오기
        const session = await getSession();

        console.log('[recordListingView] Called with:', { listingId, viewDuration, scrollDepth });
        console.log('[recordListingView] Session exists:', !!session);

        // 로그인하지 않은 경우 조용히 종료
        if (!session || !session.user) {
            console.warn('[recordListingView] No session found - user not logged in');
            return;
        }

        // NextAuth 세션에서 access token 추출 (session.user.accessToken에 저장됨)
        const token = (session.user as any).accessToken;

        console.log('[recordListingView] Token exists:', !!token);

        if (!token) {
            console.warn('[recordListingView] No access token in session');
            return;
        }

        const requestBody = {
            listing_id: listingId,
            view_duration: viewDuration,
            scroll_depth: scrollDepth,
        };

        console.log('[recordListingView] Sending request to:', `${API_BASE_URL}/api/users/history/view/`);
        console.log('[recordListingView] Request body:', requestBody);

        const response = await fetch(`${API_BASE_URL}/api/users/history/view/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(requestBody),
        });

        console.log('[recordListingView] Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[recordListingView] Failed to record:', response.status, errorText);
        } else {
            const data = await response.json();
            console.log('[recordListingView] Successfully recorded:', data);
        }
    } catch (error) {
        console.error('[recordListingView] Error:', error);
    }
}

/**
 * 검색 이력 저장
 * @param searchConditions 검색 조건
 * @param resultCount 검색 결과 개수
 */
export async function recordSearchHistory(
    searchConditions: Record<string, any>,
    resultCount: number
): Promise<void> {
    try {
        const session = await getSession();

        if (!session || !session.user) {
            return;
        }

        const token = (session.user as any).accessToken;

        if (!token) {
            return;
        }

        const response = await fetch(`${API_BASE_URL}/api/users/history/search/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({
                search_conditions: searchConditions,
                result_count: resultCount,
            }),
        });

        if (!response.ok) {
            console.warn('Failed to record search history:', response.statusText);
        }
    } catch (error) {
        console.warn('Error recording search history:', error);
    }
}
