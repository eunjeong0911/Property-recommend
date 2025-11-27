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
import { useRouter } from 'next/navigation';
import TemperatureList from './TemperatureList';

interface LandImageProps {
    id?: string;
    images?: string[];
    temperature?: number;
    price: string;
    onLike?: () => void;
    isLiked?: boolean;
}

export default function LandImage({
    id = '1',
    images = [
        'https://img.peterpanz.com/photo/20250115/16772468/67871b38ee314_origin.jpg',
        'https://img.peterpanz.com/photo/20250115/16772468/67871b3976aac_origin.jpg',
        'https://img.peterpanz.com/photo/20250115/16772468/67871b39eb65a_origin.jpg',
        'https://img.peterpanz.com/photo/20250115/16772468/67871b3a65cad_origin.jpg'
    ],
    price,
    onLike,
    isLiked = false
}: LandImageProps) {
    const router = useRouter();
    const [liked, setLiked] = useState(isLiked);
    const [isHovered, setIsHovered] = useState(false);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    const handleLike = (e: React.MouseEvent) => {
        e.stopPropagation();
        setLiked(!liked);
        onLike?.();
    };

    const handlePrevImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
    };

    const handleNextImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
    };

    const handleClick = () => {
        router.push(`/landDetail/${id}`);
    };

    return (
        <div className="relative cursor-pointer" onClick={handleClick}>
            <div
                className="relative w-full aspect-square bg-gray-200 rounded-lg overflow-hidden group"
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
            >
                <Image
                    src={images[currentImageIndex]}
                    alt="매물 이미지"
                    fill
                    className="object-cover"
                />

                {/* 이전/다음 버튼 */}
                {images.length > 1 && (
                    <>
                        <button
                            onClick={handlePrevImage}
                            className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full w-8 h-8 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10"
                        >
                            ‹
                        </button>
                        <button
                            onClick={handleNextImage}
                            className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full w-8 h-8 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10"
                        >
                            ›
                        </button>
                    </>
                )}

                {/* 이미지 인디케이터 */}
                {images.length > 1 && (
                    <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1 z-10">
                        {images.map((_, index) => (
                            <div
                                key={index}
                                className={`w-1.5 h-1.5 rounded-full transition-colors ${
                                    index === currentImageIndex ? 'bg-white' : 'bg-white/50'
                                }`}
                            />
                        ))}
                    </div>
                )}

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
