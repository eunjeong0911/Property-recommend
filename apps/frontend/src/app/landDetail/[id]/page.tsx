/**
 * LandDetailPage
 * 
 * 매물 상세 페이지
 * 
 * 주요 구성:
 * - LandDetail 컴포넌트 (매물 상세 정보)
 * - Map 컴포넌트 (위치 및 주변 시설)
 * - MarkerInfo 컴포넌트 (주변 시설 정보 - Neo4j 연동)
 * - 커뮤니티 게시글 미리보기 (단지별)
 * - 비슷한 추천 매물 리스트
 */

'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Image from 'next/image';
import LandDetail from '@/components/LandDetail';
import Map from '@/components/Map';
import MarkerInfo from '@/components/MarkerInfo';
import LandList from '@/components/LandList';
import { fetchCommunityPosts } from '@/api/communityApi';

interface CommunityPost {
    id: string;
    title: string;
    content: string;
    author_name: string;
    created_at: string;
    likes_count: number;
    comments_count: number;
    region?: string;
    dong?: string;
    complex_name?: string;
}

export default function LandDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const [communityPosts, setCommunityPosts] = useState<CommunityPost[]>([]);
    const [loadingPosts, setLoadingPosts] = useState(true);
    const [activeMapCategories, setActiveMapCategories] = useState<Set<string>>(new Set());

    // 커뮤니티 게시글 로드
    useEffect(() => {
        const loadCommunityPosts = async () => {
            try {
                setLoadingPosts(true);
                // 지역 게시판에서 최근 게시글 가져오기
                const response = await fetchCommunityPosts({ board: 'region' });
                const posts = response.results || response || [];
                setCommunityPosts(posts.slice(0, 3)); // 최대 3개만 표시
            } catch (error) {
                console.error('Failed to fetch community posts:', error);
                setCommunityPosts([]);
            } finally {
                setLoadingPosts(false);
            }
        };

        loadCommunityPosts();
    }, []);

    // 시설 카테고리 클릭 핸들러
    const handleCategoryClick = (category: string, isActive: boolean) => {
        setActiveMapCategories(prev => {
            const newSet = new Set(prev);
            if (isActive) {
                newSet.add(category);
            } else {
                newSet.delete(category);
            }
            return newSet;
        });
        // TODO: 지도에 해당 카테고리 시설 마커 표시
        console.log(`카테고리 ${category} ${isActive ? '활성화' : '비활성화'}`);
    };

    // 날짜 포맷
    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const diffDays = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return '오늘';
        if (diffDays === 1) return '어제';
        if (diffDays < 7) return `${diffDays}일 전`;
        return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
    };

    return (
        <div className="max-w-7xl mx-auto px-4 py-8">
            {/* 매물 상세 정보 */}
            <LandDetail landId={id} />

            {/* 위치 및 주변 시설 정보 */}
            <div className="mt-8">
                <h3 className="text-xl font-bold mb-4 text-slate-800">위치 및 주변 시설</h3>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                        <Map landId={id} />
                    </div>
                    <div className="lg:col-span-1">
                        <MarkerInfo landId={id} onCategoryClick={handleCategoryClick} />
                    </div>
                </div>
            </div>

            {/* 커뮤니티 게시글 미리보기 */}
            <div className="mt-8">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-slate-800">행정동 커뮤니티 게시글</h3>
                    <a
                        href="/community"
                        className="text-sm text-purple-600 hover:text-purple-800 font-medium transition-colors"
                    >
                        더보기 →
                    </a>
                </div>

                {loadingPosts ? (
                    <div className="flex justify-center items-center h-32">
                        <div className="w-6 h-6 border-3 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                ) : communityPosts.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {communityPosts.map((post) => (
                            <a
                                key={post.id}
                                href={`/community?post=${post.id}`}
                                className="block rounded-2xl border border-gray-200 bg-white shadow-sm p-4 hover:shadow-md transition-all hover:border-gray-300"
                            >
                                {/* 지역 태그 */}
                                <div className="flex flex-wrap gap-1 mb-2">
                                    {post.region && (
                                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                                            {post.region}
                                        </span>
                                    )}
                                    {post.dong && (
                                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                                            {post.dong}
                                        </span>
                                    )}
                                </div>

                                {/* 제목 */}
                                <h4 className="font-semibold text-slate-800 mb-1 line-clamp-1">
                                    {post.title}
                                </h4>

                                {/* 내용 미리보기 */}
                                <p className="text-sm text-slate-600 line-clamp-2 mb-3">
                                    {post.content}
                                </p>

                                {/* 하단 정보 */}
                                <div className="flex items-center justify-between text-xs text-slate-500">
                                    <span>{post.author_name}</span>
                                    <div className="flex items-center gap-3">
                                        <span className="flex items-center gap-1">
                                            ❤️ {post.likes_count}
                                        </span>
                                        <span className="flex items-center gap-1">
                                            💬 {post.comments_count}
                                        </span>
                                        <span>{formatDate(post.created_at)}</span>
                                    </div>
                                </div>
                            </a>
                        ))}
                    </div>
                ) : (
                    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-8 text-center">
                        <p className="text-slate-500">아직 등록된 게시글이 없습니다.</p>
                        <a
                            href="/community"
                            className="inline-block mt-2 text-purple-600 hover:text-purple-800 font-medium"
                        >
                            커뮤니티 바로가기 →
                        </a>
                    </div>
                )}
            </div>

            {/* 비슷한 추천 매물 */}
            <div className="mt-8">
                <h3 className="text-xl font-bold mb-4 text-slate-800">비슷한 추천 매물</h3>
                <LandList />
            </div>
        </div>
    );
}
