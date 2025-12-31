/**
 * 서비스 소개 페이지
 *
 * GoZip(고집) 서비스에 대한 소개 및 주요 기능 설명
 */

'use client'

import Link from 'next/link'

export default function ServiceInsPage() {
  const points = [
    { icon: '💰', title: '가격', desc: '시세 대비 수준 판단', grad: 'from-blue-500 to-cyan-500' },
    { icon: '📍', title: '입지', desc: '생활권·인접 지역 맥락', grad: 'from-emerald-500 to-green-500' },
    { icon: '🚇', title: '교통', desc: '출퇴근 동선 중심', grad: 'from-purple-500 to-violet-500' },
    { icon: '🧩', title: '조건', desc: '옵션·구조·요구사항', grad: 'from-lime-500 to-emerald-500' },
    { icon: '🔁', title: '대안', desc: '유사 매물·대체 선택지', grad: 'from-orange-500 to-red-500' },
  ]

  const features = [
    {
      icon: '💬',
      color: 'bg-blue-600',
      title: '질문 기반 상담',
      desc: '“강남역 근처”, “출퇴근하기 좋은 곳”처럼 표현이 달라도 부동산 맥락을 기준으로 의도를 이해해 답변합니다.',
      bg: 'from-blue-50 to-sky-50',
      border: 'border-blue-200/70',
      tag: '상담',
    },
    {
      icon: '⚖️',
      color: 'bg-purple-600',
      title: '시세 대비 가격 판단',
      desc: '주변 시세·유사 매물과 비교해 “저렴/적정/비쌈” 판단에 필요한 근거를 정리해줍니다.',
      bg: 'from-purple-50 to-violet-50',
      border: 'border-purple-200/70',
      tag: '판단',
    },
    {
      icon: '🧭',
      color: 'bg-emerald-600',
      title: '지역 분위기·생활 환경 안내',
      desc: '교통, 생활권, 주변 편의시설 같은 지역 특성을 요약해 “살기 좋은지”를 빠르게 판단할 수 있게 돕습니다.',
      bg: 'from-emerald-50 to-green-50',
      border: 'border-emerald-200/70',
      tag: '요약',
    },
    {
      icon: '🔁',
      color: 'bg-orange-600',
      title: '유사 매물·대안 추천',
      desc: '조건이 비슷하거나 생활권이 겹치는 대안을 함께 보여줘 선택지를 넓혀줍니다.',
      bg: 'from-orange-50 to-amber-50',
      border: 'border-orange-200/70',
      tag: '대안',
    },
    {
      icon: '🆚',
      color: 'bg-pink-600',
      title: '찜한 두 매물 비교 상담',
      desc: '두 매물을 나란히 비교해 어떤 기준에서 A/B가 유리한지 근거 중심으로 정리합니다.',
      bg: 'from-pink-50 to-rose-50',
      border: 'border-pink-200/70',
      tag: '비교',
    },
    {
      icon: '⚡',
      color: 'bg-red-600',
      title: '조건이 많아도 즉시 응답',
      desc: '지역·가격·옵션 같은 조건이 늘어나도 빠르게 답변이 나오도록 검색 구조를 최적화했습니다.',
      bg: 'from-red-50 to-orange-50',
      border: 'border-red-200/70',
      tag: '속도',
    },
  ]

  const steps = [
    {
      step: '01',
      title: '질문 입력',
      desc: '원하는 지역/예산/조건을 사람에게 말하듯 입력하세요. 정확한 검색어가 없어도 됩니다.',
      grad: 'from-blue-600 to-sky-600',
    },
    {
      step: '02',
      title: '추천·대안 확인',
      desc: '조건에 맞는 매물과 함께 유사 매물·대안까지 정리된 답변을 확인합니다.',
      grad: 'from-indigo-600 to-purple-600',
    },
    {
      step: '03',
      title: '두 매물 비교 상담',
      desc: '찜한 두 매물을 선택하면, 가격·교통·생활권 등 기준별 장단점을 나란히 비교해줍니다.',
      grad: 'from-emerald-600 to-teal-600',
    },
  ]

  return (
    <div className="min-h-screen text-slate-900 bg-[radial-gradient(1200px_700px_at_18%_-10%,rgba(99,102,241,0.28),transparent_60%),radial-gradient(900px_650px_at_90%_0%,rgba(14,165,233,0.22),transparent_58%),radial-gradient(1000px_700px_at_50%_110%,rgba(217,70,239,0.16),transparent_55%),linear-gradient(to_bottom,rgba(238,242,255,1),rgba(248,250,252,1),rgba(240,253,250,1))]">
      {/* subtle grid (indigo tint) */}
      <div className="pointer-events-none fixed inset-0 -z-10 opacity-[0.12] [background-image:linear-gradient(to_right,rgba(99,102,241,0.22)_1px,transparent_1px),linear-gradient(to_bottom,rgba(99,102,241,0.22)_1px,transparent_1px)] [background-size:56px_56px]" />

      <div className="max-w-5xl mx-auto px-4 pb-24 space-y-16">
        {/* HERO */}
        <section className="text-center space-y-6 pt-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-indigo-700 text-sm font-semibold border border-indigo-200/70 bg-white/75 backdrop-blur shadow-[0_14px_40px_-28px_rgba(99,102,241,0.55)]">
            <span className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse"></span>
            AI 기반 부동산 챗봇 상담 서비스
          </div>

          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
            부동산, 이제 검색하지 말고
            <br />
            <span className="bg-gradient-to-r from-indigo-600 via-sky-600 to-fuchsia-600 bg-clip-text text-transparent">
              GoZip
            </span>
            스럽게 물어보세요
          </h1>

          <p className="text-slate-700 text-lg max-w-2xl mx-auto leading-relaxed">
            실제 매물 데이터와 지역 정보를 기반으로,
            <br />
            <span className="font-semibold text-slate-900">질문 하나로</span> 매물 탐색부터 비교·판단까지 한 번에 안내받을 수 있습니다.
          </p>

          <div className="flex justify-center gap-4 pt-2 flex-wrap">
            <Link
              href="/main"
              className="group px-6 py-3 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white font-semibold rounded-xl transition-all shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/35 hover:-translate-y-0.5 active:translate-y-0"
            >
              <span className="inline-flex items-center gap-2">
                매물 둘러보기
                <span className="transition-transform group-hover:translate-x-0.5">→</span>
              </span>
            </Link>

            <Link
              href="/wishlist"
              className="px-6 py-3 bg-white/80 backdrop-blur text-slate-700 font-semibold rounded-xl border border-slate-200/80 hover:border-indigo-300 hover:text-indigo-700 transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0"
            >
              찜한 매물 비교하기
            </Link>
          </div>
        </section>
    {/* ABOUT */}
        <section className="space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center justify-center gap-2">
              <span>GoZip(고집)이란?</span>
              <span className="text-2xl">🏠</span>
            </h2>
            <p className="text-slate-700 text-sm font-medium">
              복잡한 부동산 정보를 “상담” 형태로 정리해주는 AI 서비스
            </p>
          </div>

          <div className="relative rounded-3xl border border-indigo-200/60 bg-white/70 backdrop-blur-xl shadow-[0_24px_70px_-45px_rgba(99,102,241,0.5)] overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-200/90 to-transparent" />
            <div className="absolute -top-28 -right-28 w-72 h-72 bg-indigo-400/16 blur-3xl rounded-full" />
            <div className="absolute -bottom-28 -left-28 w-72 h-72 bg-teal-400/12 blur-3xl rounded-full" />

            <div className="p-8 md:p-10">
              <div className="grid md:grid-cols-2 gap-10 items-center">
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-slate-900">부동산 정보를 더 쉽고 정확하게</h3>

                  <p className="text-slate-700 leading-relaxed">
                    부동산 정보는 구조가 복잡하고 비교해야 할 요소가 많습니다.
                    <br />
                    GoZip(고집)은 가격·위치·교통·주변 환경을 따로 확인하는 번거로움을 줄이고,
                    <span className="font-semibold text-indigo-700"> 필요한 정보만</span> 한 번에 안내합니다.
                  </p>

                  <ul className="space-y-2 text-slate-700">
                    <li className="flex items-center gap-2">
                      <span className="w-7 h-7 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-sm">
                        💬
                      </span>
                      <span>
                        <strong>질문 기반</strong>으로 편하게 상담
                      </span>
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-7 h-7 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center text-sm">
                        ✅
                      </span>
                      <span>
                        <strong>시세 대비</strong> 가격 판단 지원
                      </span>
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-7 h-7 rounded-full bg-fuchsia-50 border border-fuchsia-100 flex items-center justify-center text-sm">
                        🔁
                      </span>
                      <span>
                        <strong>대안 제시</strong> 및 비교 기준 정리
                      </span>
                    </li>
                  </ul>
                </div>

                <div className="flex justify-center">
                  <div className="relative w-56 h-56">
                    <div className="absolute inset-0 rounded-full ring-2 ring-indigo-400/55 animate-[ripple_2.2s_ease-out_infinite]" />
                    <div className="absolute inset-0 rounded-full ring-2 ring-fuchsia-400/40 animate-[ripple_2.2s_ease-out_infinite] [animation-delay:1.1s]" />
                    <div className="absolute inset-0 rounded-full bg-gradient-to-t from-indigo-400 via-sky-400 to-fuchsia-400 opacity-25 blur-xl" />

                    <div className="relative w-full h-full rounded-full bg-white/85 flex items-center justify-center shadow-xl border border-white/70">
                      <div className="text-center">
                        <div className="text-5xl font-extrabold bg-gradient-to-r from-indigo-600 via-sky-600 to-fuchsia-600 bg-clip-text text-transparent tracking-tight">
                          GoZip
                        </div>
                        <div className="text-sm text-slate-600 font-semibold mt-1">AI 상담</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* POINTS */}
        <section className="space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-100 text-sky-700 text-xs font-bold border border-sky-200/70">
              POINTS
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight flex items-center justify-center gap-2">
              <span>핵심 상담 포인트 5가지</span>
              <span className="text-2xl">📌</span>
            </h2>
            <p className="text-slate-700 text-sm font-medium">GoZip(고집)이 답변에서 우선으로 정리하는 기준</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {points.map((item, idx) => (
              <div
                key={idx}
                className="relative rounded-2xl bg-white border border-sky-200/70 shadow-[0_16px_45px_-40px_rgba(2,132,199,0.55)] p-5 hover:-translate-y-1 transition-all"
              >
                <div className={`absolute left-5 top-0 -translate-y-1/2 h-[6px] w-14 rounded-full bg-gradient-to-r ${item.grad}`} />
                <div className="text-3xl mb-3 mt-2">{item.icon}</div>
                <h3 className="font-bold text-slate-900 mb-1">{item.title}</h3>
                <p className="text-xs text-slate-700 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* FEATURES */}
        <section className="space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-100 text-sky-700 text-xs font-bold border border-sky-200/70">
              FEATURES
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight flex items-center justify-center gap-2">
              <span>주요 기능</span>
              <span className="text-2xl">✨</span>
            </h2>
            <p className="text-slate-700 text-sm font-medium">GoZip이 제공하는 상담 기능</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {features.map((f, idx) => (
              <div
                key={idx}
                className={`relative rounded-[22px] border ${f.border} bg-white shadow-[0_18px_55px_-44px_rgba(2,132,199,0.55)] overflow-hidden p-6 hover:-translate-y-1 transition-all`}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${f.bg}`} />
                <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/70 to-transparent" />

                <div className="relative flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-2xl ${f.color} text-white flex items-center justify-center text-2xl shadow-[0_12px_25px_-18px_rgba(0,0,0,0.35)]`}>
                    {f.icon}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold bg-white/80 border border-sky-200/70 text-slate-700">
                        {f.tag}
                      </span>
                      <h3 className="text-lg font-bold text-slate-900">{f.title}</h3>
                    </div>

                    <p className="text-slate-700 text-sm leading-relaxed">{f.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* HOW IT WORKS: 2x2 (ML/ML/ES/Neo4j) */}
        <section className="space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-100 text-sky-700 text-xs font-bold border border-sky-200/70">
              HOW IT WORKS
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight">GoZip은 어떻게 ‘판단’을 제공하나요?</h2>
            <p className="text-slate-700 text-sm font-medium">
              “가격 합리성” + “중개소 신뢰도”를 머신러닝으로 판단하고, Elasticserch/Neo4j로 상담을 완성합니다
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* ML 1 */}
            <div className="relative rounded-[24px] bg-white border border-sky-200/70 shadow-[0_18px_55px_-44px_rgba(2,132,199,0.55)] overflow-hidden p-7">
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400" />
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">💰</span>
                <h3 className="text-lg font-bold text-slate-900">실거래가 기반 가격 판단</h3>
              </div>

              <p className="text-slate-700 leading-relaxed">
                GoZip은 실제 거래된 데이터를 기준으로
                해당 매물이 <strong>시세 대비 저렴/적정/비쌈</strong>인지 판단합니다.
              </p>

              <div className="mt-4 space-y-2 text-sm text-slate-700">
                <div className="rounded-xl bg-sky-50 border border-sky-200/70 p-3">
                  같은 지역·비슷한 조건의 거래를 기준으로 <strong>가격 기준선</strong>을 만듭니다.
                </div>
                <div className="rounded-xl bg-sky-50 border border-sky-200/70 p-3">
                  단순 평균이 아니라, 조건(지역/유형/면적/연월 등)을 반영해 <strong>비교 가능한 시세</strong>로 판단합니다.
                </div>
              </div>

              <div className="mt-4 rounded-xl bg-white border border-sky-200/70 p-3 text-sm text-slate-700">
                결과: “왜 저렴/적정/비쌈인지”를 상담 답변에 근거로 제공합니다.
              </div>
            </div>

            {/* ML 2 */}
            <div className="relative rounded-[24px] bg-white border border-sky-200/70 shadow-[0_18px_55px_-44px_rgba(2,132,199,0.55)] overflow-hidden p-7">
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-sky-500 to-indigo-500" />
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">🏢</span>
                <h3 className="text-lg font-bold text-slate-900">중개소 신뢰도 판단</h3>
              </div>

              <p className="text-slate-700 leading-relaxed">
                GoZip은 거래 실적만 보지 않습니다.
                <br />
                <strong>중개소의 운영 구조·업력·인력 구성</strong>을 분석해
                구조적으로 신뢰할 수 있는 중개소인지 판단합니다.
              </p>

              <div className="mt-4 space-y-2 text-sm text-slate-700">
                <div className="rounded-xl bg-blue-50 border border-blue-200/70 p-3">
                  “운영 방식” 자체에서 나타나는 리스크 신호를 잡아냅니다.
                </div>
                <div className="rounded-xl bg-blue-50 border border-blue-200/70 p-3">
                  계약 전 단계에서 <strong>리스크를 미리 고려</strong>할 수 있도록 근거를 제공합니다.
                </div>
              </div>

              <div className="mt-4 rounded-xl bg-white border border-sky-200/70 p-3 text-sm text-slate-700">
                결과: 금/은/동 으로 “신뢰도”를 판단하는 보조 기준이 됩니다.
              </div>
            </div>

            {/* ES */}
            <div className="relative rounded-[24px] bg-white border border-sky-200/70 shadow-[0_18px_55px_-44px_rgba(2,132,199,0.55)] overflow-hidden p-7">
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-sky-400 via-cyan-500 to-blue-500" />
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">⚡</span>
                <h3 className="text-lg font-bold text-slate-900">Elasticsearch (빠른 탐색)</h3>
              </div>

              <p className="text-slate-700 leading-relaxed">
                사용자가 질문을 입력하면 관련 매물과 정보를 빠르게 찾아냅니다.
                수많은 매물을 훑는 대신, 필요한 조건이 어디에 있는지 미리 정리된 검색 시스템입니다.
              </p>

              <div className="mt-4 grid gap-2 text-sm">
                <div className="bg-sky-50 border border-sky-200/70 rounded-xl px-4 py-3 text-slate-700">
                  조건이 많아져도 빠르게
                </div>
                <div className="bg-sky-50 border border-sky-200/70 rounded-xl px-4 py-3 text-slate-700">
                  매물이 늘어나도 지연 없이
                </div>
                <div className="bg-sky-50 border border-sky-200/70 rounded-xl px-4 py-3 text-slate-700">
                  후보 매물/근거 데이터 즉시 구성
                </div>
              </div>
            </div>

            {/* Neo4j */}
            <div className="relative rounded-[24px] bg-white border border-sky-200/70 shadow-[0_18px_55px_-44px_rgba(2,132,199,0.55)] overflow-hidden p-7">
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-400 via-sky-500 to-cyan-400" />
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">🕸️</span>
                <h3 className="text-lg font-bold text-slate-900">Neo4j (관계 기반 비교)</h3>
              </div>

              <p className="text-slate-700 leading-relaxed">
                검색으로 후보를 찾은 뒤,
                “비슷한 가격대/생활권/시설” 같은 연결 관계를 따라가며
                함께 비교할 만한 대안과 선택 기준까지 제시합니다.
              </p>

              <div className="mt-4 space-y-2 text-sm text-slate-700">
                <div className="bg-emerald-50 border border-emerald-200/70 rounded-xl px-4 py-3">
                  주변 인프라가 비슷한 매물
                </div>
                <div className="bg-emerald-50 border border-emerald-200/70 rounded-xl px-4 py-3">
                  각종 온도를 통한 직관적인 매물 비교
                </div>
                <div className="bg-emerald-50 border border-emerald-200/70 rounded-xl px-4 py-3">
                  사용자의 선호도를 반영한 맞춤 추천
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[22px] bg-gradient-to-r from-blue-600 via-sky-600 to-indigo-600 text-white p-6 shadow-[0_18px_55px_-44px_rgba(37,99,235,0.7)]">
            <p className="text-sm leading-relaxed text-white/95">
              GoZip은 <span className="font-semibold text-white">ML로 가격/신뢰도를 판단</span>하고,
              <span className="font-semibold text-white"> Elasticserch로 빠르게 후보를 찾고</span>,
              <span className="font-semibold text-white"> Neo4j로 비교를 확장</span>해
              “검색”이 아니라 “판단”을 제공하는 상담을 완성합니다.
            </p>
          </div>
        </section>

        {/* HOW TO USE */}
        <section className="space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-100 text-sky-700 text-xs font-bold border border-sky-200/70">
              STEPS
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight flex items-center justify-center gap-2">
              <span>이용 방법</span>
              <span className="text-2xl">🚀</span>
            </h2>
            <p className="text-slate-700 text-sm font-medium">3단계로 시작하는 GoZip 상담</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {steps.map((s, idx) => (
              <div
                key={idx}
                className="relative rounded-[22px] bg-white border border-sky-200/70 shadow-[0_18px_55px_-44px_rgba(2,132,199,0.55)] overflow-hidden p-6 hover:-translate-y-1 transition-all"
              >
                <div className={`absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r ${s.grad}`} />
                <div className={`inline-flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-r ${s.grad} text-white font-extrabold text-sm mb-4 shadow-[0_14px_30px_-20px_rgba(0,0,0,0.35)]`}>
                  {s.step}
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{s.title}</h3>
                <p className="text-slate-700 text-sm leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="relative rounded-[28px] bg-gradient-to-r from-blue-600 via-sky-600 to-indigo-600 p-10 text-center text-white shadow-[0_30px_90px_-60px_rgba(37,99,235,0.85)] overflow-hidden">
          <div className="absolute -top-28 -left-28 w-[420px] h-[420px] rounded-full bg-white/14 blur-3xl" />
          <div className="absolute -bottom-28 -right-28 w-[460px] h-[460px] rounded-full bg-white/10 blur-3xl" />

          <h2 className="relative text-2xl md:text-3xl font-extrabold mb-3">
            지금 바로 GoZip(고집)과 상담해보세요
          </h2>
          <p className="relative text-white/90 mb-6 max-w-xl mx-auto">
            검색에 시간을 쓰는 대신, “나에게 맞는 선택”을 고민하는 데 집중하세요.
          </p>

          <div className="relative flex justify-center gap-4 flex-wrap">
            <Link
              href="/main"
              className="px-8 py-3 bg-white text-blue-700 font-bold rounded-xl hover:bg-blue-50 transition-all shadow-lg hover:-translate-y-0.5 active:translate-y-0"
            >
              GoZip과 매물 보러가기
            </Link>
            
          </div>
        </section>
      </div>
    </div>
  )
}
