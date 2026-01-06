#!/bin/bash

# =============================================================================
# Production Deployment Script with Parameter Store Integration
# =============================================================================
# EC2 App Server에서 실행되는 배포 스크립트
# Parameter Store에서 환경 변수를 자동으로 로드합니다.
#
# 사용법:
#   chmod +x scripts/deployment/deploy_app.sh
#   ./scripts/deployment/deploy_app.sh
# =============================================================================

set -e

echo "🚀 배포 시작..."
echo "=================================================="

# 1. 최신 코드 가져오기
echo ""
echo "📥 Step 1: 최신 코드 가져오기"
git fetch origin
git checkout deploy/production
git pull origin deploy/production

# 2. Parameter Store에서 환경 변수 로드
echo ""
echo "🔐 Step 2: Parameter Store에서 환경 변수 로드"
if [ -f "scripts/deployment/load_parameters.sh" ]; then
    chmod +x scripts/deployment/load_parameters.sh
    ./scripts/deployment/load_parameters.sh
else
    echo "⚠️  load_parameters.sh를 찾을 수 없습니다. 기존 .env.production 사용"
fi

# .env.production 파일 확인
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production 파일이 없습니다!"
    echo "Parameter Store 설정을 확인하거나 수동으로 .env.production을 생성하세요."
    exit 1
fi

# 3. ECR 로그인
echo ""
echo "🔑 Step 3: ECR 로그인"
aws ecr get-login-password --region ap-northeast-2 | \
    docker login --username AWS \
    --password-stdin 046685909225.dkr.ecr.ap-northeast-2.amazonaws.com

# 4. 최신 이미지 Pull
echo ""
echo "📦 Step 4: 최신 Docker 이미지 가져오기"
docker-compose -f docker-compose.prod.app.yml pull

# 5. 컨테이너 재시작
echo ""
echo "🔄 Step 5: 서비스 재시작"
docker-compose --env-file .env.production -f docker-compose.prod.app.yml up -d --force-recreate

# 6. 상태 확인
echo ""
echo "🔍 Step 6: 서비스 상태 확인"
sleep 5
docker ps

# 7. 헬스 체크
echo ""
echo "💚 Step 7: 헬스 체크"
echo "Backend: "
curl -f http://localhost:8000/api/health/ || echo "⚠️  Backend health check failed"

echo ""
echo ""
echo "Frontend (through Nginx): "
curl -f http://localhost/ || echo "⚠️  Frontend health check failed"

echo ""
echo "=================================================="
echo "✅ 배포 완료!"
echo ""
echo "서비스 URL: https://goziphouse.com"
echo ""
echo "로그 확인:"
echo "  docker logs realestate-frontend --tail 50"
echo "  docker logs realestate-backend --tail 50"
echo "  docker logs realestate-nginx --tail 50"
