/**
 * LandImage 컴포넌트
 * 
 * 매물 사진을 표시하는 컴포넌트
 * 
 * 주요 기능:
 * - 매물 이미지 표시
 * - 이미지 슬라이더
 * - 찜하기 버튼
 */

'use client';

import { useState } from 'react';
import Image from 'next/image';
import TemperatureList from './TemperatureList';

interface LandImageProps {
    image?: string;
    temperature?: number;
    price: string;
    onLike?: () => void;
    isLiked?: boolean;
}

export default function LandImage({
    image = 'https://img.peterpanz.com/photo/20250115/16772468/67871b38ee314_origin.jpg',
    price,
    onLike,
    isLiked = false
}: LandImageProps) {
    const [liked, setLiked] = useState(isLiked);
    const [isHovered, setIsHovered] = useState(false);

    const handleLike = () => {
        setLiked(!liked);
        onLike?.();
    };

    return (
        <div className="relative">
            <div
                className="relative w-full aspect-square bg-gray-200 rounded-lg overflow-hidden"
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
            >
                <Image
                    src={image}
                    alt="매물 이미지"
                    fill
                    className="object-cover"
                />

                {/* 찜하기 버튼 */}
                <button
                    onClick={handleLike}
                    className="absolute top-3 right-3 hover:scale-110 transition-transform z-10"
                >
                    <Image
                        src={liked ? '/icons/whish_on.png' : '/icons/whish_off.png'}
                        alt="찜하기"
                        width={40}
                        height={40}
                    />
                </button>

            </div>

            {/* 온도 정보 - hover 시 표시 (이미지 왼쪽에 겹치게) */}
            {isHovered && (
                <div className="absolute left-0 top-8 -translate-x-[calc(100%-30px)] z-20 w-64">
                    <TemperatureList />
                </div>
            )}

            {/* 가격 정보 */}
            <div className="mt-3 text-center">
                <p className="text-lg font-bold text-gray-800">{price}</p>
            </div>
        </div>
    );
}
