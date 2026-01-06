#!/bin/bash

# =============================================================================
# AWS Parameter Store 환경 변수 설정 스크립트
# =============================================================================
# 이 스크립트는 .env.production의 환경 변수들을 AWS Parameter Store에 저장합니다.
# 
# 사용법:
#   chmod +x scripts/deployment/setup_parameters.sh
#   ./scripts/deployment/setup_parameters.sh
# =============================================================================

set -e

# 설정
REGION="ap-northeast-2"
PREFIX="/realestate/prod"

echo "🔐 AWS Parameter Store에 환경 변수 저장 중..."
echo "Region: $REGION"
echo "Prefix: $PREFIX"
echo ""

# .env.production 파일 경로
ENV_FILE=".env.production"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env.production 파일을 찾을 수 없습니다."
    exit 1
fi

# 민감한 정보 (SecureString으로 저장)
SECURE_PARAMS=(
    "GOOGLE_CLIENT_ID"
    "GOOGLE_CLIENT_SECRET"
    "NEXTAUTH_SECRET"
    "POSTGRES_PASSWORD"
    "NEO4J_AUTH"
    "DJANGO_SECRET_KEY"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
)

# 일반 정보 (String으로 저장)
STRING_PARAMS=(
    "NEXTAUTH_URL"
    "NEXT_PUBLIC_API_URL"
    "SERVER_API_URL"
    "POSTGRES_HOST"
    "POSTGRES_PORT"
    "POSTGRES_DB"
    "POSTGRES_USER"
    "NEO4J_URI"
    "NEO4J_USER"
    "ELASTICSEARCH_HOST"
    "ELASTICSEARCH_PORT"
    "REDIS_HOST"
    "REDIS_PORT"
    "OPENAI_API_KEY"
    "AWS_REGION"
    "AWS_S3_BUCKET_NAME"
    "KAKAO_API_KEY"
)

# SecureString 파라미터 저장
for param in "${SECURE_PARAMS[@]}"; do
    value=$(grep "^${param}=" "$ENV_FILE" | cut -d '=' -f2- | sed 's/^["'"'"']\(.*\)["'"'"']$/\1/')
    
    if [ -n "$value" ]; then
        echo "📝 저장 중: ${PREFIX}/${param} (SecureString)"
        aws ssm put-parameter \
            --name "${PREFIX}/${param}" \
            --value "$value" \
            --type "SecureString" \
            --region "$REGION" \
            --overwrite \
            --no-cli-pager 2>/dev/null || echo "⚠️  이미 존재하거나 권한 없음"
    else
        echo "⚠️  건너뜀: ${param} (값 없음)"
    fi
done

# String 파라미터 저장
for param in "${STRING_PARAMS[@]}"; do
    value=$(grep "^${param}=" "$ENV_FILE" | cut -d '=' -f2- | sed 's/^["'"'"']\(.*\)["'"'"']$/\1/')
    
    if [ -n "$value" ]; then
        echo "📝 저장 중: ${PREFIX}/${param} (String)"
        aws ssm put-parameter \
            --name "${PREFIX}/${param}" \
            --value "$value" \
            --type "String" \
            --region "$REGION" \
            --overwrite \
            --no-cli-pager 2>/dev/null || echo "⚠️  이미 존재하거나 권한 없음"
    else
        echo "⚠️  건너뜀: ${param} (값 없음)"
    fi
done

echo ""
echo "✅ Parameter Store 설정 완료!"
echo ""
echo "확인 방법:"
echo "  aws ssm get-parameters-by-path --path ${PREFIX} --region ${REGION}"
