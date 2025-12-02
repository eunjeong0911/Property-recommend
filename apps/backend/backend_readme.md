# Real Estate Platform - Django Backend

## 🛠 기술 스택

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

## ⚙️ 환경 설정

### 1. 환경변수 설정 (`.env` 파일)

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력합니다:

```env
# Database
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=
NEO4J_PASSWORD=
NEO4J_AUTH=

# OpenAI (선택사항)
OPENAI_API_KEY=your_openai_api_key

# Django
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Redis
REDIS_URL=redis://localhost:6379/0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Google OAuth (Google Cloud Console에서 발급)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# NextAuth
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=http://localhost:3000

# 카카오 지도 API
NEXT_PUBLIC_KAKAO_MAP_KEY=your_kakao_map_key
```

### 2. Google OAuth 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. **API 및 서비스 > 사용자 인증 정보** 메뉴로 이동
4. **OAuth 2.0 클라이언트 ID** 생성
5. 승인된 리디렉션 URI 추가:
   - `http://localhost:3000/api/auth/callback/google`
6. 발급받은 클라이언트 ID와 시크릿을 `.env`에 추가

## 🚀 설치 방법

### 1. 필수 요구사항

- **Docker & Docker Compose** (권장)
- 또는 로컬 개발 환경:
  - Python 3.11+
  - Node.js 18+
  - PostgreSQL 14+
  - Redis
  - Neo4j

## 설치 및 실행 방법
#### Backend

```bash

docker-compose up -d

cd apps/backend

uv pip install -r requirements.txt
uv pip install Pillow

# 마이그레이션 실행
python manage.py makemigrations
python manage.py migrate

# 개발 서버 실행
python manage.py runserver
```

#### Frontend

```bash
cd apps/frontend

# 패키지 설치
npm install
npm run dev

```

```

**접속 URL:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Django Admin: http://localhost:8000/admin


### 3. 서비스 상태 확인

```bash
# Docker 컨테이너 상태 확인
docker ps

# 백엔드 로그 확인
docker logs skn18-final-1team-backend-1

# 데이터베이스 접속 확인
docker exec -it skn18-final-1team-postgres-1 psql -U postgres -d realestate
```

## ✨ 주요 기능

### 1. 구글 소셜 로그인
- Google OAuth 2.0 기반 간편 로그인
- JWT 토큰 발급 및 자동 갱신
- 신규 사용자 자동 생성
- 로그인 성공 시 선호도 조사 → 메인 페이지 자동 리다이렉트

### 2. 사용자 이력 추적
- 로그인/로그아웃 이력
- 검색 조건 이력
- 매물 조회 이력
- 찜 목록 관리 (추가/삭제 이력 포함)
- 선호도 설문 조사

### 3. 프로필 관리
- 구글 프로필 이미지 자동 가져오기
- 사용자 커스텀 프로필 이미지 업로드
- 프로필 정보 수정
- 계정 삭제

### 4. 커뮤니티
- 게시글 작성/조회/수정/삭제 (Soft Delete)
- 댓글 기능
- 조회수 추적

## 📡 API 엔드포인트

### 인증 관련
```
POST   /api/users/auth/google/          # 구글 로그인
POST   /api/users/token/refresh/        # JWT 토큰 갱신
POST   /api/users/logout/               # 로그아웃
```

### 사용자 정보
```
GET    /api/users/me/                   # 현재 사용자 정보 조회
DELETE /api/users/me/                   # 계정 삭제
PATCH  /api/users/me/update/            # 사용자 정보 수정
POST   /api/users/me/profile-image/     # 프로필 이미지 업로드
```

### 선호도 설문
```
GET    /api/users/preference-survey/    # 설문 정보 조회
POST   /api/users/preference-survey/    # 설문 제출
```

### 사용자 이력
```
GET    /api/users/history/search/       # 검색 이력 조회
POST   /api/users/history/search/       # 검색 이력 저장
POST   /api/users/history/view/         # 매물 조회 이력 저장
```

### 찜 목록
```
GET    /api/users/wishlist/             # 찜 목록 조회
POST   /api/users/wishlist/             # 찜 추가
DELETE /api/users/wishlist/<id>/        # 찜 삭제
```

### 커뮤니티
```
GET    /api/community/posts/            # 게시글 목록
POST   /api/community/posts/            # 게시글 작성
GET    /api/community/posts/<id>/       # 게시글 상세
PUT    /api/community/posts/<id>/       # 게시글 수정
DELETE /api/community/posts/<id>/       # 게시글 삭제 (Soft Delete)
```

## 🗄️ 데이터베이스 구조

### Users App

#### User (사용자)
- 구글 OAuth 정보 (`google_id`, `profile_image`)
- 사용자 상태 (`is_new_user`, `survey_completed`)
- 선호도 정보 (`job_type`)
- 프로필 이미지 (`profile_image_file`)

#### LoginHistory (로그인 이력)
- 사용자, 액션(login/logout), IP, User-Agent, 시간

#### SearchHistory (검색 이력)
- 사용자, 검색 조건(JSON), 결과 개수, 시간

#### ListingViewHistory (매물 조회 이력)
- 사용자, 매물 ID, 조회 시간, 스크롤 깊이

#### Wishlist (찜 목록)
- 사용자, 매물 ID, 메모, 생성/수정 시간

#### WishlistHistory (찜 이력)
- 사용자, 매물 ID, 액션(add/remove), 시간

#### PreferenceSurvey (선호도 설문)
- 사용자, 우선순위(JSON), 시간

### Community App

#### CommunityPost (게시글)
- 사용자, 제목, 내용, 조회수
- Soft Delete (`is_deleted`)

#### CommunityComment (댓글)
- 게시글, 사용자, 내용
- Soft Delete (`is_deleted`)

## 🔧 주요 설정 파일

### Django Settings (`apps/backend/config/settings/base.py`)

```python
# 사용자 모델
AUTH_USER_MODEL = "users.User"

# JWT 설정
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# CORS 설정
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
CORS_ALLOW_CREDENTIALS = True

# Media 파일
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

### Docker Compose (`docker-compose.yml`)

주요 서비스:
- **postgres**: PostgreSQL 14 + pgvector
- **neo4j**: Neo4j 5.x
- **redis**: Redis 7.x
- **backend**: Django 애플리케이션

## 🐛 문제 해결

### 1. 마이그레이션 오류

```bash
# 마이그레이션 초기화
docker exec skn18-final-1team-backend-1 python manage.py migrate --fake
docker exec skn18-final-1team-backend-1 python manage.py makemigrations
docker exec skn18-final-1team-backend-1 python manage.py migrate
```

### 2. Docker 컨테이너 재시작

```bash
docker-compose down
docker-compose up -d
```

### 3. 백엔드 컨테이너 접속

```bash
docker exec -it skn18-final-1team-backend-1 bash
```

### 4. 데이터베이스 초기화

```bash
docker-compose down -v  # 볼륨 삭제
docker-compose up -d
# 마이그레이션 재실행
```

### 5. Next.js 빌드 캐시 문제

```bash
cd apps/frontend
rm -rf .next
npm run dev
```

## 📝 개발 참고사항

### 새로운 앱 추가 시

1. Django 앱 생성
```bash
docker exec skn18-final-1team-backend-1 python manage.py startapp <app_name> apps/<app_name>
```

2. `INSTALLED_APPS`에 추가
```python
INSTALLED_APPS = [
    ...
    'apps.<app_name>',
]
```

3. 모델 생성 후 마이그레이션
```bash
docker exec skn18-final-1team-backend-1 python manage.py makemigrations
docker exec skn18-final-1team-backend-1 python manage.py migrate
```

### API 테스트

#### cURL 예제
```bash
# 구글 로그인
curl -X POST http://localhost:8000/api/users/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "User Name",
    "googleId": "google_user_id"
  }'

# JWT 토큰 포함 요청
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer <access_token>"

# 프로필 이미지 업로드
curl -X POST http://localhost:8000/api/users/me/profile-image/ \
  -H "Authorization: Bearer <access_token>" \
  -F "profile_image=@/path/to/image.jpg"
```

## 🎯 로그인 흐름

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