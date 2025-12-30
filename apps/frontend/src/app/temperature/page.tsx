'use client';

import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type TempKey = 'convenience' | 'traffic' | 'culture' | 'safety' | 'pet';

type TempItem = {
    key: TempKey;
    title: string;
    subtitle: string;
    icon: string;
    accent: string; // top color bar
    ring: string; // selected ring color
    desc: string;
    bullets: string[];
};

export default function TemperaturePage() {
    const items: TempItem[] = useMemo(
    () => [
        {
        key: 'convenience',
        title: '생활편의',
        subtitle: '일상 시설 접근성',
        icon: '🏪',
        accent: 'bg-red-500',
        ring: 'ring-red-400',
        desc: '편의점·세탁소·마트·공원까지의 거리를 기준으로, 일상생활이 얼마나 편리한지 평가합니다.',
        bullets: [
            '전체 매물 거리 분포(분위수) 기준으로 “가깝다/보통/멀다”를 나눕니다.',
            '가까울수록 점수가 높고, 기준 거리 이상은 점수가 크게 낮아집니다.',
            '공원은 거리 + 면적(규모)까지 함께 고려해 “작은 공원” 편향을 줄입니다.',
        ],
        },
        {
        key: 'traffic',
        title: '교통',
        subtitle: '지하철 + 버스',
        icon: '🚇',
        accent: 'bg-blue-500',
        ring: 'ring-blue-400',
        desc: '지하철은 “역까지 거리”, 버스는 “정류장 개수(밀도)”로 출퇴근·이동 편리함을 평가합니다.',
        bullets: [
            '지하철은 거리 기준(초역세권/역세권/보통/비역세권)으로 해석합니다.',
            '버스는 거리보다 “정류장 개수”가 체감에 직접 영향 → 개수 기반으로 점수화합니다.',
            '전체 매물 분포 대비 상대 위치를 보여주도록 설계했습니다.',
        ],
        },
        {
        key: 'culture',
        title: '문화',
        subtitle: '희소성 + 접근성',
        icon: '🎭',
        accent: 'bg-violet-500',
        ring: 'ring-violet-400',
        desc: '도서관·영화관·공연장·미술관 등 문화시설의 종류/개수/거리를 종합해 문화 접근성을 평가합니다.',
        bullets: [
            '문화시설은 분포가 불균형 → 희소한 시설에 더 높은 가중치를 둡니다.',
            '가까울수록 점수가 높아지는 거리 감쇠 방식을 적용합니다.',
            '과대대표 위험이 있는 시설(예: 도서관)은 가중치를 낮춰 변별력을 확보합니다.',
        ],
        },
        {
        key: 'safety',
        title: '안전',
        subtitle: '범죄 + 인프라',
        icon: '🛡️',
        accent: 'bg-orange-500',
        ring: 'ring-orange-400',
        desc: '범죄 위험(유형별 가중치)과 CCTV·경찰관서·비상벨 등 안전 인프라를 함께 고려해 안심도를 평가합니다.',
        bullets: [
            '범죄는 유형별 위험도를 다르게 반영해 “중범죄 영향”이 묻히지 않게 합니다.',
            '인프라는 정규화 후 가중합으로 반영(CCTV/경찰관서/비상벨).',
            '36.5°C를 평균 기준선으로 두어 사용자에게 직관적으로 비교 가능하게 합니다.',
        ],
        },
        {
        key: 'pet',
        title: '반려',
        subtitle: '반려 생활환경',
        icon: '🐶',
        accent: 'bg-emerald-500',
        ring: 'ring-emerald-400',
        desc: '동물병원·놀이터·그루밍·반려용품점·공원 등 반려 관련 시설 접근성을 가중치로 종합 평가합니다.',
        bullets: [
            '시설별 “기준 거리” 내에 있을수록 점수가 높습니다.',
            '반려놀이터/동물병원 등 체감 큰 시설에 더 높은 가중치를 적용합니다.',
            '기준 거리 밖이면 해당 항목은 0점 처리되어 해석이 명확합니다.',
        ],
        },
    ],
    []
    );

    const [selected, setSelected] = useState<TempKey>('convenience');
    const active = items.find((x) => x.key === selected)!;

  // Stagger variants for bullet list
    const listVariants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: { staggerChildren: 0.05, delayChildren: 0.06 },
    },
    };

    const itemVariants = {
    hidden: { opacity: 0, y: 6 },
    show: { opacity: 1, y: 0 },
    };

    return (
    <div className="max-w-7xl mx-auto px-4 py-12 mb-24">
      {/* Header */}
        <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-100 text-sky-700 text-sm font-semibold">
            POINTS
        </div>
        <h1 className="text-4xl font-extrabold text-slate-900 mt-4">
            온도란 무엇일까요?
        </h1>
        <p className="text-slate-600 mt-2">
            “이 집이 나에게 얼마나 잘 맞는지”를 데이터로 표현합니다.
        </p>
        </div>

      {/* Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {items.map((it) => {
            const isActive = it.key === selected;

            return (
            <motion.button
                key={it.key}
                onClick={() => setSelected(it.key)}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                animate={isActive ? { y: -2, scale: 1.02 } : { y: 0, scale: 1 }}
                transition={{ duration: 0.18 }}
                className={[
                'text-left rounded-2xl bg-white border border-slate-200 shadow-sm',
                'transition-shadow hover:shadow-md',
                'focus:outline-none focus:ring-2 focus:ring-offset-2',
                isActive ? `ring-2 ${it.ring} shadow-md` : '',
                ].join(' ')}
            >
              {/* top accent bar */}
                <div className={`h-1.5 w-16 rounded-full ${it.accent} ml-6 mt-5`} />
                <div className="p-6 pt-4">
                <div className="flex items-center gap-3">
                    <motion.span
                    className="text-3xl"
                    animate={isActive ? { rotate: [0, -8, 0] } : { rotate: 0 }}
                    transition={{ duration: 0.25 }}
                    >
                    {it.icon}
                    </motion.span>
                    <div>
                    <div className="text-lg font-bold text-slate-900">{it.title}</div>
                    <div className="text-sm text-slate-500">{it.subtitle}</div>
                    </div>
                </div>
                </div>
            </motion.button>
            );
        })}
        </div>

      {/* Details (animated switch) */}
        <div className="mt-8">
        <AnimatePresence mode="wait">
            <motion.div
            key={active.key}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 14 }}
            transition={{ duration: 0.22 }}
            className="rounded-3xl bg-white border border-slate-200 shadow-sm p-8"
            >
            <div className="flex items-start gap-4">
                <div className="text-4xl">{active.icon}</div>

                <div className="flex-1">
                <h2 className="text-2xl font-extrabold text-slate-900">
                    {active.title} 온도
                </h2>
                <p className="text-slate-600 mt-2 leading-relaxed">{active.desc}</p>

                <div className="mt-6">
                    <div className="text-sm font-bold text-slate-800 mb-2">
                    우리가 이렇게 판단합니다
                    </div>

                    <motion.ul
                    variants={listVariants}
                    initial="hidden"
                    animate="show"
                    className="space-y-2 text-slate-700"
                    >
                    {active.bullets.map((b, idx) => (
                        <motion.li key={idx} variants={itemVariants} className="flex gap-2">
                        <span className="mt-1.5 h-2 w-2 rounded-full bg-slate-400 shrink-0" />
                        <span className="leading-relaxed">{b}</span>
                        </motion.li>
                    ))}
                    </motion.ul>
                </div>
                </div>
            </div>
            </motion.div>
        </AnimatePresence>
        </div>

      {/* Tips (always visible, subtle entrance only once) */}
        <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18, delay: 0.1 }}
        className="mt-7 rounded-2xl bg-slate-50 border border-slate-200 p-5 text-slate-700"
        >
        <div className="font-bold mb-1">💡 활용 팁</div>
        <div className="text-sm leading-relaxed">
            온도는 “정답”이 아니라 비교를 돕는 지표입니다. 비슷한 가격의 매물이라도
            교통/생활/안전 등 강점이 다를 수 있어요. 본인 우선순위에 맞춰 참고해 주세요.
        </div>
        </motion.div>
    </div>
    );
}
