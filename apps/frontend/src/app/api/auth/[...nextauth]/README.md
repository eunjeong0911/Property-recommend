# Catch-all Segments (`[...nextauth]`)

이 폴더 이름에 있는 `[...]` 문법은 Next.js의 **Catch-all Segments (모든 경로 잡기)** 기능입니다.

## ❓ 왜 이렇게 만들었나요?
NextAuth.js는 로그인/로그아웃 처리를 위해 **여러 개의 URL**을 혼자서 처리해야 합니다.
- `/api/auth/signin` (로그인)
- `/api/auth/signout` (로그아웃)
- `/api/auth/callback/google` (구글 로그인 후 복귀)
- `/api/auth/session` (세션 확인)
- ... 등등

이 모든 경로에 대해 일일이 파일을 만드는 대신, **"`/api/auth/` 뒤에 무엇이 오든 이 폴더의 `route.ts`가 다 처리하겠다!"** 라고 선언한 것입니다.

## 📝 문법 설명
- **`[]` (대괄호)**: Dynamic Route (변수처럼 변하는 경로)
- **`...` (점 3개)**: Catch-all (뒤에 오는 모든 경로를 포함)

덕분에 파일 하나(`route.ts`)로 복잡한 로그인 관련 라우팅을 한 번에 해결할 수 있습니다.
