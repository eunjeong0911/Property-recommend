/**
 * Button 컴포넌트
 *
 * 앱 전역에서 사용하는 공통 버튼 컴포넌트
 *
 * 주요 기능:
 * - 텍스트, 배경색, 크기 등 다양한 스타일 커스터마이징 가능
 * - 클릭 이벤트 핸들러(onClick) 바인딩
 * - 사용 목적에 따라 '등록', '수정', '삭제', '댓글 등록', '뒤로가기' 등 재사용 가능
 */

'use client'

import { useParticleEffect } from '../hooks/useParticleEffect'

interface ButtonProps {
  children: React.ReactNode
  onClick?: (e?: React.MouseEvent<HTMLButtonElement>) => void
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  fullWidth?: boolean
  type?: 'button' | 'submit' | 'reset'
  className?: string
}

export default function Button({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  fullWidth = false,
  type = 'button',
  className = ''
}: ButtonProps) {
  const { triggerEffect } = useParticleEffect()

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!disabled) {
      triggerEffect(e.currentTarget)
      onClick?.(e)
    }
  }

  // Variant 스타일
  const variantStyles = {
    primary: 'bg-[#16375B] border-[#16375B] text-white shadow-[0_0_15px_rgba(22,55,91,0.6)] ring-2 ring-[#16375B]/30 hover:bg-[#0f2844] disabled:bg-gray-300 disabled:shadow-none disabled:ring-0 disabled:border-transparent',
    secondary: 'bg-white/50 border-white/40 text-slate-600 hover:bg-white/80 hover:border-white/80 border-2 backdrop-blur-sm disabled:bg-gray-100 disabled:text-gray-400 disabled:border-transparent',
    danger: 'bg-red-500 border-red-400 text-white hover:bg-red-600 shadow-[0_0_15px_rgba(239,68,68,0.6)] ring-2 ring-red-300 disabled:bg-gray-300 disabled:shadow-none disabled:ring-0 disabled:border-transparent',
    ghost: 'bg-transparent text-slate-600 hover:bg-white/30 disabled:text-gray-400',
    outline: 'bg-transparent border-2 border-slate-300 text-slate-600 hover:border-slate-400 hover:bg-slate-50 disabled:border-gray-200 disabled:text-gray-400'
  }

  // Size 스타일
  const sizeStyles = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base'
  }

  // Width 스타일
  const widthStyle = fullWidth ? 'w-full' : ''

  return (
    <button
      type={type}
      onClick={handleClick}
      disabled={disabled}
      className={`
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${widthStyle}
        rounded-full font-medium transition-all duration-200
        disabled:cursor-not-allowed
        flex items-center justify-center gap-2
        ${className}
      `}
    >
      {children}
    </button>
  )
}
