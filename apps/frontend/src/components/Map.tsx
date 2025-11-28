/**
 * Map 컴포넌트
 * 
 * 지도 인터페이스를 담당하는 컴포넌트
 * 
 * 주요 기능:
 * - 지도 표시
 * - 마커 표시
 * - 온도 표시
 * - 지도 확대/축소 및 이동
 */

'use client';

import { useEffect, useRef, useState } from 'react';

declare global {
    interface Window {
        kakao: any;
    }
}

export default function Map() {
    const mapContainer = useRef<HTMLDivElement>(null);
    const mapRef = useRef<any>(null);
    const markerRef = useRef<any>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        // window 객체 체크 (SSR 대응)
        if (typeof window === 'undefined') return;

        // 카카오맵 스크립트 동적 로드
        const script = document.createElement('script');
        script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${process.env.NEXT_PUBLIC_KAKAO_MAP_KEY}&libraries=services&autoload=false`;
        script.async = true;

        script.onload = () => {
            console.log('카카오 지도 스크립트 로드 완료');
            initializeMap();
        };

        script.onerror = () => {
            console.error('카카오 지도 스크립트 로드 실패');
        };

        document.head.appendChild(script);

        return () => {
            // 컴포넌트 언마운트 시 스크립트 제거
            document.head.removeChild(script);
        };
    }, []);

    const initializeMap = () => {
        if (!mapContainer.current) {
            console.log('mapContainer가 없음');
            return;
        }

        // window 체크 후 kakao.maps.load 사용
        if (typeof window !== 'undefined' && window.kakao && window.kakao.maps) {
            window.kakao.maps.load(() => {
                console.log('카카오 지도 API 로드 완료');

                const options = {
                    center: new window.kakao.maps.LatLng(37.5665, 126.9780), // 서울 중심 좌표
                    level: 3, // 지도 확대 레벨
                };

                const map = new window.kakao.maps.Map(mapContainer.current, options);
                mapRef.current = map;
                console.log('지도 생성 완료');

                // 예시: 마커 추가
                const markerPosition = new window.kakao.maps.LatLng(37.5665, 126.9780);
                const marker = new window.kakao.maps.Marker({
                    position: markerPosition,
                });
                marker.setMap(map);
                markerRef.current = marker;
                console.log('마커 추가 완료');
            });
        }
    };

    const moveToCurrentLocation = () => {
        if (!navigator.geolocation) {
            alert('현재 위치를 지원하지 않는 브라우저입니다.');
            return;
        }

        setIsLoading(true);

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                
                if (mapRef.current && markerRef.current && window.kakao) {
                    // 현재 위치로 지도 중심 이동
                    const moveLatLon = new window.kakao.maps.LatLng(latitude, longitude);
                    mapRef.current.setCenter(moveLatLon);
                    
                    // 커스텀 마커 이미지 생성
                    const imageSrc = '/icons/nowLocation.png';
                    const imageSize = new window.kakao.maps.Size(40, 40); // 마커 이미지 크기
                    const imageOption = { offset: new window.kakao.maps.Point(20, 40) }; // 마커 이미지의 기준점
                    
                    const markerImage = new window.kakao.maps.MarkerImage(
                        imageSrc,
                        imageSize,
                        imageOption
                    );
                    
                    // 기존 마커 제거
                    markerRef.current.setMap(null);
                    
                    // 새로운 커스텀 마커 생성
                    const newMarker = new window.kakao.maps.Marker({
                        position: moveLatLon,
                        image: markerImage
                    });
                    
                    newMarker.setMap(mapRef.current);
                    markerRef.current = newMarker;
                    
                    console.log('현재 위치로 이동:', latitude, longitude);
                }
                
                setIsLoading(false);
            },
            (error) => {
                console.error('위치 정보를 가져올 수 없습니다:', error);
                alert('위치 정보를 가져올 수 없습니다. 위치 권한을 확인해주세요.');
                setIsLoading(false);
            },
            {
                enableHighAccuracy: true, // 높은 정확도
                timeout: 5000, // 5초 타임아웃
                maximumAge: 0 // 캐시 사용 안함
            }
        );
    };

    return (
        <div style={{ position: 'relative' }}>
            <div
                ref={mapContainer}
                style={{
                    width: '100%',
                    height: '500px',
                    backgroundColor: '#f0f0f0',
                }}
            />
            
            {/* 현재 위치 버튼 */}
            <button
                onClick={moveToCurrentLocation}
                disabled={isLoading}
                className="absolute bottom-5 right-5 z-10 flex items-center gap-2 px-4 py-3 bg-white hover:bg-gray-50 disabled:bg-gray-100 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200"
                style={{
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                }}
            >
                <span className="text-xl">{isLoading ? '⏳' : '📍'}</span>
                <span className="font-semibold text-gray-700 text-sm">
                    {isLoading ? '찾는 중...' : '내 위치'}
                </span>
            </button>
        </div>
    );
}
