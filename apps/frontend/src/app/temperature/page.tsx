/**
 * TemperaturePage
 *
 * 온도 상세 정보 페이지
 *
 * 주요 기능:
 * - 5가지 온도(교통, 편의시설, 공원, 허위매물, 치안/안전)에 대한 설명
 * - 카드 형태로 표시하고 자세히 보기 버튼으로 상세 내용 토글
 */

'use client';

import ToggleTemperatureCard, { type ToggleTemperatureCardProps } from '@/components/ToggleTemperatureCard';

export default function TemperaturePage() {
    const temperatureCards: ToggleTemperatureCardProps[] = [
        {
            icon: '🚇',
            title: '교통온도',
            description: '지하철과 버스의 접근성을 나타내는 지표입니다. 출퇴근과 일상생활 이동의 편리함을 평가합니다.',
            color: 'from-blue-100/80 to-blue-200/80',
            details: {
                subtitle: '어떻게 계산되나요?',
                howItWorks: '매물에서 가장 가까운 지하철역 3곳과 버스 정류장까지의 거리를 측정합니다. 역의 규모(이용객 수)와 출퇴근 시간대 혼잡도를 함께 고려하여 점수를 계산합니다. 가까울수록, 역이 클수록 높은 점수를 받습니다.',
                examples: [
                    '지하철역까지 도보 5분 이내면 매우 우수',
                    '버스 정류장이 많고 가까울수록 좋음',
                    '출퇴근 시간대 이용객이 많은 역은 가산점',
                    '여러 노선 환승 가능한 역은 추가 점수'
                ]
            }
        },
        {
            icon: '🏪',
            title: '편의시설온도',
            description: '일상생활에 필요한 편의점, 마트, 병원, 약국 등의 접근성을 나타내는 지표입니다. 매물 내부 옵션도 함께 고려합니다.',
            color: 'from-yellow-100/80 to-yellow-200/80',
            details: {
                subtitle: '어떻게 계산되나요?',
                howItWorks: '매물에 세탁기, 냉장고, 주방 시설이 있는지 확인합니다. 옵션이 부족할수록 외부 편의시설(빨래방, 식당 등)이 더 중요해집니다. 동시에 주변 500m 이내 편의점, 마트, 병원, 약국의 개수와 거리를 측정하여 종합적으로 점수를 매깁니다.',
                examples: [
                    '풀옵션 매물은 기본 점수가 높음',
                    '도보 5분 내 편의점/마트가 있으면 우수',
                    '병원, 약국이 10분 이내 거리면 좋음',
                    '옵션 부족 시 주변 시설이 더 중요함'
                ]
            }
        },
        {
            icon: '🌳',
            title: '공원온도',
            description: '산책, 운동, 휴식을 위한 공원과 녹지 공간의 접근성을 나타내는 지표입니다. 공원의 크기와 시설도 함께 평가합니다.',
            color: 'from-green-100/80 to-green-200/80',
            details: {
                subtitle: '어떻게 계산되나요?',
                howItWorks: '집 근처 800m 이내 공원들을 찾아 각 공원의 면적, 시설(운동기구, 벤치, 화장실 등), 종류(근린공원, 어린이공원 등)를 평가합니다. 가까운 공원일수록, 공원이 클수록, 시설이 많을수록 높은 점수를 받습니다.',
                examples: [
                    '도보 5분 내 근린공원이 있으면 매우 우수',
                    '공원 면적이 클수록 좋음',
                    '운동기구, 산책로가 있으면 가산점',
                    '여러 공원이 가까이 있으면 추가 점수'
                ]
            }
        },
        {
            icon: '🚫',
            title: '허위매물온도',
            description: '.',
            color: 'from-red-100/80 to-red-200/80',
            details: {
                subtitle: '어떻게 계산되나요?',
                howItWorks: '.',
                examples: [
                    '.'
                ]
            }
        },
        {
            icon: '⭐',
            title: '치안/안전온도',
            description: '.',
            color: 'from-orange-100/80 to-orange-200/80',
            details: {
                subtitle: '어떻게 계산되나요?',
                howItWorks: '.',
                examples: [
                    '.'
                ]
            }
        }
    ];

    return (
        <div className="max-w-7xl mx-auto px-4 py-12 mb-24">
            {/* 페이지 제목 */}
            <div className="text-center mb-12">
                <h1 className="text-4xl font-bold text-slate-800 mb-4">
                    온도(Temperature)란? 🌡️
                </h1>
                <div className="space-y-2 text-slate-700 text-lg max-w-3xl mx-auto">
                    <p>
                        매물의 특성을 <strong className="text-blue-600">30~43°C</strong> 사이 수치로 표현한 지표입니다.
                    </p>
                    <p className="text-base text-slate-600">
                        36.5°C = 서울 평균 수준 | 높을수록 해당 항목이 우수함
                    </p>
                </div>
            </div>

            {/* 온도 카드 그리드 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                {temperatureCards.map((card, index) => (
                    <ToggleTemperatureCard key={index} {...card} />
                ))}
            </div>

            {/* 안내 문구 */}
            <div className="p-6 rounded-2xl border-2 border-white/40 bg-gradient-to-r from-sky-100/60 to-blue-100/60 backdrop-blur-md shadow-lg">
                <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
                    <span>💡</span>
                    <span>온도는 어떻게 활용되나요?</span>
                </h3>
                <p className="text-slate-700 leading-relaxed">
                    각 온도는 0.0 ~ 1.0 사이의 점수를 30~43°C로 변환한 값입니다.
                    선호도 조사에서 선택한 우선순위에 따라 각 온도에 가중치가 적용되어,
                    회원님께 가장 적합한 매물을 추천해드립니다.
                </p>
            </div>
        </div>
    );
}
