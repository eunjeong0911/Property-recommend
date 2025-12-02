# Real Estate Platform - Django Backend

## 기술 스택

### Backend
- **Django 4.2** - Python 웹 프레임워크
- **Django REST Framework** - RESTful API 구축
- **PostgreSQL + pgvector** - 관계형 데이터베이스 및 벡터 검색
- **Neo4j** - 그래프 데이터베이스 (추천 시스템)
- **Redis** - 캐싱 및 세션 관리
- **JWT Authentication** - JSON Web Token 인증
- **Google OAuth 2.0** - 소셜 로그인
- **Pillow** - 이미지 처리

### Frontend
- **Next.js 14** - React 프레임워크 (App Router)
- **NextAuth.js** - 인증 관리
- **TypeScript** - 타입 안정성
- **Tailwind CSS** - 스타일링

### DevOps
- **Docker & Docker Compose** - 컨테이너화
- **dotenv** - 환경변수 관리

## 📁 프로젝트 구조
```
SKN18-FINAL-1TEAM/
├── apps/
│   ├── backend/                 # Django 백엔드
│   │   ├── apps/
│   │   │   ├── users/          # 사용자 인증 및 이력 관리
│   │   │   ├── community/      # 커뮤니티 기능
│   │   │   ├── listings/       # 매물 관리
│   │   │   ├── recommend/      # 추천 시스템
│   │   │   └── graph/          # Neo4j 그래프 분석
│   │   ├── config/             # Django 설정
│   │   │   ├── settings/
│   │   │   │   ├── base.py    # 기본 설정
│   │   │   │   └── dev.py     # 개발 환경 설정
│   │   │   └── urls.py        # URL 라우팅
│   │   ├── media/             # 업로드된 파일
│   │   ├── manage.py
│   │   └── requirements.txt
│   │
│   └── frontend/               # Next.js 프론트엔드
│       ├── src/
│       │   ├── app/           # 페이지 라우트
│       │   ├── components/    # React 컴포넌트
│       │   ├── lib/          # 유틸리티 (axios 설정 등)
│       │   └── types/        # TypeScript 타입 정의
│       └── package.json
│
├── docker-compose.yml          # Docker 서비스 정의
├── .env                       # 환경변수 설정
└── README.md
```
---

## 환경 설정

### 1. 환경변수 설정 (`.env` 파일)

.env.sample 파일 복사 후 `.env` 파일로 변경해서 내용 입력


### 2. 개발 환경
  - Python 3.11+
  - Node.js 18+
  - PostgreSQL 14+
  - Redis
  - Neo4j
  
---

## 설치 및 실행 

#### Backend

```bash

docker-compose up -d

cd apps/backend

uv pip install -r requirements.txt
uv pip install Pillow

# 마이그레이션 실행
python manage.py makemigrations users community
python manage.py migrate

# 백엔드 실행
python manage.py runserver
```

#### Frontend

```bash
cd apps/frontend

# 패키지 설치
npm install
npm run dev
```

## 구현 & 설계 의도 (전체 Django 기준)

| 도메인 | 설계 의도/구현 내용 |
| --- | --- |
| **인증(Auth)** | NextAuth + Django REST 조합. Google OAuth는 `/api/users/auth/google/` 하나로 사용자 등록/로그인을 처리하고, Credentials 로그인은 동일 토큰 플로우를 사용해 Google로 가입한 사용자도 ID/비밀번호 폼에서 즉시 로그인 가능. 로그인/로그아웃 시 LoginHistory로 IP & User-Agent 추적. |
| **JWT & 세션** | Django에서 access/refresh 토큰을 발급하고 NextAuth session이 이를 받아 저장. 만료 시 refresh 토큰으로 `/api/users/token/refresh/` 호출. Frontend는 axios interceptor가 자동으로 Bearer 토큰을 주입. |
| **프로필 관리** | Google 프로필 이미지를 최초 저장하고, 사용자 업로드 이미지는 `User.profile_image_file` BinaryField에 Base64로 저장. Serializer가 data URI로 내려주므로 정적파일 서버 없이도 프런트가 표시 가능. |
| **사용자 이력** | SearchHistory, ListingViewHistory, WishlistHistory 등 별도 테이블로 구성해 행동 로그를 추적. Mentor가 “왜 이렇게 테이블이 많나?”라고 물으면, 추후 추천/분석에 쓰기 위한 구조이며, 비즈니스 핵심 데이터가 되기 때문이라고 설명할 수 있음. |
| **선호도 조사** | 신규 로그인 시 `is_new_user` + `survey_completed` flag로 설문 흐름을 제어. 설문 제출(`/api/users/preference-survey/`) 시 우선순위를 JSON으로 저장하고, 추천 시스템에 재사용. |
| **커뮤니티 게시판** | `board_type`(자유/행정동)과 `region/dong/complex_name`으로 필터 가능한 구조. Soft Delete(`is_deleted`)를 사용해 데이터 감사가 가능. 조회수는 `F()` 연산으로 증분. |
| **커뮤니티 좋아요** | `CommunityPostLike`로 사용자별 좋아요를 추적하고, `CommunityPost.like_count`를 캐시 필드로 유지. POST/DELETE API가 중복 방지 & 카운트 동기화 담당. |
| **API 일원화** | 프런트는 전부 `/api/**` REST endpoint를 호출. 더 이상 클라이언트 로컬 상태로만 데이터를 조작하지 않아 QA/운영 환경과 동일한 코드를 유지. |
| **왜 이렇게 했는지** | 명확한 API 레이어와 DB 기록을 유지해야 팀 내 다른 개발자나 멘토 검수 시 “데이터는 어디에 근거하나?”라는 질문에 바로 답할 수 있음. 또한 Soft Delete, BinaryField 저장 같은 구조는 Docker 재시작이나 다중 서버 상황에서도 일관성을 확보하기 위한 선택. |

## 주요 기능 요약
- Google 소셜 로그인 + JWT
- 사용자 이력 추적 (로그인/검색/매물/찜)
- 프로필 관리 (이미지 업로드/계정 삭제)
- 선호도 설문 → 추천 시스템 입력값
- 커뮤니티 게시판 (자유/행정동) + 댓글 + 좋아요

## API Snapshot

### 인증 관련
```
POST /api/users/auth/google/
POST /api/users/auth/login/        # email/password
POST /api/users/token/refresh/
POST /api/users/logout/
```

### 사용자 이력
```
GET    /api/users/me/
PATCH  /api/users/me/update/
DELETE /api/users/me/
POST   /api/users/me/profile-image/
GET    /api/users/preference-survey/
POST   /api/users/preference-survey/
GET/POST /api/users/history/search/
POST   /api/users/history/view/
```

### 찜 목록
```
GET    /api/users/wishlist/
POST   /api/users/wishlist/
DELETE /api/users/wishlist/<listing_id>/
```

### 커뮤니티
```
GET    /api/community/posts/?board=free|region&region=&dong=&complex_name=
POST   /api/community/posts/
GET    /api/community/posts/<id>/
PATCH  /api/community/posts/<id>/
DELETE /api/community/posts/<id>/
POST   /api/community/posts/<id>/comments/
POST   /api/community/posts/<id>/like/
DELETE /api/community/posts/<id>/like/
```

## 데이터베이스 개요

### Users App
- `User`: Google OAuth 정보, 상태 플래그, 프로필 이미지(BinaryField)
- `LoginHistory`: 로그인/로그아웃 로그
- `SearchHistory`, `ListingViewHistory`: 검색/매물 행동 로그
- `Wishlist`, `WishlistHistory`: 찜 상태 + 이력
- `PreferenceSurvey`: 사용자 우선순위 JSON 저장

### Community App
- `CommunityPost`: 게시판 종류/지역 필드, Soft Delete, 조회수/좋아요 수
- `CommunityComment`: 댓글 (Soft Delete)
- `CommunityPostLike`: 사용자-게시글 좋아요 관계 (중복 방지)

## Troubleshooting
- **Migration error**: `python manage.py showmigrations` → 잘못된 항목은 `--fake` 초기화 후 재적용.
- **Docker 서비스 재시작**: `docker-compose down && docker-compose up -d`
- **프론트 빌드 캐시**: `rm -rf .next && npm run dev`

## 로그인 Flow 요약
```
1. 사용자가 "로그인" 버튼 클릭
   ↓
2. Google OAuth 로그인 페이지로 리다이렉트
   ↓
3. 구글 계정 선택 및 인증
   ↓
4. Django 백엔드 API 호출 (POST /api/users/auth/google/)
   - 신규 사용자: 사용자 생성 (is_new_user=True)
   - 기존 사용자: 사용자 정보 업데이트
   - JWT 토큰 발급 (access + refresh)
   - 로그인 이력 저장
   ↓
5. NextAuth 세션 생성 (토큰 저장)
   ↓
6. 자동 리다이렉트
   - 신규 사용자 (is_new_user=True, survey_completed=False)
     → /preferenceSurvey (선호도 조사 페이지)
   - 기존 사용자 또는 설문 완료
     → /main (메인 페이지)
   ↓
7. 선호도 조사 제출 (신규 사용자만)
   - POST /api/users/preference-survey/
   - job_type 및 priorities 저장
   - is_new_user=False, survey_completed=True 업데이트
   ↓
8. /main 페이지로 리다이렉트
   ↓
9. 헤더 버튼: "로그인" → "마이페이지"로 변경
```