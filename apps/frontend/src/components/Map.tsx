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

import { useEffect, useRef } from 'react';

declare global {
    interface Window {
        kakao: any;
    }
}

export default function Map() {
    const mapContainer = useRef<HTMLDivElement>(null);

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
                console.log('지도 생성 완료');

                // 예시: 마커 추가
                const markerPosition = new window.kakao.maps.LatLng(37.5665, 126.9780);
                const marker = new window.kakao.maps.Marker({
                    position: markerPosition,
                });
                marker.setMap(map);
                console.log('마커 추가 완료');
            });
        }
    };

    return (
        <div
            ref={mapContainer}
            style={{
                width: '100%',
                height: '500px',
                backgroundColor: '#f0f0f0',
            }}
        />
    );
}
