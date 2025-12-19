# AWS 배포 전 체크리스트

## ✅ 완료된 설정

### Docker 최적화
- [x] Multi-stage 빌드 적용 (backend, rag, reco, frontend)
- [x] Non-root 사용자 실행
- [x] 서비스별 requirements.txt 분리
- [x] Health check 엔드포인트 내장
- [x] .dockerignore 최적화

### ECS/Fargate 준비
- [x] Task Definition 템플릿 (backend, rag, frontend)
- [x] Secrets Manager 연동 설정
- [x] CloudWatch Logs 설정
- [x] Health check 설정

### 네트워크/보안
- [x] ALB Target Group 설정 가이드
- [x] CloudFront Behavior 분리 설정
- [x] CORS 설정 (환경변수 기반)
- [x] Django 프로덕션 보안 설정 (HTTPS, HSTS, Cookie)

### 로깅
- [x] JSON 로깅 포맷 (CloudWatch 호환)
- [x] 환경변수 기반 로그 레벨 설정

---

## 🔧 AWS 콘솔에서 수동 설정 필요

### 1. Secrets Manager 시크릿 생성
```bash
# 필수 시크릿 목록
realestate/db          # POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
realestate/django      # DJANGO_SECRET_KEY
realestate/openai      # OPENAI_API_KEY
realestate/nextauth    # NEXTAUTH_SECRET
realestate/google      # GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
realestate/neo4j       # NEO4J_USER, NEO4J_PASSWORD
```

### 2. SSM Parameter Store
```bash
/realestate/kakao-map-key   # Kakao Map API Key (공개 키)
```

### 3. ECR 리포지토리 생성
```bash
make ecr-setup
# 또는
./infra/aws/ecr-setup.sh ap-northeast-2
```

### 4. VPC 및 서브넷
- [ ] VPC 생성 (또는 기존 VPC 사용)
- [ ] Public 서브넷 2개 이상 (ALB용)
- [ ] Private 서브넷 2개 이상 (ECS 태스크용)
- [ ] NAT Gateway (Private 서브넷 인터넷 접근용)

### 5. 보안 그룹
- [ ] ALB 보안 그룹: 80, 443 인바운드
- [ ] ECS 보안 그룹: ALB에서만 접근 허용
- [ ] RDS 보안 그룹: ECS에서만 접근 허용
- [ ] ElastiCache 보안 그룹: ECS에서만 접근 허용
- [ ] OpenSearch 보안 그룹: ECS에서만 접근 허용

### 6. RDS (PostgreSQL + pgvector)
- [ ] RDS 인스턴스 생성 (db.t3.medium 이상)
- [ ] PostgreSQL 16.x 선택
- [ ] pgvector 확장 활성화
- [ ] 초기 데이터 마이그레이션

### 7. ElastiCache (Redis)
- [ ] Redis 클러스터 생성
- [ ] 엔드포인트 확인

### 8. OpenSearch Service
- [ ] 도메인 생성
- [ ] 인덱스 매핑 적용 (`infra/opensearch/mappings/`)
- [ ] 초기 데이터 인덱싱

### 9. Neo4j (Aura 또는 EC2)
- [ ] Neo4j Aura 인스턴스 생성 또는 EC2 설치
- [ ] 연결 정보 Secrets Manager에 저장
- [ ] 초기 그래프 데이터 적재

### 10. ALB 설정
- [ ] Application Load Balancer 생성
- [ ] Target Groups 생성 (frontend, backend, rag)
- [ ] 리스너 규칙 설정 (path-based routing)
- [ ] idle_timeout: 300초 (RAG 스트리밍용)

### 11. CloudFront 설정
- [ ] Distribution 생성
- [ ] Origin: ALB
- [ ] Behavior 분리 설정 (`infra/aws/cloudfront-config.json` 참조)
- [ ] WAF 연결 (선택)

### 12. Route 53
- [ ] 도메인 등록/이전
- [ ] CloudFront 연결 (A 레코드, Alias)

### 13. ACM (SSL 인증서)
- [ ] 인증서 요청 (us-east-1 리전 - CloudFront용)
- [ ] 도메인 검증

### 14. ECS 클러스터 및 서비스
- [ ] ECS 클러스터 생성
- [ ] Task Definition 등록
- [ ] 서비스 생성 (frontend, backend, rag)
- [ ] Auto Scaling 설정

### 15. IAM 역할
- [ ] ecsTaskExecutionRole (ECR, Secrets Manager, CloudWatch 접근)
- [ ] ecsTaskRole (S3, 기타 AWS 서비스 접근)

---

## 📋 배포 순서

1. **인프라 서비스 먼저**
   - VPC, 서브넷, 보안 그룹
   - RDS, ElastiCache, OpenSearch
   - Neo4j (Aura 또는 EC2)

2. **데이터 마이그레이션**
   - PostgreSQL 스키마 및 데이터
   - OpenSearch 인덱스 및 데이터
   - Neo4j 그래프 데이터

3. **컨테이너 배포**
   - ECR에 이미지 푸시
   - ECS 서비스 생성

4. **네트워크 설정**
   - ALB 설정
   - CloudFront 설정
   - Route 53 DNS 설정

5. **검증**
   - Health check 확인
   - 기능 테스트
   - 성능 테스트

---

## 💰 예상 비용 (월간, ap-northeast-2 기준)

| 서비스 | 스펙 | 예상 비용 |
|--------|------|----------|
| ECS Fargate (frontend) | 0.25 vCPU, 0.5GB x 2 | ~$15 |
| ECS Fargate (backend) | 0.5 vCPU, 1GB x 2 | ~$30 |
| ECS Fargate (rag) | 1 vCPU, 2GB x 2 | ~$60 |
| RDS PostgreSQL | db.t3.medium | ~$50 |
| ElastiCache Redis | cache.t3.micro | ~$15 |
| OpenSearch | t3.small.search | ~$40 |
| ALB | - | ~$20 |
| CloudFront | 100GB 전송 | ~$10 |
| NAT Gateway | - | ~$35 |
| **합계** | | **~$275/월** |

*Neo4j Aura 별도 (Free tier 또는 $65/월~)*

---

## 🚨 주의사항

1. **환경 변수 검증**: 배포 전 모든 필수 환경 변수가 설정되었는지 확인
2. **데이터 백업**: 마이그레이션 전 기존 데이터 백업
3. **롤백 계획**: 문제 발생 시 이전 버전으로 롤백할 수 있도록 준비
4. **모니터링**: CloudWatch 알람 설정 (CPU, 메모리, 에러율)
5. **비용 알림**: AWS Budgets 설정으로 비용 초과 방지
