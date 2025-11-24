# Frontend - Next.js 14

공개 웹 서비스를 위한 Next.js 14 (App Router) 기반 프론트엔드입니다.

## 기술 스택

- **Next.js 14** (App Router)
- **React 18**
- **TypeScript**
- **Zustand** (상태 관리)
- **Axios** (API 통신)

## 주요 기능

- 매물 검색 및 상세 정보
- AI 기반 매물 추천
- SEO 최적화 (Server-Side Rendering)
- 반응형 디자인

## 폴더 구조

```
src/
├── app/              # Next.js App Router 페이지
│   ├── layout.tsx    # 루트 레이아웃
│   ├── page.tsx      # 홈페이지
│   └── globals.css   # 전역 스타일
├── components/       # 재사용 가능한 UI 컴포넌트
├── lib/             # 유틸리티 및 API 클라이언트
└── store/           # Zustand 상태 관리
```

## 개발 환경 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 프로덕션 실행
npm start
```

## 환경 변수

`.env.local` 파일을 생성하고 다음 변수를 설정하세요:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Docker 실행

```bash
# docker-compose로 전체 스택 실행
docker-compose up frontend
```
