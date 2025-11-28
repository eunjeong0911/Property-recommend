/**
 * PreferenceFilter 컴포넌트
 * 
 * 사용자 선호도 기반 매물 필터링 컴포넌트
 * 
 * 주요 기능:
 * - 버튼 형태의 필터 옵션 선택 (대중교통, 주변 공원, 대학/직장 거리, 편의시설, 치안/안전, 허위매물, 초기화)
 * - 선택된 필터 조건 표시
 */

'use client';

import {
    motion,
    MotionValue,
    useMotionValue,
    useSpring,
    useTransform,
    type SpringOptions,
    AnimatePresence
} from 'framer-motion';
import React, { Children, cloneElement, useEffect, useMemo, useRef, useState } from 'react';

// --- Dock Components ---

type DockItemProps = {
    className?: string;
    children: React.ReactNode;
    onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
    mouseX: MotionValue<number>;
    spring: SpringOptions;
    distance: number;
    baseItemSize: number;
    magnification: number;
    isSelected?: boolean;
};

function DockItem({
    children,
    className = '',
    onClick,
    mouseX,
    spring,
    distance,
    magnification,
    baseItemSize,
    isSelected
}: DockItemProps) {
    const ref = useRef<HTMLDivElement>(null);
    const isHovered = useMotionValue(0);

    const mouseDistance = useTransform(mouseX, (val: number) => {
        const rect = ref.current?.getBoundingClientRect() ?? {
            x: 0,
            width: baseItemSize
        };
        return val - rect.x - baseItemSize / 2;
    });

    const targetSize = useTransform(mouseDistance, [-distance, 0, distance], [baseItemSize, magnification, baseItemSize]);
    const size = useSpring(targetSize, spring);

    return (
        <motion.div
            ref={ref}
            style={{
                width: size,
                height: size
            }}
            onHoverStart={() => isHovered.set(1)}
            onHoverEnd={() => isHovered.set(0)}
            onFocus={() => isHovered.set(1)}
            onBlur={() => isHovered.set(0)}
            onClick={onClick}
            className={`
                relative inline-flex items-center justify-center rounded-full border-2 shadow-md cursor-pointer
                transition-colors duration-200
                ${isSelected
                    ? 'bg-blue-500 border-blue-400 text-white'
                    : 'bg-white/50 border-white/40 text-slate-600 hover:border-white/80'
                }
                ${className}
            `}
            tabIndex={0}
            role="button"
            aria-pressed={isSelected}
        >
            {Children.map(children, child =>
                React.isValidElement(child)
                    ? cloneElement(child as React.ReactElement<{ isHovered?: MotionValue<number> }>, { isHovered })
                    : child
            )}
        </motion.div>
    );
}

type DockLabelProps = {
    className?: string;
    children: React.ReactNode;
    isHovered?: MotionValue<number>;
};

function DockLabel({ children, className = '', isHovered }: DockLabelProps) {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (!isHovered) return;
        const unsubscribe = isHovered.on('change', (latest: number) => {
            setIsVisible(latest === 1);
        });
        return () => unsubscribe();
    }, [isHovered]);

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 0, y: 0 }}
                    animate={{ opacity: 1, y: -10 }}
                    exit={{ opacity: 0, y: 0 }}
                    transition={{ duration: 0.2 }}
                    className={`${className} absolute -top-8 left-1/2 w-fit whitespace-pre rounded-md border border-slate-600 bg-slate-800 px-2 py-1 text-xs text-white z-50`}
                    role="tooltip"
                    style={{ x: '-50%' }}
                >
                    {children}
                </motion.div>
            )}
        </AnimatePresence>
    );
}

type DockIconProps = {
    className?: string;
    children: React.ReactNode;
};

function DockIcon({ children, className = '' }: DockIconProps) {
    return <div className={`flex items-center justify-center text-xl ${className}`}>{children}</div>;
}

// --- PreferenceFilter Component ---

interface FilterOption {
    id: string;
    label: string;
    icon: string;
}

interface PreferenceFilterProps {
    onFilterChange?: (filters: string[]) => void;
    initialFilters?: string[];
}

const FILTER_OPTIONS: FilterOption[] = [
    { id: 'transport', label: '대중교통', icon: '🚇' },
    { id: 'park', label: '주변 공원', icon: '🌳' },
    { id: 'distance', label: '대학가', icon: '🏢' },
    { id: 'facilities', label: '편의시설', icon: '🏪' },
    { id: 'safety', label: '치안/안전', icon: '⭐' },
    { id: 'fake', label: '허위매물', icon: '🚫' },
];

export default function PreferenceFilter({
    onFilterChange,
    initialFilters = []
}: PreferenceFilterProps) {
    const [selectedFilters, setSelectedFilters] = useState<Set<string>>(
        new Set(initialFilters)
    );

    const mouseX = useMotionValue(Infinity);
    const isHovered = useMotionValue(0);

    // Dock configuration
    const spring = { mass: 0.1, stiffness: 150, damping: 12 };
    const magnification = 60;
    const distance = 140;
    const baseItemSize = 45;
    const panelHeight = 68;
    const dockHeight = 100;

    const maxHeight = useMemo(() => Math.max(dockHeight, magnification + magnification / 2 + 4), [magnification, dockHeight]);
    const heightRow = useTransform(isHovered, [0, 1], [panelHeight, maxHeight]);
    const height = useSpring(heightRow, spring);

    // Particle Effect Logic
    const particleCount = 12;
    const particleDistances: [number, number] = [40, 60];
    const particleR = 30;
    const timeVariance = 200;
    const animationTime = 400;
    const colors = [1, 2, 3, 4]; // We'll map these to CSS vars or specific colors

    const noise = (n = 1) => n / 2 - Math.random() * n;
    const getXY = (distance: number, pointIndex: number, totalPoints: number): [number, number] => {
        const angle = ((360 + noise(8)) / totalPoints) * pointIndex * (Math.PI / 180);
        return [distance * Math.cos(angle), distance * Math.sin(angle)];
    };
    const createParticle = (i: number, t: number, d: [number, number], r: number) => {
        let rotate = noise(r / 10);
        return {
            start: getXY(d[0], particleCount - i, particleCount),
            end: getXY(d[1] + noise(7), particleCount - i, particleCount),
            time: t,
            scale: 1 + noise(0.2),
            color: colors[Math.floor(Math.random() * colors.length)],
            rotate: rotate > 0 ? (rotate + r / 20) * 10 : (rotate - r / 20) * 10
        };
    };

    const makeParticles = (element: HTMLElement) => {
        const d: [number, number] = particleDistances;
        const r = particleR;
        const bubbleTime = animationTime * 2 + timeVariance;
        // element.style.setProperty('--time', `${bubbleTime}ms`); // Not strictly needed on the element itself for this implementation

        for (let i = 0; i < particleCount; i++) {
            const t = animationTime * 2 + noise(timeVariance * 2);
            const p = createParticle(i, t, d, r);

            const particle = document.createElement('span');
            const point = document.createElement('span');
            particle.classList.add('particle');
            particle.style.setProperty('--start-x', `${p.start[0]}px`);
            particle.style.setProperty('--start-y', `${p.start[1]}px`);
            particle.style.setProperty('--end-x', `${p.end[0]}px`);
            particle.style.setProperty('--end-y', `${p.end[1]}px`);
            particle.style.setProperty('--time', `${p.time}ms`);
            particle.style.setProperty('--scale', `${p.scale}`);

            // Map color indices to actual colors
            const colorMap = ['#60A5FA', '#3B82F6', '#93C5FD', '#2563EB']; // Blue shades
            const color = colorMap[p.color - 1] || '#3B82F6';
            particle.style.setProperty('--color', color);

            particle.style.setProperty('--rotate', `${p.rotate}deg`);
            point.classList.add('point');
            particle.appendChild(point);
            element.appendChild(particle);

            setTimeout(() => {
                try {
                    if (element.contains(particle)) {
                        element.removeChild(particle);
                    }
                } catch { }
            }, t);
        }
    };

    const handleFilterClick = (filterId: string, event: React.MouseEvent<HTMLElement>) => {
        const newFilters = new Set(selectedFilters);

        if (newFilters.has(filterId)) {
            newFilters.delete(filterId);
        } else {
            newFilters.add(filterId);
            // Trigger particle effect only on selection
            makeParticles(event.currentTarget as HTMLElement);
        }

        setSelectedFilters(newFilters);
        onFilterChange?.(Array.from(newFilters));
    };

    const handleReset = (event: React.MouseEvent<HTMLElement>) => {
        setSelectedFilters(new Set());
        onFilterChange?.([]);
        // Optional: Trigger effect on reset too
        makeParticles(event.currentTarget as HTMLElement);
    };

    return (
        <>
            <style>
                {`
                    .particle,
                    .point {
                        display: block;
                        opacity: 0;
                        width: 10px;
                        height: 10px;
                        border-radius: 9999px;
                        transform-origin: center;
                        pointer-events: none;
                    }
                    .particle {
                        --time: 600ms;
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        z-index: 50;
                        animation: particle var(--time) ease 1 forwards;
                    }
                    .point {
                        background: var(--color);
                        opacity: 1;
                        width: 100%;
                        height: 100%;
                        animation: point var(--time) ease 1 forwards;
                    }
                    @keyframes particle {
                        0% {
                            transform: translate(-50%, -50%) rotate(0deg) translate(var(--start-x), var(--start-y));
                            opacity: 1;
                        }
                        100% {
                            transform: translate(-50%, -50%) rotate(var(--rotate)) translate(var(--end-x), var(--end-y));
                            opacity: 0;
                        }
                    }
                    @keyframes point {
                        0% { transform: scale(0); }
                        50% { transform: scale(var(--scale)); }
                        100% { transform: scale(0); }
                    }
                `}
            </style>
            <div
                className="flex justify-center w-full py-4"
                style={{ height: maxHeight + 32 }}
            >
                <div className="flex items-end h-full">
                    <motion.div
                        onMouseMove={({ pageX }: { pageX: number }) => {
                            isHovered.set(1);
                            mouseX.set(pageX);
                        }}
                        onMouseLeave={() => {
                            isHovered.set(0);
                            mouseX.set(Infinity);
                        }}
                        className="relative flex items-end w-fit gap-3 rounded-2xl border-white/40 border-2 bg-gradient-to-b from-sky-100/60 to-blue-200/60 backdrop-blur-md pb-2 px-4 shadow-2xl z-40 mx-auto"
                        style={{ height: height }}
                        role="toolbar"
                        aria-label="Filter dock"
                    >
                        {FILTER_OPTIONS.map((option) => (
                            <DockItem
                                key={option.id}
                                onClick={(e: any) => handleFilterClick(option.id, e)}
                                mouseX={mouseX}
                                spring={spring}
                                distance={distance}
                                magnification={magnification}
                                baseItemSize={baseItemSize}
                                isSelected={selectedFilters.has(option.id)}
                                className={`
                                    ${selectedFilters.has(option.id)
                                        ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.6)] ring-2 ring-blue-300'
                                        : 'bg-white/50 border-white/50 text-slate-600 hover:bg-white/80 hover:border-white/80'
                                    }
                                `}
                            >
                                <DockIcon>{option.icon}</DockIcon>
                                <DockLabel>{option.label}</DockLabel>
                            </DockItem>
                        ))}

                        {/* Separator */}
                        <div className="w-[1px] h-8 bg-slate-400/30 mx-1 mb-3" />

                        {/* Reset Button */}
                        <DockItem
                            onClick={(e: any) => handleReset(e)}
                            mouseX={mouseX}
                            spring={spring}
                            distance={distance}
                            magnification={magnification}
                            baseItemSize={baseItemSize}
                            className={selectedFilters.size === 0 ? 'opacity-50 cursor-not-allowed bg-white/30' : 'text-red-500 border-red-200 bg-white/50 hover:bg-white/80'}
                        >
                            <DockIcon>🔄</DockIcon>
                            <DockLabel>초기화</DockLabel>
                        </DockItem>

                    </motion.div>
                </div>
            </div>
        </>
    );
}
