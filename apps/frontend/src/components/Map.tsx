/**
 * Map 컴포넌트
 * 
 * 지도 인터페이스를 담당하는 컴포넌트
 * 
 * 주요 기능:
 * - 지도 표시
 * - 마커 표시
 * - 지도 확대/축소 및 이동
 * - 주변 시설 마커 표시 (Neo4j 연동)
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { fetchLandLocations, LandLocation, fetchFacilityLocations, FacilityLocation } from '../api/landApi';
import { seoulDistricts, getTemperatureColor } from '../mapdata/seoulDistricts';

declare global {
    interface Window {
        kakao: any;
    }
}

interface MapProps {
    landId?: string; // 매물 상세 페이지에서 전달되는 매물 ID
    activeCategories?: Set<string>; // 활성화된 시설 카테고리
}

export default function Map({ landId, activeCategories }: MapProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const mapRef = useRef<any>(null);
    const markersRef = useRef<Array<{ marker: any; overlay: any; overlayState?: { isOpen: boolean; overlay: any } }>>([]);
    const facilityMarkersRef = useRef<any[]>([]); // 시설 마커 저장
    const polygonsRef = useRef<any[]>([]);
    const overlaysRef = useRef<any[]>([]);
    const [locations, setLocations] = useState<LandLocation[]>([]);
    const [currentLand, setCurrentLand] = useState<LandLocation | null>(null);

    useEffect(() => {
        // window 객체 체크 (SSR 대응)
        if (typeof window === 'undefined') return;

        // 상세 페이지: currentLand가 로드될 때까지 대기
        // 메인 페이지: 바로 지도 초기화
        if (landId && !currentLand) return;

        // 이미 스크립트가 로드되어 있는지 확인
        const existingScript = document.querySelector('script[src*="dapi.kakao.com"]');

        if (existingScript) {
            // 이미 로드된 경우 바로 초기화
            if (window.kakao && window.kakao.maps) {
                initializeMap();
            } else {
                // 스크립트는 있지만 아직 로드 안된 경우 대기
                existingScript.addEventListener('load', initializeMap);
            }
            return;
        }

        // 카카오맵 스크립트 동적 로드
        const script = document.createElement('script');
        script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${process.env.NEXT_PUBLIC_KAKAO_MAP_KEY}&libraries=services&autoload=false`;
        script.async = true;
        script.defer = true; // defer 추가로 성능 개선

        script.onload = () => {
            console.log('카카오 지도 스크립트 로드 완료');
            initializeMap();
        };

        script.onerror = () => {
            console.error('카카오 지도 스크립트 로드 실패');
        };

        document.head.appendChild(script);

        return () => {
            // 컴포넌트 언마운트 시에도 스크립트는 유지 (재사용을 위해)
            // document.head.removeChild(script);
        };
    }, [currentLand]);

    // 매물 위치 데이터 로드 (상세 페이지에서만)
    useEffect(() => {
        const loadLocations = async () => {
            // 상세 페이지에서만 매물 위치 로드
            if (!landId) {
                // 메인 페이지: 마커 없이 지도만 표시
                setCurrentLand(null);
                setLocations([]);
                return;
            }

            try {
                const data = await fetchLandLocations({ land_id: landId });
                if (data.length > 0) {
                    setCurrentLand(data[0]);
                    setLocations(data);
                    console.log('매물 위치 로드 완료:', data[0]);
                } else {
                    console.warn('매물 위치 정보를 찾을 수 없습니다:', landId);
                }
            } catch (error) {
                console.error('매물 위치 로드 실패:', error);
            }
        };

        loadLocations();
    }, [landId]);

    const initializeMap = () => {
        if (!mapContainer.current) {
            console.log('mapContainer가 없음');
            return;
        }

        // window 체크 후 kakao.maps.load 사용
        if (typeof window !== 'undefined' && window.kakao && window.kakao.maps) {
            window.kakao.maps.load(() => {
                console.log('카카오 지도 API 로드 완료');

                // 매물 상세 페이지인 경우 해당 매물 위치 중심, 아니면 서울 중심
                // 메인 페이지: 지도 중심 조정
                const centerLat = currentLand?.latitude || (landId ? 37.5665 : 37.5715);
                const centerLng = currentLand?.longitude || (landId ? 126.9780 : 126.9705);
                const zoomLevel = landId ? 3 : 9; // 상세 페이지는 더 확대, 메인은 서울 전역

                const options = {
                    center: new window.kakao.maps.LatLng(centerLat, centerLng),
                    level: zoomLevel,
                };

                const map = new window.kakao.maps.Map(mapContainer.current, options);
                mapRef.current = map;
                console.log('지도 생성 완료');

                // 상세 페이지에서 매물 마커 즉시 생성
                if (landId && currentLand) {
                    console.log('📍 매물 마커 생성 시작:', currentLand);
                    const position = new window.kakao.maps.LatLng(currentLand.latitude, currentLand.longitude);

                    // 커스텀 마커 이미지 (빨간색 핀)
                    const markerContent = document.createElement('div');
                    markerContent.innerHTML = `
                        <div style="
                            position: relative;
                            width: 40px;
                            height: 50px;
                            cursor: pointer;
                        ">
                            <svg viewBox="0 0 24 24" width="40" height="40" fill="#dc2626" stroke="#fff" stroke-width="1">
                                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                            </svg>
                            <div style="
                                position: absolute;
                                bottom: -8px;
                                left: 50%;
                                transform: translateX(-50%);
                                background: #dc2626;
                                color: white;
                                padding: 2px 6px;
                                border-radius: 4px;
                                font-size: 10px;
                                font-weight: bold;
                                white-space: nowrap;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                            ">매물</div>
                        </div>
                    `;

                    const customOverlay = new window.kakao.maps.CustomOverlay({
                        position: position,
                        content: markerContent,
                        yAnchor: 1.2,
                        xAnchor: 0.5,
                        zIndex: 100
                    });

                    customOverlay.setMap(map);

                    // 기존 마커 배열에 저장
                    markersRef.current.push({
                        marker: customOverlay,
                        overlay: null,
                        overlayState: undefined
                    });

                    console.log('✅ 매물 마커 생성 완료');
                }

                // 메인 페이지에서만 구별 폴리곤 표시
                if (!landId) {
                    // 지도 이동/확대 제한 (서울 전역 고정)
                    map.setZoomable(false);
                    map.setDraggable(false);

                    drawDistrictPolygons(map);
                }
            });
        }
    };

    // 서울시 구별 폴리곤 그리기
    const drawDistrictPolygons = (map: any) => {
        // 기존 폴리곤 제거
        polygonsRef.current.forEach(polygon => polygon.setMap(null));
        overlaysRef.current.forEach(overlay => overlay.setMap(null));
        polygonsRef.current = [];
        overlaysRef.current = [];

        seoulDistricts.forEach((district) => {
            const path = district.path.map(
                coord => new window.kakao.maps.LatLng(coord.lat, coord.lng)
            );

            const color = getTemperatureColor(district.temperature);

            // 폴리곤 생성
            const polygon = new window.kakao.maps.Polygon({
                path: path,
                strokeWeight: 2,
                strokeColor: color,
                strokeOpacity: 0.8,
                fillColor: color,
                fillOpacity: 0.4,
            });

            polygon.setMap(map);
            polygonsRef.current.push(polygon);

            // 구 이름만 표시 (마커 없이 텍스트만)
            const content = document.createElement('div');
            content.style.cssText = `
                font-size: 12px;
                font-weight: 700;
                color: #1f2937;
                text-shadow: 1px 1px 2px white, -1px -1px 2px white, 1px -1px 2px white, -1px 1px 2px white;
                pointer-events: none;
            `;
            content.textContent = district.name;

            const overlay = new window.kakao.maps.CustomOverlay({
                position: new window.kakao.maps.LatLng(district.center.lat, district.center.lng),
                content: content,
                yAnchor: 0.5,
                xAnchor: 0.5,
            });

            overlay.setMap(map);
            overlaysRef.current.push(overlay);

            // 폴리곤 호버 이벤트
            window.kakao.maps.event.addListener(polygon, 'mouseover', () => {
                polygon.setOptions({
                    fillOpacity: 0.7,
                    strokeWeight: 3,
                });
            });

            window.kakao.maps.event.addListener(polygon, 'mouseout', () => {
                polygon.setOptions({
                    fillOpacity: 0.4,
                    strokeWeight: 2,
                });
            });
        });

        console.log('서울시 구별 폴리곤 표시 완료');
    };

    // 매물 마커 표시 (상세 페이지에서만)
    useEffect(() => {
        console.log('🔍 매물 마커 useEffect 실행:', {
            hasMap: !!mapRef.current,
            hasKakao: !!window.kakao,
            landId,
            locationsLength: locations.length
        });
        if (!mapRef.current || !window.kakao || !landId || locations.length === 0) return;

        // 기존 매물 마커 제거
        markersRef.current.forEach(item => {
            if (item.marker) item.marker.setMap(null);
            if (item.overlay) item.overlay.setMap(null);
        });
        markersRef.current = [];

        // CSS 애니메이션 추가 (한 번만)
        if (!document.getElementById('overlay-animation-style')) {
            const style = document.createElement('style');
            style.id = 'overlay-animation-style';
            style.textContent = `
                @keyframes popUp {
                    0% {
                        opacity: 0;
                        transform: scale(0.3);
                    }
                    50% {
                        transform: scale(1.05);
                    }
                    100% {
                        opacity: 1;
                        transform: scale(1);
                    }
                }
                .overlay-close-btn:hover {
                    transform: scale(1.15) rotate(90deg);
                    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                }
                .overlay-wrapper {
                    filter: drop-shadow(0 12px 24px rgba(0,0,0,0.2));
                }
            `;
            document.head.appendChild(style);
        }

        // 새 매물 마커 추가
        locations.forEach((location) => {
            const position = new window.kakao.maps.LatLng(location.latitude, location.longitude);

            // 마커 생성
            const marker = new window.kakao.maps.Marker({
                position: position,
                title: location.address,
            });

            marker.setMap(mapRef.current);

            // 상세 페이지에서는 오버레이를 생성하지 않음 (마커만 표시)
            const isDetailPage = !!landId;

            if (isDetailPage) {
                // 상세 페이지: 마커만 저장하고 오버레이는 생성하지 않음
                markersRef.current.push({
                    marker,
                    overlay: null,
                    overlayState: undefined
                });
                return; // 오버레이 생성 로직 건너뛰기
            }

            // 메인 페이지: 오버레이 생성 (기존 로직)
            // CSS 애니메이션 추가 (한 번만)
            if (!document.getElementById('overlay-animation-style')) {
                const style = document.createElement('style');
                style.id = 'overlay-animation-style';
                style.textContent = `
                    @keyframes popUp {
                        0% {
                            opacity: 0;
                            transform: scale(0.3);
                        }
                        50% {
                            transform: scale(1.05);
                        }
                        100% {
                            opacity: 1;
                            transform: scale(1);
                        }
                    }
                    .overlay-close-btn:hover {
                        transform: scale(1.15) rotate(90deg);
                        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                    }
                    .overlay-wrapper {
                        filter: drop-shadow(0 12px 24px rgba(0,0,0,0.2));
                    }
                `;
                document.head.appendChild(style);
            }

            // 오버레이 컨텐츠 생성
            const overlayContent = document.createElement('div');
            overlayContent.className = 'overlay-wrapper';
            overlayContent.style.cssText = `
                position: relative;
                background: linear-gradient(to bottom, #ffffff 0%, #f8fafc 100%);
                border-radius: 16px;
                padding: 14px;
                width: 220px;
                max-width: 300px;
                animation: popUp 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
                border: 2px solid transparent;
                background-clip: padding-box;
                transform-origin: left center;
                word-wrap: break-word;
                overflow-wrap: break-word;
                box-sizing: border-box;
            `;

            // 그라데이션 테두리 효과
            const borderGradient = document.createElement('div');
            borderGradient.style.cssText = `
                position: absolute;
                inset: -2px;
                border-radius: 16px;
                padding: 2px;
                background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899);
                -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                -webkit-mask-composite: xor;
                mask-composite: exclude;
                pointer-events: none;
                z-index: -1;
            `;
            overlayContent.appendChild(borderGradient);

            const contentHTML = `
                <div style="position: relative; cursor: pointer;" id="overlay-${location.id}">
                    <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 8px 10px; border-radius: 10px 10px 0 0; margin: -14px -14px 8px -14px; box-shadow: 0 3px 8px rgba(59, 130, 246, 0.3);">
                        <div style="font-weight: 700; font-size: 14px; letter-spacing: -0.2px;">${location.price || '매물'}</div>
                    </div>
                    
                    <div style="font-size: 11px; color: #1f2937; margin-bottom: 8px; line-height: 1.4; font-weight: 600; display: flex; align-items: start; gap: 4px; word-break: keep-all; overflow-wrap: break-word;">
                        <span style="font-size: 13px;">📍</span>
                        <span style="flex: 1; min-width: 0;">${location.address}</span>
                    </div>
                    
                    <div style="display: flex; gap: 4px; margin-bottom: 8px; flex-wrap: wrap;">
                        <span style="background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%); color: #0369a1; padding: 4px 8px; border-radius: 6px; font-size: 10px; font-weight: 700; border: 1px solid #7dd3fc;">${location.building_type || ''}</span>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 6px; border-radius: 6px; font-size: 11px; color: #0369a1; text-align: center; font-weight: 700; border: 1.5px solid #bae6fd; display: flex; align-items: center; justify-content: center; gap: 4px;">
                        <span style="font-size: 13px;">📐</span>
                        <span>${location.area || '면적 정보 없음'}</span>
                    </div>
                    
                    <div style="font-size: 10px; color: #3b82f6; padding-top: 6px; margin-top: 6px; border-top: 1.5px dashed #bae6fd; text-align: center; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 4px;">
                        <span>상세보기</span>
                        <span style="font-size: 12px;">→</span>
                    </div>
                </div>
            `;

            overlayContent.innerHTML = contentHTML;

            // 커스텀 오버레이 생성 - 마커 오른쪽에 표시
            const customOverlay = new window.kakao.maps.CustomOverlay({
                position: position,
                content: overlayContent,
                yAnchor: 0.5,
                xAnchor: -0.2,
                zIndex: 100
            });

            // 오버레이 상태 관리 객체
            const overlayState = {
                isOpen: false,
                overlay: customOverlay
            };

            // 마커 클릭 이벤트 - 상태 객체 참조
            const markerClickHandler = () => {
                console.log('🔵 마커 클릭됨:', location.id, '현재 상태:', overlayState.isOpen);

                // 다른 모든 오버레이 닫기
                markersRef.current.forEach(item => {
                    if (item.overlay !== customOverlay && item.overlay && item.overlayState) {
                        item.overlay.setMap(null);
                        item.overlayState.isOpen = false;
                    }
                });

                if (overlayState.isOpen) {
                    // 이미 열려있으면 오버레이 닫기
                    customOverlay.setMap(null);
                    overlayState.isOpen = false;
                    console.log('❌ 오버레이 닫힘');
                } else {
                    // 오버레이 열기
                    customOverlay.setMap(mapRef.current);
                    overlayState.isOpen = true;
                    console.log('✅ 오버레이 열림');

                    // 오버레이 클릭 시 상세 페이지로 이동
                    setTimeout(() => {
                        const overlayElement = document.getElementById(`overlay-${location.id}`);
                        if (overlayElement) {
                            overlayElement.onclick = () => {
                                console.log('🔗 오버레이 클릭 - 상세 페이지로 이동:', location.id);
                                window.location.href = `/landDetail/${location.id}`;
                            };
                        }
                    }, 50);
                }
            };

            // 카카오맵 마커 클릭 이벤트 등록
            try {
                window.kakao.maps.event.addListener(marker, 'click', markerClickHandler);
                console.log('✅ 마커 클릭 이벤트 등록 완료:', location.id);
            } catch (error) {
                console.error('❌ 마커 클릭 이벤트 등록 실패:', error);
            }

            // 마커와 오버레이 저장 (상태 객체 포함)
            markersRef.current.push({
                marker,
                overlay: customOverlay,
                overlayState: overlayState
            });
        });

        console.log(`매물 마커 ${locations.length}개 표시 완료`);
    }, [locations, landId]);

    // 시설 마커 표시 (activeCategories 변경 시)
    useEffect(() => {
        if (!mapRef.current || !window.kakao || !landId || !activeCategories) {
            console.log('시설 마커 표시 조건 미충족:', {
                hasMap: !!mapRef.current,
                hasKakao: !!window.kakao,
                landId,
                hasActiveCategories: !!activeCategories
            });
            return;
        }

        // 기존 시설 마커 제거
        facilityMarkersRef.current.forEach(marker => marker.setMap(null));
        facilityMarkersRef.current = [];

        // 활성화된 카테고리가 없으면 종료
        if (activeCategories.size === 0) {
            console.log('활성화된 카테고리 없음');
            return;
        }

        console.log('활성화된 카테고리:', Array.from(activeCategories));

        // 카테고리별 아이콘 매핑
        const categoryIcons: Record<string, string> = {
            'transportation': '/assets/map_pin/bus.png',
            'medical': '/assets/map_pin/medical_facilities.png',
            'convenience': '/assets/map_pin/convenience.png',
            'safety': '/assets/map_pin/cctv.png'
        };

        // 카테고리별 색상 및 이모지 매핑
        const categoryStyles: Record<string, { color: string; bgColor: string; emoji: string; label: string }> = {
            'transportation': { color: '#2563eb', bgColor: '#dbeafe', emoji: '🚇', label: '교통' },
            'medical': { color: '#dc2626', bgColor: '#fee2e2', emoji: '🏥', label: '의료' },
            'convenience': { color: '#16a34a', bgColor: '#dcfce7', emoji: '🏪', label: '편의' },
            'safety': { color: '#7c3aed', bgColor: '#ede9fe', emoji: '📹', label: '안전' }
        };

        // 현재 열린 오버레이 추적 (클로저로 관리)
        let currentOpenOverlay: any = null;

        // 각 활성화된 카테고리에 대해 시설 위치 가져오기
        activeCategories.forEach(async (category) => {
            try {
                console.log(`${category} 시설 데이터 요청 중...`);
                const response = await fetchFacilityLocations(
                    landId,
                    category as 'transportation' | 'medical' | 'convenience' | 'safety'
                );

                console.log(`${category} 시설 데이터 응답:`, response);

                if (response.facilities.length === 0) {
                    console.warn(`${category} 시설이 없습니다.`);
                    return;
                }

                const style = categoryStyles[category] || categoryStyles['convenience'];

                // 시설 마커 생성
                response.facilities.forEach((facility: FacilityLocation) => {
                    const position = new window.kakao.maps.LatLng(facility.latitude, facility.longitude);

                    // 커스텀 마커 이미지 생성
                    const iconSrc = categoryIcons[category];
                    const imageSize = new window.kakao.maps.Size(32, 32);
                    const markerImage = new window.kakao.maps.MarkerImage(iconSrc, imageSize);

                    // 마커 생성
                    const marker = new window.kakao.maps.Marker({
                        position: position,
                        image: markerImage,
                        title: facility.name
                    });

                    marker.setMap(mapRef.current);
                    facilityMarkersRef.current.push(marker);

                    // 커스텀 오버레이 콘텐츠 (더 예쁜 디자인)
                    const overlayContent = document.createElement('div');
                    overlayContent.innerHTML = `
                        <div style="
                            position: relative;
                            background: white;
                            border-radius: 12px;
                            padding: 12px 14px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                            border: 2px solid ${style.color};
                            min-width: 120px;
                            max-width: 200px;
                            animation: fadeIn 0.2s ease-out;
                        ">
                            <style>
                                @keyframes fadeIn {
                                    from { opacity: 0; transform: translateY(-5px); }
                                    to { opacity: 1; transform: translateY(0); }
                                }
                            </style>
                            
                            <!-- 카테고리 태그 -->
                            <div style="
                                display: inline-flex;
                                align-items: center;
                                gap: 4px;
                                background: ${style.bgColor};
                                color: ${style.color};
                                padding: 3px 8px;
                                border-radius: 6px;
                                font-size: 10px;
                                font-weight: 700;
                                margin-bottom: 8px;
                            ">
                                <span>${style.emoji}</span>
                                <span>${style.label}</span>
                            </div>
                            
                            <!-- 시설 이름 -->
                            <div style="
                                font-size: 13px;
                                font-weight: 600;
                                color: #1f2937;
                                line-height: 1.4;
                                word-break: keep-all;
                            ">${facility.name}</div>
                            
                            <!-- 화살표 -->
                            <div style="
                                position: absolute;
                                bottom: -8px;
                                left: 50%;
                                transform: translateX(-50%);
                                width: 0;
                                height: 0;
                                border-left: 8px solid transparent;
                                border-right: 8px solid transparent;
                                border-top: 8px solid ${style.color};
                            "></div>
                            <div style="
                                position: absolute;
                                bottom: -5px;
                                left: 50%;
                                transform: translateX(-50%);
                                width: 0;
                                height: 0;
                                border-left: 6px solid transparent;
                                border-right: 6px solid transparent;
                                border-top: 6px solid white;
                            "></div>
                        </div>
                    `;

                    // 커스텀 오버레이 생성
                    const customOverlay = new window.kakao.maps.CustomOverlay({
                        position: position,
                        content: overlayContent,
                        yAnchor: 1.3,
                        xAnchor: 0.5,
                        zIndex: 50
                    });

                    // 오버레이 열림 상태 추적
                    let isOpen = false;

                    // 마커 클릭 시 토글 (열기/닫기)
                    window.kakao.maps.event.addListener(marker, 'click', () => {
                        if (isOpen) {
                            // 이미 열려있으면 닫기
                            customOverlay.setMap(null);
                            isOpen = false;
                            currentOpenOverlay = null;
                        } else {
                            // 다른 오버레이가 열려있으면 먼저 닫기
                            if (currentOpenOverlay) {
                                currentOpenOverlay.overlay.setMap(null);
                                currentOpenOverlay.setOpen(false);
                            }
                            // 새 오버레이 열기
                            customOverlay.setMap(mapRef.current);
                            isOpen = true;
                            currentOpenOverlay = { overlay: customOverlay, setOpen: (val: boolean) => { isOpen = val; } };
                        }
                    });

                    // 오버레이 클릭 시에도 닫기
                    overlayContent.addEventListener('click', () => {
                        customOverlay.setMap(null);
                        isOpen = false;
                        currentOpenOverlay = null;
                    });
                });

                console.log(`✅ ${category} 시설 마커 ${response.facilities.length}개 표시 완료`);
            } catch (error) {
                console.error(`❌ ${category} 시설 데이터 로드 실패:`, error);
            }
        });
    }, [activeCategories, landId]);


    // 매물 위치로 이동하는 함수
    const moveToPropertyLocation = () => {
        if (!mapRef.current || !currentLand) return;

        const position = new window.kakao.maps.LatLng(currentLand.latitude, currentLand.longitude);
        mapRef.current.setCenter(position);
        mapRef.current.setLevel(3); // 적절한 줌 레벨로 설정
    };

    return (
        <div className="relative w-full h-[450px] rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden p-2">
            <div
                ref={mapContainer}
                className="w-full h-full rounded-xl overflow-hidden"
            />

            {/* 매물위치 버튼 (상세 페이지에서만 표시) */}
            {landId && currentLand && (
                <button
                    onClick={moveToPropertyLocation}
                    className="absolute bottom-4 right-4 z-10 flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-gray-50 text-slate-700 font-semibold text-sm rounded-xl shadow-lg border border-gray-200 transition-all hover:shadow-xl active:scale-95"
                    title="매물 위치로 이동"
                >
                    <svg
                        className="w-4 h-4 text-purple-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                        />
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                    </svg>
                    <span>매물위치</span>
                </button>
            )}
        </div>
    );
}
