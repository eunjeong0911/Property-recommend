/**
 * LoadingSpinner 컴포넌트
 *
 * 전체 사이트에서 사용하는 통일된 로딩 화면
 *
 * 주요 기능:
 * - 스피너 애니메이션
 * - 로딩 메시지
 * - 일관된 디자인
 */

'use client'

interface LoadingSpinnerProps {
    message?: string
    fullPage?: boolean
}

export default function LoadingSpinner({
    message = '로딩 중...',
    fullPage = false
}: LoadingSpinnerProps) {
    if (fullPage) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#F0F8FF]">
                <div className="text-center">
                    {/* 스피너 */}
                    <div className="relative w-16 h-16 mx-auto mb-4">
                        <div className="absolute inset-0 border-4 border-[#16375B]/20 rounded-full"></div>
                        <div className="absolute inset-0 border-4 border-transparent border-t-[#16375B] rounded-full animate-spin"></div>
                    </div>
                    {/* 메시지 */}
                    <p className="text-slate-600 font-medium">{message}</p>
                </div>
            </div>
        )
    }

    return (
        <div className="bg-white rounded-2xl shadow-sm p-12 text-center min-h-[500px] flex flex-col items-center justify-center">
            {/* 스피너 */}
            <div className="relative w-16 h-16 mx-auto mb-6">
                <div className="absolute inset-0 border-4 border-[#16375B]/20 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-transparent border-t-[#16375B] rounded-full animate-spin"></div>
            </div>
            {/* 메시지 */}
            <p className="text-slate-600 font-medium text-lg">{message}</p>
        </div>
    )
}
