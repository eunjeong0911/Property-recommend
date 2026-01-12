#!/bin/bash

# =============================================================================
# AWS Parameter Store에서 환경 변수 로드 스크립트
# =============================================================================
# EC2 인스턴스에서 실행하여 Parameter Store의 값을 .env.production 파일로 생성
# 
# 사용법:
#   chmod +x scripts/deployment/load_parameters.sh
#   ./scripts/deployment/load_parameters.sh
# =============================================================================

set -e

# 설정
REGION="ap-northeast-2"
PREFIX="/realestate/prod"
OUTPUT_FILE=".env.production"

echo "🔐 AWS Parameter Store에서 환경 변수 로드 중..."
echo "Region: $REGION"
echo "Prefix: $PREFIX"
echo "Output: $OUTPUT_FILE"
echo ""

# 기존 파일 백업
if [ -f "$OUTPUT_FILE" ]; then
    BACKUP_FILE="${OUTPUT_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📦 기존 파일 백업: $BACKUP_FILE"
    cp "$OUTPUT_FILE" "$BACKUP_FILE"
fi

# 임시 파일 생성
TMP_FILE=$(mktemp)

# Parameter Store에서 모든 파라미터 가져오기
echo "📥 Parameter Store에서 데이터 가져오는 중..."

aws ssm get-parameters-by-path \
    --path "$PREFIX" \
    --with-decryption \
    --region "$REGION" \
    --query 'Parameters[*].[Name,Value]' \
    --output text | while IFS=$'\t' read -r name value; do
    
    # 파라미터 이름에서 PREFIX 제거하여 환경 변수 이름 추출
    env_name=$(echo "$name" | sed "s|${PREFIX}/||")
    
    # .env 형식으로 저장
    echo "${env_name}=${value}" >> "$TMP_FILE"
done

# 파라미터가 하나라도 로드되었는지 확인
if [ ! -s "$TMP_FILE" ]; then
    echo "❌ Parameter Store에서 파라미터를 찾을 수 없습니다."
    echo ""
    echo "확인사항:"
    echo "  1. EC2 IAM Role에 Parameter Store 읽기 권한이 있는지 확인"
    echo "  2. Parameter가 실제로 저장되어 있는지 확인:"
    echo "     aws ssm get-parameters-by-path --path $PREFIX --region $REGION"
    rm -f "$TMP_FILE"
    exit 1
fi

# 파일 정렬 및 저장
sort "$TMP_FILE" > "$OUTPUT_FILE"
rm -f "$TMP_FILE"

echo ""
echo "✅ 환경 변수 로드 완료!"
echo "📄 파일 위치: $OUTPUT_FILE"
echo ""

# 로드된 환경 변수 개수 출력
param_count=$(wc -l < "$OUTPUT_FILE")
echo "📊 로드된 파라미터 개수: $param_count"
echo ""

# 중요 환경 변수 확인 (값은 숨김)
echo "🔍 주요 환경 변수 확인:"
for key in GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET NEXTAUTH_SECRET SERVER_API_URL NEXTAUTH_URL; do
    if grep -q "^${key}=" "$OUTPUT_FILE"; then
        value=$(grep "^${key}=" "$OUTPUT_FILE" | cut -d '=' -f2-)
        if [ -n "$value" ]; then
            echo "  ✅ ${key}: 설정됨"
        else
            echo "  ⚠️  ${key}: 비어있음"
        fi
    else
        echo "  ❌ ${key}: 없음"
    fi
done

echo ""
echo "💡 다음 명령어로 Docker Compose를 재시작하세요:"
echo "   docker-compose --env-file $OUTPUT_FILE -f docker-compose.prod.app.yml up -d --force-recreate"
