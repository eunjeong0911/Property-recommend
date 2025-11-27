/**
 * Login 컴포넌트
 * 
 * 사용자 로그인 폼 컴포넌트
 */
export default function Login() {
    return (
        <div className="w-full max-w-md p-6 bg-white rounded-lg shadow-md">
            <h2 className="mb-4 text-2xl font-bold text-center">로그인</h2>
            <form className="space-y-4">
                <div>
                    <label className="block mb-1 text-sm font-medium text-gray-700">이메일</label>
                    <input
                        type="email"
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="example@email.com"
                    />
                </div>
                <div>
                    <label className="block mb-1 text-sm font-medium text-gray-700">비밀번호</label>
                    <input
                        type="password"
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="********"
                    />
                </div>
                <button
                    type="submit"
                    className="w-full px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                    로그인
                </button>
            </form>
        </div>
    );
}
