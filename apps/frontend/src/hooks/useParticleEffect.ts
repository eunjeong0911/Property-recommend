import { useEffect } from 'react';

export const useParticleEffect = () => {
    // Inject styles once
    useEffect(() => {
        const styleId = 'particle-effect-styles';
        if (!document.getElementById(styleId)) {
            const style = document.createElement('style');
            style.id = styleId;
            style.innerHTML = `
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
                    z-index: 9999; /* High z-index to show above everything */
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
            `;
            document.head.appendChild(style);
        }
    }, []);

    const triggerEffect = (element: HTMLElement) => {
        const particleCount = 12;
        const particleDistances: [number, number] = [40, 60];
        const particleR = 30;
        const timeVariance = 200;
        const animationTime = 400;
        const colors = [1, 2, 3, 4];

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

        const d: [number, number] = particleDistances;
        const r = particleR;

        for (let i = 0; i < particleCount; i++) {
            const t = animationTime * 2 + noise(timeVariance * 2);
            const p = createParticle(i, t, d, r);

            const particle = document.createElement('span');
            const point = document.createElement('span');
            particle.classList.add('particle');

            // Calculate relative position if needed, but here we append to the element
            // If the element has overflow hidden, this might be cut off.
            // Ideally, we append to body and position absolutely based on rect, 
            // but for simplicity and context (like inside a button), appending to element is easier if it's relative.
            // However, to avoid overflow issues (z-index), appending to body is safer.
            // Let's try appending to the element first as per original implementation, 
            // but ensure the element has 'relative' position.

            particle.style.setProperty('--start-x', `${p.start[0]}px`);
            particle.style.setProperty('--start-y', `${p.start[1]}px`);
            particle.style.setProperty('--end-x', `${p.end[0]}px`);
            particle.style.setProperty('--end-y', `${p.end[1]}px`);
            particle.style.setProperty('--time', `${p.time}ms`);
            particle.style.setProperty('--scale', `${p.scale}`);

            const colorMap = ['#60A5FA', '#3B82F6', '#93C5FD', '#2563EB'];
            const color = colorMap[p.color - 1] || '#3B82F6';
            particle.style.setProperty('--color', color);

            particle.style.setProperty('--rotate', `${p.rotate}deg`);
            point.classList.add('point');
            particle.appendChild(point);

            // Ensure the parent is positioned relative so particles are positioned correctly
            const computedStyle = window.getComputedStyle(element);
            if (computedStyle.position === 'static') {
                element.style.position = 'relative';
            }

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

    return { triggerEffect };
};
