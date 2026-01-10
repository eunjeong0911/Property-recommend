# AWS ETL Pipeline - 부동산 데이터 자동화 파이프라인

## 📌 개요

서울 전역 부동산 매물 데이터를 **매일 자동으로 크롤링**하고, AI 기반 전처리를 거쳐 **PostgreSQL, Neo4j, Elasticsearch**에 저장하는 완전 자동화 ETL 파이프라인입니다.

**핵심 기능:**
- ⏰ 매일 12:00 KST 자동 실행
- 🚀 5개 구역 병렬 크롤링 (서울 25개 구)
- 🤖 OpenAI 기반 검색 텍스트 생성
- 💾 다중 데이터베이스 동시 적재
- 📊 ML 모델 자동 적용 (가격 분류, 중개사 신뢰도)

---

## 🏗️ 아키텍처

```
EventBridge (12:00 KST)
  ↓
Step Functions
  ├─ 5개 병렬 크롤링 Task (ECS Fargate)
  │  ├─ 강남권: 강남구, 서초구, 송파구, 강동구
  │  ├─ 중구권: 중구, 종로구, 용산구, 성동구, 동대문구
  │  ├─ 성북권: 성북구, 강북구, 도봉구, 노원구, 중랑구
  │  ├─ 마포권: 마포구, 서대문구, 은평구, 영등포구, 구로구
  │  └─ 금천권: 금천구, 관악구, 동작구, 양천구, 강서구
  ↓
S3 (data/RDB/land/*.json)
  ↓
ETL Task (ECS Fargate)
  ├─ S3 다운로드
  ├─ PostgreSQL Import
  ├─ Neo4j Import
  ├─ Elasticsearch Import
  ├─ 가격 분류 모델
  └─ 중개사 신뢰도 모델
  ↓
SNS 알림 (성공/실패)
```

---

## 📋 AWS 리소스

| 리소스 | 이름 | 용도 |
|-------|------|------|
| S3 Bucket | `realestate-data-{account-id}` | 크롤링 데이터 저장 |
| Secrets Manager | `realestate/db-credentials` | DB 접속 정보, API 키 |
| ECR Repository | `realestate-scripts` | Docker 이미지 |
| ECS Cluster | `realestate-cluster` | Fargate 클러스터 |
| Task Definition | `realestate-crawl-task` | 크롤링 Task |
| Task Definition | `realestate-etl-task` | Import/모델 Task |
| Step Functions | `realestate-etl-pipeline` | 워크플로우 |
| EventBridge Rule | `realestate-daily-schedule` | 일일 스케줄 |
| SNS Topic | `realestate-etl-notifications` | 알림 |

---

## 🚀 빠른 시작

### 1. Docker 이미지 빌드 및 푸시

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin {account-id}.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 빌드
docker build -f infra/docker/scripts.Dockerfile -t realestate-scripts .

# 태그 및 푸시
docker tag realestate-scripts:latest {account-id}.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-scripts:latest
docker push {account-id}.dkr.ecr.ap-northeast-2.amazonaws.com/realestate-scripts:latest
```

### 2. Step Functions 수동 실행

**AWS 콘솔:**
1. **Step Functions** → `realestate-etl-pipeline`
2. **Start execution**
3. **Input**: `{}`

### 3. 로그 확인

```bash
# 크롤링 Task 로그
aws logs tail /ecs/realestate-crawl-task --since 1h --region ap-northeast-2

# ETL Task 로그
aws logs tail /ecs/realestate-etl-task --since 1h --region ap-northeast-2
```

---

## 📊 실행 흐름

### Phase 1: 병렬 크롤링 (5~10분)

각 Task는 다음을 수행합니다:
1. **Playwright 크롤링** - 피터팬 매물 데이터 수집
2. **OpenAI 전처리** - 검색 텍스트 생성
3. **S3 업로드** - `s3://realestate-data-{account-id}/data/RDB/land/`

### Phase 2: ETL Pipeline (10~20분)

1. **S3 다운로드** - 크롤링된 데이터 가져오기
2. **DB Import**:
   - PostgreSQL: 매물 데이터, 중개사 정보
   - Neo4j: 관계 데이터 (매물-지하철, 매물-학교)
   - Elasticsearch: 검색 인덱스
3. **ML 모델 적용**:
   - 가격 분류 모델 (저가/적정/고가)
   - 중개사 신뢰도 평가 (Gold/Silver/Bronze)

---

## 🔧 환경 변수

### realestate-crawl-task

```bash
ENABLE_CRAWLING=true
ENABLE_PREPROCESSING=true
UPLOAD_TO_S3=true
S3_BUCKET=realestate-data-{account-id}
S3_PREFIX=data/
AWS_REGION=ap-northeast-2
HEADLESS_MODE=true
CRAWL_GROUP=1  # 1~5 (Step Functions에서 Override)
```

### realestate-etl-task

```bash
DOWNLOAD_FROM_S3=true
S3_BUCKET=realestate-data-{account-id}
S3_PREFIX=data/
AWS_REGION=ap-northeast-2
```

**Secrets (Secrets Manager):**
- `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`
- `OPENAI_API_KEY`, `KAKAO_API_KEY`, `VWORLD_API_KEY`

---

## 📁 프로젝트 구조

```
SKN18-FINAL-1TEAM/
├── infra/
│   ├── docker/
│   │   └── scripts.Dockerfile          # ECS Task용 Docker 이미지
│   └── AWS_ETL_README.md               # 이 파일
├── scripts/
│   ├── 01_crawling/
│   │   └── peterpan/
│   │       └── crawl_seoul.py          # 크롤링 스크립트
│   ├── 02_preprocessing/
│   │   └── generate_search_text_parallel.py  # OpenAI 전처리
│   ├── 03_import/
│   │   ├── import_all.py               # 통합 Import
│   │   ├── postgres/                   # PostgreSQL Importer
│   │   ├── neo4j/                      # Neo4j Importer
│   │   └── elasticsearch/              # Elasticsearch Importer
│   ├── download_from_s3.py             # S3 다운로드
│   ├── upload_to_s3.py                 # S3 업로드
│   └── run_all.py                      # 메인 실행 스크립트
└── data/                               # 로컬 데이터 (Docker 볼륨)
```

---

## 🧪 테스트

### 로컬 테스트

```bash
# 가상환경 활성화
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 환경 변수 설정
export DOWNLOAD_FROM_S3=false
export ENABLE_CRAWLING=true
export ENABLE_PREPROCESSING=true

# 실행
python scripts/run_all.py
```

### AWS 테스트

```bash
# Step Functions 실행
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:ap-northeast-2:{account-id}:stateMachine:realestate-etl-pipeline \
  --region ap-northeast-2

# 실행 상태 확인
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:ap-northeast-2:{account-id}:stateMachine:realestate-etl-pipeline \
  --region ap-northeast-2
```

---

## 💰 예상 비용

**매일 1회 실행 기준 (월간):**

| 서비스 | 비용 |
|-------|------|
| ECS Fargate (크롤링 5개) | ~$15 |
| ECS Fargate (ETL 1개) | ~$6 |
| S3 Storage (~10GB) | ~$0.23 |
| CloudWatch Logs | ~$2.50 |
| Step Functions | ~$0.03 |
| **합계** | **~$24/월** |

---

## 🔍 모니터링

### CloudWatch Logs

- `/ecs/realestate-crawl-task` - 크롤링 로그
- `/ecs/realestate-etl-task` - ETL 로그

### Step Functions

- **AWS 콘솔** → **Step Functions** → `realestate-etl-pipeline`
- **Graph inspector**에서 각 State 실행 상태 확인

### SNS 알림

- 성공 시: `✅ ETL Pipeline Success`
- 실패 시: `❌ ETL Pipeline Failed` (에러 상세 포함)

---

## 🛠️ 트러블슈팅

### Task가 시작되지 않음

**원인:** IAM Role 권한 부족

**해결:**
```bash
aws iam list-attached-role-policies --role-name RealEstateStepFunctionsRole
```

### Page crashed (크롤링 실패)

**원인:** 메모리 부족, remobile 리다이렉트

**해결:**
- Task 메모리 증가 (4GB → 8GB)
- CloudWatch Logs에서 `/tmp/debug/*.html` 확인

### Secrets Manager 접근 실패

**원인:** Task Execution Role에 권한 없음

**해결:** `secretsmanager:GetSecretValue` 권한 추가

---