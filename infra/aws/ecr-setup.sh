#!/bin/bash
# =============================================================================
# ECR Repository Setup Script
# =============================================================================
# Creates ECR repositories for all services
# Usage: ./ecr-setup.sh [AWS_REGION]
# =============================================================================

set -e

AWS_REGION=${1:-ap-northeast-2}
REPOSITORIES=(
    "realestate-backend"
    "realestate-frontend"
    "realestate-rag"
    "realestate-reco"
)

echo "Creating ECR repositories in region: $AWS_REGION"

for REPO in "${REPOSITORIES[@]}"; do
    echo "Creating repository: $REPO"
    
    # Create repository if it doesn't exist
    aws ecr describe-repositories --repository-names "$REPO" --region "$AWS_REGION" 2>/dev/null || \
    aws ecr create-repository \
        --repository-name "$REPO" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256 \
        --image-tag-mutability MUTABLE
    
    # Set lifecycle policy to keep only last 10 images
    aws ecr put-lifecycle-policy \
        --repository-name "$REPO" \
        --region "$AWS_REGION" \
        --lifecycle-policy-text '{
            "rules": [
                {
                    "rulePriority": 1,
                    "description": "Keep last 10 images",
                    "selection": {
                        "tagStatus": "any",
                        "countType": "imageCountMoreThan",
                        "countNumber": 10
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }'
    
    echo "Repository $REPO created successfully"
done

echo ""
echo "All repositories created. To push images:"
echo "1. Login to ECR:"
echo "   aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin \$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com"
echo ""
echo "2. Build and push images using:"
echo "   docker compose -f docker-compose.yml -f docker-compose.prod.yml build"
echo "   docker push <account-id>.dkr.ecr.$AWS_REGION.amazonaws.com/<repo-name>:latest"
