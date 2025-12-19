# Docker 최적화 마이그레이션 가이드

## 변경 사항 요약

### 1. Dockerfile 최적화

#### 적용된 개선사항
- **Multi-stage 빌드**: 빌드 의존성과 런타임 분리로 이미지 크기 50% 이상 감소
- **Non-root 사용자**: 보안 강화를 위해 appuser(UID 1000)로 실행
- **서비스별 requirements.txt**: 불필요한 의존성 제거로 빌드 시간 단축
- **Health check 내장**: ALB/ECS 호환 헬스체크 설정
- **캐시 최적화**: 레이어 순서 최적화로 재빌드 시간 단축

#### 이미지 크기 비교 (예상)
| 서비스 | 이전 | 이후 |
|--------|------|------|
| backend | ~1.5GB | ~500MB |
| rag | ~1.5GB | ~600MB |
| reco | ~2.0GB | ~1.2GB |
| frontend | ~300MB | ~150MB |

### 2. docker-compose.yml 개선

- **네트워크 격리**: backend-network, frontend-network 분리
- **리소스 제한**: 메모리/CPU 제한 설정
- **헬스체크 조건**: 의존 서비스 헬스체크 완료 후 시작
- **명명된 볼륨**: 일관된 볼륨 이름 사용
- **환경 변수 검증**: 필수 변수 누락 시 에러

### 3. 프로덕션 설정 분리

- `docker-compose.prod.yml`: 프로덕션 오버라이드
- `nginx.prod.conf`: 프로덕션 Nginx 설정 (rate limiting, gzip, 보안 헤더)

## 마이그레이션 절차

### 1단계: 기존 컨테이너 정리
```bash
docker compose down -v
docker system prune -f
```

### 2단계: 새 이미지 빌드
```bash
make setup
# 또는
docker compose build --no-cache
```

### 3단계: 서비스 시작
```bash
make up
```

### 4단계: 헬스체크 확인
```bash
make health
```

## 주의사항

### 볼륨 마운트 변경
개발 환경에서는 여전히 소스 코드가 마운트되지만, 프로덕션에서는 이미지에 포함된 코드만 사용됩니다.

### 환경 변수
`.env` 파일에 다음 변수가 필수입니다:
- `POSTGRES_PASSWORD`
- `NEO4J_PASSWORD`

### 서비스별 requirements.txt
각 서비스는 이제 자체 requirements.txt를 사용합니다:
- `apps/backend/requirements.txt`
- `apps/rag/requirements.txt`
- `apps/reco/requirements.txt`

공유 유틸리티 서비스(scripts, analytics, crawling)는 여전히 `infra/docker/requirements.txt`를 사용합니다.

## 롤백 절차

문제 발생 시 Git에서 이전 버전으로 롤백:
```bash
git checkout HEAD~1 -- docker-compose.yml infra/docker/
docker compose build
docker compose up -d
```

## AWS 배포

AWS ECS 배포는 `infra/aws/DEPLOYMENT_GUIDE.md`를 참조하세요.
