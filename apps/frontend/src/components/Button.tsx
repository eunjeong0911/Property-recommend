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
  // Variant 스타일
  const variantStyles = {
    primary: 'bg-blue-500 text-white hover:bg-blue-600 disabled:bg-gray-300',
    secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:bg-gray-100',
    danger: 'bg-red-500 text-white hover:bg-red-600 disabled:bg-gray-300',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 disabled:text-gray-400',
    outline: 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:bg-gray-100'
  }

  // Size 스타일
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  }

  // Width 스타일
  const widthStyle = fullWidth ? 'w-full' : ''

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${widthStyle}
        rounded-lg font-medium transition-colors
        disabled:cursor-not-allowed
        ${className}
      `}
    >
      {children}
    </button>
  )
}
