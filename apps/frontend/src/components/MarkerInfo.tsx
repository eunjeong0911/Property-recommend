/**
 * MarkerInfo 컴포넌트
 * 
 * 지도 마커 정보 컴포넌트
 * 
 * 주요 기능:
 * - 마커 정보 표시
 */

'use client';

interface MarkerItem {
    id: string;
    name: string;
    icon: string;
    count: number;
    description: string;
}

const markerData: MarkerItem[] = [
    {
        id: 'bus',
        name: '버스 정류장',
        icon: '/icons/bus.png',
        count: 12,
        description: '반경 500m 내'
    },
    {
        id: 'market',
        name: '편의점/마트',
        icon: '/icons/market.png',
        count: 8,
        description: '반경 500m 내'
    },
    {
        id: 'hospital',
        name: '병원',
        icon: '/icons/hospital.png',
        count: 5,
        description: '반경 1km 내'
    },
    {
        id: 'cctv',
        name: 'CCTV',
        icon: '/icons/cctv.png',
        count: 24,
        description: '반경 500m 내'
    }
];

export default function MarkerInfo() {
    return (
        <div className="bg-white rounded-lg shadow-md p-6" style={{ height: '500px' }}>
            <h3 className="text-lg font-bold mb-4">주변 시설 정보</h3>
            
            <div className="space-y-6">
                {markerData.map((marker) => (
                    <div 
                        key={marker.id}
                        className="flex items-center gap-4 p-4 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100"
                    >
                        <div className="flex-shrink-0">
                            <img 
                                src={marker.icon} 
                                alt={marker.name}
                                className="w-10 h-10 object-contain"
                            />
                        </div>
                        
                        <div className="flex-1">
                            <div className="flex items-center justify-between">
                                <h4 className="font-semibold text-gray-800">{marker.name}</h4>
                                <span className="text-lg font-bold text-blue-600">{marker.count}개</span>
                            </div>
                            <p className="text-sm text-gray-500 mt-1">{marker.description}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
