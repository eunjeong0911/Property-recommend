import axios from 'axios';
import { getSession } from 'next-auth/react';

// Axios 인스턴스 생성
const axiosInstance = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
});

// 요청 인터셉터: JWT 토큰 자동 추가
axiosInstance.interceptors.request.use(
    async (config) => {
        const session = await getSession();
        if (session?.user?.accessToken) {
            config.headers.Authorization = `Bearer ${session.user.accessToken}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// 응답 인터셉터: 401 에러 시 토큰 갱신 시도
axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // 401 에러이고, 재시도하지 않은 요청인 경우
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const session = await getSession();
                if (session?.user?.refreshToken) {
                    // 토큰 갱신 API 호출
                    const response = await axios.post(
                        `${process.env.NEXT_PUBLIC_API_URL}/api/users/token/refresh/`,
                        { refresh: session.user.refreshToken }
                    );

                    const newAccessToken = response.data.access;

                    // TODO: NextAuth session update 구현 필요
                    // 현재는 세션 업데이트 방법이 제한적이므로 로그아웃 처리

                    // 원래 요청 재시도
                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                    return axiosInstance(originalRequest);
                }
            } catch (refreshError) {
                // 토큰 갱신 실패 시 로그인 페이지로 리다이렉트
                console.error('Token refresh failed:', refreshError);
                if (typeof window !== 'undefined') {
                    window.location.href = '/login';
                }
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default axiosInstance;