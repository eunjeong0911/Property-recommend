/**
 * LandDetail 컴포넌트
 * 
 * 매물 상세정보를 표시하는 컴포넌트
 * 
 * 주요 기능:
 * - 매물 기본 정보 (월세, 보증금, 관리비, 공급면적, 전용면적, 방/화장실 수, 주거 형태 등)
 * - 부동산 정보 (연락처, 전화번호, 주소)
 * - 상세내용 텍스트
 * 
 * - LandImage import
 */

'use client';

import { useState } from 'react';
import Image from 'next/image';
import Temperature from './Temperature';

interface LandDetailProps {
    landId: string;
}

export default function LandDetail({ landId }: LandDetailProps) {
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [liked, setLiked] = useState(false);

    // Mock data
    const images = [
        'https://img.peterpanz.com/photo/20250115/16772468/67871b38ee314_origin.jpg',
        'https://img.peterpanz.com/photo/20250115/16772468/67871b3976aac_origin.jpg',
        'https://img.peterpanz.com/photo/20250115/16772468/67871b39eb65a_origin.jpg',
        'https://img.peterpanz.com/photo/20250115/16772468/67871b3a65cad_origin.jpg'
    ];

    const handlePrevImage = () => {
        setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
    };

    const handleNextImage = () => {
        setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
    };

    return (
        <div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                {/* 왼쪽: 이미지 */}
                <div>
                    <div className="relative aspect-[4/3] bg-gray-200 rounded-lg overflow-hidden group">
                        <Image
                            src={images[currentImageIndex]}
                            alt="매물 이미지"
                            fill
                            className="object-cover"
                        />

                        {/* 찜하기 버튼 */}
                        <button
                            onClick={() => setLiked(!liked)}
                            className="absolute top-4 right-4 hover:scale-110 transition-transform z-10"
                        >
                            <Image
                                src={liked ? '/icons/whish_on.png' : '/icons/whish_off.png'}
                                alt="찜하기"
                                width={48}
                                height={48}
                            />
                        </button>

                        {/* 이전/다음 버튼 */}
                        <button
                            onClick={handlePrevImage}
                            className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full w-10 h-10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10 text-xl"
                        >
                            ‹
                        </button>
                        <button
                            onClick={handleNextImage}
                            className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full w-10 h-10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10 text-xl"
                        >
                            ›
                        </button>

                        {/* 이미지 카운터 */}
                        <div className="absolute bottom-4 right-4 bg-black/60 text-white px-3 py-1 rounded-full text-sm">
                            {currentImageIndex + 1} / {images.length}
                        </div>
                    </div>

                    {/* 부동산 정보 */}
                    <div className="mt-6 bg-white border border-gray-200 rounded-lg p-6">
                        <h3 className="text-lg font-bold mb-4">부동산 정보</h3>
                        
                        {/* 온도 바 */}
                        <div className="mb-6">
                            <Temperature label="부동산 온도" value={0.7} />
                        </div>

                        <div className="space-y-3">
                            <div className="flex items-center gap-2">
                                <span className="w-20 text-gray-500 text-sm">중개사무소</span>
                                <p className="font-medium">주식회사부동산공인중개사사무소</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-20 text-gray-500 text-sm">전화번호</span>
                                <p className="font-medium">02-867-1467</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-20 text-gray-500 text-sm">대표자</span>
                                <p className="font-medium">박유홍</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-20 text-gray-500 text-sm">주소</span>
                                <p className="font-medium">서울특별시 금천구 가산동 145-21 D동 101호</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 오른쪽: 정보 */}
                <div className="flex flex-col">
                    {/* 가격 정보 */}
                    <div className="mb-6">
                        <h1 className="text-3xl font-bold">월세 3,000 / 43</h1>
                    </div>

                    {/* 매물 정보 */}
                    <div className="bg-white border border-gray-200 rounded-lg p-6 flex-1">
                        <h3 className="text-lg font-bold mb-4">매물 상세 정보</h3>
                        <div className="space-y-3">
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">매물번호</span>
                                <p className="font-medium">17278443</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">건축물 용도</span>
                                <p className="font-medium">공동주택</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">공급면적</span>
                                <p className="font-medium">20.63m2 (6.24평)</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">전용면적</span>
                                <p className="font-medium">25.98m2 (7.86평)</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">층수</span>
                                <p className="font-medium">13층 / 총 15층</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">방향</span>
                                <p className="font-medium">남향</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">방/욕실 수</span>
                                <p className="font-medium">방 1개 / 욕실 1개</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">주차</span>
                                <p className="font-medium">가능 (1대)</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">입주가능일</span>
                                <p className="font-medium">즉시입주</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">관리비</span>
                                <p className="font-medium">10만원</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">난방방식</span>
                                <p className="font-medium">개별난방</p>
                            </div>
                            <div className="flex items-center" style={{ gap: '100px' }}>
                                <span className="text-gray-500 text-sm w-32">엘리베이터</span>
                                <p className="font-medium">있음</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 하단: 상세내용 (전체 너비) */}
            <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4">상세내용</h3>
                <p className="text-gray-700 whitespace-pre-line leading-relaxed">
                    안녕을 드려 전신으로 중개하는 대용부동산공인중개사사무소 입니다!!
                    해당 매물은 직접 확인된 실매물입니다
                    
                    저가 실고 싶은 집들로 엄선해서 공고합니다
                    저가 같이 담아서 오래오래 확인할 수 연관된 매물만 출고합니다
                    허위매물 없습니다
                    
                    24시간 대기중!! 편하게 전화나 문자주세요!!
                    편하게 연락주시면 그쪽님의 니즈에 맞는 곳으로 최선을 다해 찾아드릴게요♥
                    
                    ✅ 매물 특징
                    - 깨끗하게 리모델링된 원룸
                    - 풀옵션 (냉장고, 세탁기, 에어컨, 침대, 책상 등)
                    - 보안이 철저한 건물 (CCTV, 출입통제시스템)
                    - 편의점, 마트 도보 5분 거리
                    - 지하철역 도보 10분 거리
                    
                    ✅ 주변 환경
                    - 대형마트: 이마트 도보 15분
                    - 병원: 종합병원 차량 10분
                    - 학교: 초/중/고등학교 인근
                    - 공원: 근린공원 도보 5분
                    
                    ✅ 교통
                    - 지하철 1호선 가산디지털단지역 도보 10분
                    - 버스정류장 도보 3분 (간선, 지선 다수)
                    - 주요 도로 접근성 우수
                    
                    문의 주시면 성심성의껏 상담해드리겠습니다!
                    감사합니다 😊
                </p>
            </div>

        </div>
    );
}
