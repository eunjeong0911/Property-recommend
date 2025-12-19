# AWS ECS 배포 가이드

## 아키텍처 개요

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                      AWS Cloud                          │
                    │                                                         │
    Internet        │   ┌─────────┐    ┌─────────────────────────────────┐   │
        │           │   │   ALB   │    │         ECS Cluster              │   │
        │           │   │         │    │  ┌─────────┐  ┌─────────┐       │   │
        └───────────┼──►│ :443    │───►│  │ Backend │  │ Frontend│       │   │
                    │   │         │    │  │ Service │  │ Service │       │   │
                    │   └─────────┘    │  └────┬────┘  └─────────┘       │   │
                    │                  │       │                          │   │
                    │                  │  ┌────┴────┐  ┌─────────┐       │   │
                    │                  │  │   RAG   │  │  Reco   │       │   │
                    │                  │  │ Service │  │ Service │       │   │
                    │                  │  └─────────┘  └─────────┘       │   │
                    │                  └─────────────────────────────────┘   │
                    │                                                         │
                    │   ┌─────────────────────────────────────────────────┐   │
                    │   │              Managed Services                    │   │
                    │   │  ┌─────┐  ┌──────┐  ┌────────────┐  ┌────────┐ │   │
                    │   │  │ RDS │  │Neo4j │  │ OpenSearch │  │ElastiC │ │   │
                    │   │  │(PG) │  │Aura  │  │  Service   │  │ ache   │ │   │
                    │   │  └─────┘  └──────┘  └────────────┘  └────────┘ │   │
                    │   └─────────────────────────────────────────────────┘   │
                    └─────────────────────────────────────────────────────────┘
```

## 사전 요구사항

1. AWS CLI 설치 및 구성
2. Docker 설치
3. 도메인 및 SSL 인증서 (ACM)

## 1단계: AWS 리소스 생성

### 1.1 ECR 리포지토리 생성

```bash
# ECR 리포지토리 생성
make ecr-setup
```

### 1.2 Secrets Manager 설정

```bash
# 데이터베이스 시크릿
aws secretsmanager create-secret \
    --name realestate/db \
    --secret-string '{"POSTGRES_DB":"realestate","POSTGRES_USER":"postgres","POSTGRES_PASSWORD":"your-secure-password"}'

# Django 시크릿
aws secretsmanager create-secret \
    --name realestate/django \
    --secret-string '{"DJANGO_SECRET_KEY":"your-django-secret-key"}'

# OpenAI API 키
aws secretsmanager create-secret \
    --name realestate/openai \
    --secret-string '{"OPENAI_API_KEY":"sk-your-openai-key"}'

# NextAuth 시크릿
aws secretsmanager create-secret \
    --name realestate/nextauth \
    --secret-string '{"NEXTAUTH_SECRET":"your-nextauth-secret"}'

# Google OAuth
aws secretsmanager create-secret \
    --name realestate/google \
    --secret-string '{"GOOGLE_CLIENT_ID":"your-client-id","GOOGLE_CLIENT_SECRET":"your-client-secret"}'

# Neo4j
aws secretsmanager create-secret \
    --name realestate/neo4j \
    --secret-string '{"NEO4J_USER":"neo4j","NEO4J_PASSWORD":"your-neo4j-password"}'
```

### 1.3 SSM Parameter Store 설정

```bash
# Kakao Map API Key (공개 키)
aws ssm put-parameter \
    --name /realestate/kakao-map-key \
    --value "your-kakao-map-key" \
    --type String
```

## 2단계: 인프라 서비스 설정

### 2.1 RDS (PostgreSQL with pgvector)

```bash
# RDS 인스턴스 생성 (pgvector 지원)
aws rds create-db-instance \
    --db-instance-identifier realestate-db \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 16.1 \
    --master-username postgres \
    --master-user-password your-password \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxx \
    --db-subnet-group-name your-subnet-group
```

### 2.2 ElastiCache (Redis)

```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id realestate-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1
```

### 2.3 OpenSearch Service

```bash
aws opensearch create-domain \
    --domain-name realestate-search \
    --engine-version OpenSearch_2.11 \
    --cluster-config InstanceType=t3.small.search,InstanceCount=1 \
    --ebs-options EBSEnabled=true,VolumeType=gp3,VolumeSize=20
```

### 2.4 Neo4j Aura (외부 서비스)

Neo4j Aura 콘솔에서 인스턴스 생성 후 연결 정보를 Secrets Manager에 저장

## 3단계: 이미지 빌드 및 푸시

```bash
# ECR 로그인
make ecr-login

# 프로덕션 이미지 빌드 및 푸시
make push IMAGE_TAG=v1.0.0
```

## 4단계: ECS 클러스터 및 서비스 생성

### 4.1 ECS 클러스터 생성

```bash
aws ecs create-cluster --cluster-name realestate-cluster
```

### 4.2 Task Definition 등록

```bash
# 환경 변수 치환 후 등록
envsubst < infra/aws/ecs-task-definition-backend.json | \
    aws ecs register-task-definition --cli-input-json file:///dev/stdin

envsubst < infra/aws/ecs-task-definition-frontend.json | \
    aws ecs register-task-definition --cli-input-json file:///dev/stdin

envsubst < infra/aws/ecs-task-definition-rag.json | \
    aws ecs register-task-definition --cli-input-json file:///dev/stdin
```

### 4.3 서비스 생성

```bash
# Backend 서비스
aws ecs create-service \
    --cluster realestate-cluster \
    --service-name backend-service \
    --task-definition realestate-backend \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000"
```

## 5단계: ALB 설정

### 5.1 Target Groups 생성

- backend-tg: 포트 8000, 헬스체크 `/api/health/`
- frontend-tg: 포트 3000, 헬스체크 `/api/health`
- rag-tg: 포트 8001, 헬스체크 `/health`

### 5.2 리스너 규칙

```
/api/*     → backend-tg
/rag/*     → rag-tg
/reco/*    → reco-tg
/*         → frontend-tg
```

## 6단계: CI/CD 파이프라인 (CodePipeline)

1. CodePipeline 생성
2. Source: GitHub 연결
3. Build: CodeBuild (buildspec.yml 사용)
4. Deploy: ECS 배포

## 모니터링

### CloudWatch 대시보드

- ECS 서비스 메트릭
- ALB 요청/응답 메트릭
- RDS 성능 메트릭
- 애플리케이션 로그

### 알람 설정

```bash
# CPU 사용률 알람
aws cloudwatch put-metric-alarm \
    --alarm-name "ECS-Backend-HighCPU" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2
```

## 비용 최적화 팁

1. **Fargate Spot**: 비프로덕션 환경에서 최대 70% 절감
2. **Auto Scaling**: 트래픽에 따른 자동 스케일링
3. **Reserved Capacity**: 예측 가능한 워크로드에 예약 용량 사용
4. **Right Sizing**: CloudWatch 메트릭 기반 리소스 최적화

## 롤백 절차

```bash
# 이전 Task Definition으로 롤백
aws ecs update-service \
    --cluster realestate-cluster \
    --service backend-service \
    --task-definition realestate-backend:PREVIOUS_REVISION
```

## 트러블슈팅

### 컨테이너 로그 확인

```bash
aws logs get-log-events \
    --log-group-name /ecs/realestate-backend \
    --log-stream-name ecs/backend/TASK_ID
```

### ECS Exec으로 컨테이너 접속

```bash
aws ecs execute-command \
    --cluster realestate-cluster \
    --task TASK_ID \
    --container backend \
    --interactive \
    --command "/bin/bash"
```
