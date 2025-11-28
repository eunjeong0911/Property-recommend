/**
 * LandDetailPage
 * 
 * 매물 상세 페이지
 */

'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import LandDetail from '@/components/LandDetail';
import Map from '@/components/Map';
import MarkerInfo from '@/components/MarkerInfo';
import CommunityCard from '@/components/CommunityCard';
import CommunityDetailModal from '@/components/CommunityDetailModal';
import LandList from '@/components/LandList';

export default function LandDetailPage() {
    const params = useParams();
    const id = params.id as string;
    
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [communityPost, setCommunityPost] = useState({
        id: '1',
        author: { name: '홍길동' },
        title: '이 동네 살기 어떤가요?',
        content: '이사를 고민중인데 이 동네 분위기가 궁금합니다. 살기 좋은가요?',
        createdAt: new Date(Date.now() - 1000 * 60 * 30),
        likes: 12,
        comments: 5,
        region: '금천구',
        dong: '가산동',
        isOwner: false,
        isLiked: false
    });

    return (
        <div className="max-w-7xl mx-auto px-4 py-8">
            <LandDetail landId={id} />
            
            {/* 지도 및 주변 시설 정보 */}
            <div className="mt-8">
                <h3 className="text-xl font-bold mb-4">위치 및 주변 시설</h3>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                        <Map />
                    </div>
                    <div className="lg:col-span-1">
                        <MarkerInfo />
                    </div>
                </div>
            </div>

            {/* 커뮤니티 게시글 */}
            <div className="mt-8">
                <h3 className="text-xl font-bold mb-4">커뮤니티 게시글</h3>
                <CommunityCard
                    post={communityPost}
                    onClick={() => setIsModalOpen(true)}
                    onToggleLike={() => {
                        setCommunityPost(prev => ({
                            ...prev,
                            isLiked: !prev.isLiked,
                            likes: prev.isLiked ? prev.likes - 1 : prev.likes + 1
                        }));
                    }}
                />
            </div>

            {/* 커뮤니티 상세 모달 */}
            <CommunityDetailModal
                post={communityPost}
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onToggleLike={() => {
                    setCommunityPost(prev => ({
                        ...prev,
                        isLiked: !prev.isLiked,
                        likes: prev.isLiked ? prev.likes - 1 : prev.likes + 1
                    }));
                }}
            />

            {/* 비슷한 추천 매물 */}
            <div className="mt-8">
                <h3 className="text-xl font-bold mb-4">비슷한 추천 매물</h3>
                <LandList />
            </div>
        </div>
    );
}
