# Frontend - 실행 가이드

Next.js 14 기반 부동산 매물 검색 서비스 프론트엔드입니다.

## 빠른 시작

### 1. 의존성 설치
```bash
cd apps/frontend
npm install
```

### 2. 환경 변수 설정
루트 디렉토리의 `.env` 파일에 다음 필수 항목을 설정하세요:

```env
# 프론트엔드 필수 환경 변수
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_KAKAO_MAP_KEY=your_kakao_map_api_key

# NextAuth (로그인 기능)
NEXTAUTH_SECRET=your_random_secret_key
NEXTAUTH_URL=http://localhost:3000

# Google 로그인 (선택)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

**카카오맵 API 키 발급**: https://developers.kakao.com/

### 3. 개발 서버 실행
```bash
npm run dev
```

브라우저에서 http://localhost:3000 접속

## 주요 명령어

```bash
# 개발 서버 실행 (Hot Reload)
npm run dev

# 프로덕션 빌드
npm run build

# 프로덕션 서버 실행
npm start

# 코드 린트 검사
npm run lint
```

## 기술 스택

- **Next.js 14** (App Router)
- **React 18** + TypeScript
- **Tailwind CSS** (스타일링)
- **Framer Motion** (애니메이션)
- **Zustand** (상태 관리)
- **Axios** (API 통신)
- **NextAuth** (인증)

## 폴더 구조

```
src/
├── app/              # Next.js App Router 페이지
│   ├── main/         # 메인 페이지 (매물 검색)
│   ├── community/    # 커뮤니티
│   ├── landDetail/   # 매물 상세
│   ├── login/        # 로그인
│   ├── my/           # 마이 페이지
│   ├── preferenceSurvey/     # 선호도조사
│   ├── wishList/     # 찜 매물
│   ├── layout.tsx    # 루트 레이아웃
│   ├── page.tsx      # 홈페이지
│   └── globals.css   # 전역 스타일
├── components/       # 재사용 컴포넌트
├── hooks/            # 커스텀 훅
├── lib/              # API 클라이언트
└── store/            # Zustand 스토어
```

## 성능 최적화

- **Dynamic Import**: 무거운 컴포넌트 지연 로딩
- **Image Optimization**: Next.js Image 컴포넌트 사용
- **Code Splitting**: 자동 라우트 기반 분할

## 문제 해결

### 포트가 이미 사용 중인 경우
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# 또는 다른 포트로 실행
npm run dev -- -p 3001
```

### 빌드 에러 발생 시
```bash
# node_modules 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install
```

### 카카오맵이 로드되지 않는 경우
- `.env` 파일에 `NEXT_PUBLIC_KAKAO_MAP_KEY` 확인
- 카카오 개발자 콘솔에서 JavaScript 키 확인
- 도메인 등록 확인 (localhost 등록 필요)

## 배포

프로덕션 빌드 후 배포:
```bash
npm run build
npm start
```

또는 Docker 사용:
```bash
# 루트 디렉토리에서
docker-compose up frontend
```
