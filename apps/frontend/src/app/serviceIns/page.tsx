/**
 * 서비스 소개 페이지
 *
 * Ondo House 서비스에 대한 소개 및 주요 기능 설명
 */

'use client'

import Link from 'next/link'

export default function ServiceInsPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 space-y-16 mb-24">
      {/* 히어로 섹션 */}
      <section className="text-center space-y-4 pt-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100/80 rounded-full text-blue-700 text-sm font-medium mb-4">
          <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
          AI 기반 부동산 추천 서비스
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 drop-shadow-sm">
          당신의 완벽한 보금자리,
          <br />
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            ONDO HOUSE
          </span>
          가 찾아드립니다
        </h1>
        <p className="text-slate-700 text-lg max-w-2xl mx-auto leading-relaxed drop-shadow-sm">
          서울 전역 <span className="font-semibold text-slate-900">9,900개 이상</span>의 매물 데이터와 
          AI 분석을 통해 나에게 딱 맞는 집을 추천받으세요.
          <br />
          복잡한 부동산 정보, 이제 온도로 쉽게 이해하세요.
        </p>
        <div className="flex justify-center gap-4 pt-4">
          <Link
            href="/main"
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg shadow-blue-500/25"
          >
            매물 둘러보기 →
          </Link>
          <Link
            href="/preferenceSurvey"
            className="px-6 py-3 bg-white text-slate-700 font-semibold rounded-xl border-2 border-slate-200 hover:border-blue-300 hover:text-blue-600 transition-all"
          >
            선호도 설문하기
          </Link>
        </div>
      </section>

      {/* 온도 시스템 소개 */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold text-slate-900 flex items-center justify-center gap-2 drop-shadow-sm">
            <span>온도 시스템이란?</span>
            <span className="text-2xl">🌡️</span>
          </h2>
          <p className="text-slate-700 text-sm font-medium drop-shadow-sm">
            ONDO HOUSE만의 독자적인 매물 평가 시스템
          </p>
        </div>
        
        <div className="relative rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-2xl overflow-hidden p-8">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-slate-800">
                복잡한 부동산 정보를 직관적인 온도로
              </h3>
              <p className="text-slate-700 leading-relaxed">
                교통, 편의시설, 안전, 공원 접근성 등 다양한 요소를 종합 분석하여 
                <span className="font-semibold text-blue-700"> 0°C ~ 100°C</span>의 
                직관적인 온도 지표로 표현합니다.
              </p>
              <ul className="space-y-2 text-slate-700">
                <li className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center text-sm">🔥</span>
                  <span><strong>높은 온도</strong> = 선호도에 잘 맞는 매물</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-sm">❄️</span>
                  <span><strong>낮은 온도</strong> = 선호도와 거리가 있는 매물</span>
                </li>
              </ul>
            </div>
            <div className="flex justify-center">
              <div className="relative w-48 h-48">
                <div className="absolute inset-0 bg-gradient-to-t from-blue-400 via-yellow-400 to-red-400 rounded-full opacity-20 blur-xl"></div>
                <div className="relative w-full h-full bg-white/80 rounded-full flex items-center justify-center shadow-xl border-4 border-white">
                  <div className="text-center">
                    <div className="text-5xl font-bold bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
                      78°
                    </div>
                    <div className="text-sm text-slate-600 font-medium mt-1">따뜻한 매물</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 온도 분석 요소 */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold text-slate-900 flex items-center justify-center gap-2 drop-shadow-sm">
            <span>5가지 핵심 분석 요소</span>
            <span className="text-2xl">📊</span>
          </h2>
          <p className="text-slate-700 text-sm font-medium drop-shadow-sm">
            AI가 분석하는 매물 평가 기준
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-4">
          {[
            { icon: '🚇', title: '교통', desc: '지하철역, 버스정류장 접근성', color: 'from-blue-500 to-cyan-500' },
            { icon: '🏪', title: '편의시설', desc: '마트, 편의점, 카페 등', color: 'from-green-500 to-emerald-500' },
            { icon: '🛡️', title: '안전', desc: 'CCTV, 치안 시설 현황', color: 'from-purple-500 to-violet-500' },
            { icon: '🌳', title: '공원', desc: '녹지공간, 공원 접근성', color: 'from-lime-500 to-green-500' },
            { icon: '✅', title: '신뢰도', desc: '허위매물 검증 점수', color: 'from-orange-500 to-red-500' },
          ].map((item, idx) => (
            <div
              key={idx}
              className="relative rounded-2xl border-white/40 border-2 bg-white/70 backdrop-blur-md shadow-lg overflow-hidden p-5 hover:shadow-xl transition-all hover:-translate-y-1"
            >
              <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${item.color}`}></div>
              <div className="text-3xl mb-3">{item.icon}</div>
              <h3 className="font-bold text-slate-800 mb-1">{item.title}</h3>
              <p className="text-xs text-slate-600">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 주요 기능 */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold text-slate-900 flex items-center justify-center gap-2 drop-shadow-sm">
            <span>주요 기능</span>
            <span className="text-2xl">✨</span>
          </h2>
          <p className="text-slate-700 text-sm font-medium drop-shadow-sm">
            ONDO HOUSE가 제공하는 스마트한 기능들
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* 기능 1 */}
          <div className="rounded-2xl border-white/40 border-2 bg-gradient-to-br from-blue-50/80 to-sky-100/80 backdrop-blur-md shadow-lg p-6 hover:shadow-xl transition-all">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center text-2xl shadow-lg">
                🗺️
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-800 mb-2">지도 기반 매물 탐색</h3>
                <p className="text-slate-600 text-sm leading-relaxed">
                  서울 25개 구의 매물을 지도에서 한눈에 확인하세요. 
                  지역별 온도 분포를 시각적으로 파악하고, 클릭 한 번으로 상세 정보를 확인할 수 있습니다.
                </p>
              </div>
            </div>
          </div>

          {/* 기능 2 */}
          <div className="rounded-2xl border-white/40 border-2 bg-gradient-to-br from-purple-50/80 to-violet-100/80 backdrop-blur-md shadow-lg p-6 hover:shadow-xl transition-all">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-purple-500 flex items-center justify-center text-2xl shadow-lg">
                🎯
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-800 mb-2">맞춤형 매물 추천</h3>
                <p className="text-slate-600 text-sm leading-relaxed">
                  선호도 설문을 통해 나만의 기준을 설정하면, AI가 9,900개 이상의 매물 중 
                  가장 적합한 매물을 온도 순으로 추천해드립니다.
                </p>
              </div>
            </div>
          </div>

          {/* 기능 3 */}
          <div className="rounded-2xl border-white/40 border-2 bg-gradient-to-br from-emerald-50/80 to-green-100/80 backdrop-blur-md shadow-lg p-6 hover:shadow-xl transition-all">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500 flex items-center justify-center text-2xl shadow-lg">
                💬
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-800 mb-2">AI 챗봇 상담</h3>
                <p className="text-slate-600 text-sm leading-relaxed">
                  부동산 관련 궁금한 점이 있으신가요? RAG 기반 AI 챗봇이 매물 정보부터 
                  지역 특성까지 24시간 친절하게 답변해드립니다.
                </p>
              </div>
            </div>
          </div>

          {/* 기능 4 */}
          <div className="rounded-2xl border-white/40 border-2 bg-gradient-to-br from-orange-50/80 to-amber-100/80 backdrop-blur-md shadow-lg p-6 hover:shadow-xl transition-all">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-orange-500 flex items-center justify-center text-2xl shadow-lg">
                📋
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-800 mb-2">스마트 필터링</h3>
                <p className="text-slate-600 text-sm leading-relaxed">
                  거래유형(매매/전세/월세/단기임대), 건물유형(아파트/빌라/원투룸/오피스텔), 
                  지역별로 원하는 조건의 매물만 빠르게 찾아보세요.
                </p>
              </div>
            </div>
          </div>

          {/* 기능 5 */}
          <div className="rounded-2xl border-white/40 border-2 bg-gradient-to-br from-pink-50/80 to-rose-100/80 backdrop-blur-md shadow-lg p-6 hover:shadow-xl transition-all">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-pink-500 flex items-center justify-center text-2xl shadow-lg">
                ❤️
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-800 mb-2">찜 매물 AI 분석</h3>
                <p className="text-slate-600 text-sm leading-relaxed">
                  마음에 드는 매물을 찜하면 AI가 해당 매물들을 종합 분석하여 
                  나의 선호 패턴과 최적의 매물 조합을 추천해드립니다.
                </p>
              </div>
            </div>
          </div>

          {/* 기능 6 */}
          <div className="rounded-2xl border-white/40 border-2 bg-gradient-to-br from-red-50/80 to-orange-100/80 backdrop-blur-md shadow-lg p-6 hover:shadow-xl transition-all">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-red-500 flex items-center justify-center text-2xl shadow-lg">
                🔍
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-800 mb-2">등기부등본 분석</h3>
                <p className="text-slate-600 text-sm leading-relaxed">
                  전세사기 위험을 사전에 차단! AI가 등기부등본을 분석하여 
                  근저당, 가압류 등 위험 요소를 자동으로 감지하고 알려드립니다.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 데이터 현황 */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold text-slate-900 flex items-center justify-center gap-2 drop-shadow-sm">
            <span>실시간 데이터 현황</span>
            <span className="text-2xl">📈</span>
          </h2>
          <p className="text-slate-700 text-sm font-medium drop-shadow-sm">
            ONDO HOUSE가 보유한 매물 현황
          </p>
        </div>

        <div className="rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md shadow-2xl overflow-hidden p-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div className="space-y-1">
              <div className="text-4xl font-bold text-blue-600">9,914</div>
              <div className="text-sm text-slate-600 font-medium">총 매물 수</div>
            </div>
            <div className="space-y-1">
              <div className="text-4xl font-bold text-emerald-600">25</div>
              <div className="text-sm text-slate-600 font-medium">서울 전 지역</div>
            </div>
            <div className="space-y-1">
              <div className="text-4xl font-bold text-purple-600">4</div>
              <div className="text-sm text-slate-600 font-medium">거래유형</div>
            </div>
            <div className="space-y-1">
              <div className="text-4xl font-bold text-orange-600">5</div>
              <div className="text-sm text-slate-600 font-medium">분석 요소</div>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-white/40">
            <h4 className="text-sm font-semibold text-slate-700 mb-4 text-center">거래유형별 매물 분포</h4>
            <div className="flex flex-wrap justify-center gap-3">
              {[
                { type: '월세', count: '6,351', percent: '64%', color: 'bg-blue-500' },
                { type: '전세', count: '1,965', percent: '20%', color: 'bg-emerald-500' },
                { type: '단기임대', count: '1,014', percent: '10%', color: 'bg-purple-500' },
                { type: '매매', count: '582', percent: '6%', color: 'bg-orange-500' },
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-white/60 rounded-full px-4 py-2">
                  <span className={`w-3 h-3 rounded-full ${item.color}`}></span>
                  <span className="text-sm font-medium text-slate-700">{item.type}</span>
                  <span className="text-xs text-slate-500">{item.count}개 ({item.percent})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 이용 방법 */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold text-slate-900 flex items-center justify-center gap-2 drop-shadow-sm">
            <span>이용 방법</span>
            <span className="text-2xl">🚀</span>
          </h2>
          <p className="text-slate-700 text-sm font-medium drop-shadow-sm">
            3단계로 시작하는 스마트한 집 찾기
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              step: '01',
              title: '회원가입 & 로그인',
              desc: 'Google 계정으로 간편하게 로그인하세요. 별도의 회원가입 절차 없이 바로 시작할 수 있습니다.',
              color: 'from-blue-500 to-blue-600',
            },
            {
              step: '02',
              title: '선호도 설문',
              desc: '교통, 편의시설, 안전, 공원 등 나에게 중요한 요소들의 우선순위를 설정해주세요.',
              color: 'from-purple-500 to-purple-600',
            },
            {
              step: '03',
              title: '맞춤 매물 확인',
              desc: 'AI가 분석한 온도 기반 추천 매물을 확인하고, 마음에 드는 매물을 찜해보세요.',
              color: 'from-emerald-500 to-emerald-600',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="relative rounded-2xl border-white/40 border-2 bg-white/70 backdrop-blur-md shadow-lg overflow-hidden p-6 hover:shadow-xl transition-all"
            >
              <div className={`absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r ${item.color}`}></div>
              <div className={`inline-flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-r ${item.color} text-white font-bold text-sm mb-4`}>
                {item.step}
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-2">{item.title}</h3>
              <p className="text-slate-600 text-sm leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA 섹션 */}
      <section className="rounded-2xl bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 p-10 text-center text-white shadow-2xl">
        <h2 className="text-2xl md:text-3xl font-bold mb-3">
          지금 바로 나만의 보금자리를 찾아보세요
        </h2>
        <p className="text-blue-100 mb-6 max-w-xl mx-auto">
          ONDO HOUSE와 함께라면 복잡한 부동산 정보도 쉽고 빠르게 이해할 수 있습니다.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <Link
            href="/main"
            className="px-8 py-3 bg-white text-blue-600 font-bold rounded-xl hover:bg-blue-50 transition-all shadow-lg"
          >
            매물 둘러보기
          </Link>
          <Link
            href="/community"
            className="px-8 py-3 bg-white/20 text-white font-bold rounded-xl hover:bg-white/30 transition-all border border-white/30"
          >
            커뮤니티 방문하기
          </Link>
        </div>
      </section>
    </div>
  )
}
