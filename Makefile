# =============================================================================
# Makefile for Real Estate Platform
# =============================================================================
# Development and deployment commands
# =============================================================================

.PHONY: help setup up down logs clean migrate ingest \
        build build-prod push deploy test lint \
        ecr-login ecr-setup

# Default target
.DEFAULT_GOAL := help

# Variables
AWS_REGION ?= ap-northeast-2
AWS_ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
IMAGE_TAG ?= latest

# =============================================================================
# Help
# =============================================================================
help:
	@echo "=============================================="
	@echo "Real Estate Platform - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "Development:"
	@echo "  make setup        - Build all Docker images"
	@echo "  make up           - Start all services (development)"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - View logs (all services)"
	@echo "  make logs-backend - View backend logs"
	@echo "  make logs-rag     - View RAG service logs"
	@echo "  make clean        - Clean volumes and cache"
	@echo "  make shell        - Open shell in backend container"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run Django migrations"
	@echo "  make ingest       - Ingest listing data"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-backend - Run backend tests"
	@echo "  make lint         - Run linters"
	@echo ""
	@echo "Production:"
	@echo "  make build-prod   - Build production images"
	@echo "  make up-prod      - Start production stack"
	@echo ""
	@echo "AWS Deployment:"
	@echo "  make ecr-login    - Login to ECR"
	@echo "  make ecr-setup    - Create ECR repositories"
	@echo "  make push         - Push images to ECR"
	@echo "  make deploy       - Deploy to ECS"

# =============================================================================
# Development Commands
# =============================================================================
setup:
	docker compose build

up:
	docker compose up -d
	@echo ""
	@echo "Services started:"
	@echo "  Frontend:   http://localhost:3000"
	@echo "  Backend:    http://localhost:8000"
	@echo "  RAG API:    http://localhost:8001"
	@echo "  Reco API:   http://localhost:8002"
	@echo "  OpenSearch: http://localhost:9200"
	@echo "  Neo4j:      http://localhost:7474"

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-rag:
	docker compose logs -f rag

logs-frontend:
	docker compose logs -f frontend

shell:
	docker compose exec backend /bin/bash

clean:
	docker compose down -v --remove-orphans
	docker system prune -f
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# =============================================================================
# Database Commands
# =============================================================================
migrate:
	docker compose exec backend python manage.py migrate

makemigrations:
	docker compose exec backend python manage.py makemigrations

ingest:
	docker compose exec backend python ../scripts/ingest_listings.py

db-shell:
	docker compose exec postgres psql -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-realestate}

# =============================================================================
# Testing Commands
# =============================================================================
test:
	docker compose exec backend pytest
	docker compose exec rag pytest

test-backend:
	docker compose exec backend pytest -v

test-rag:
	docker compose exec rag pytest -v

lint:
	docker compose exec backend python -m flake8 .
	docker compose exec backend python -m black --check .

format:
	docker compose exec backend python -m black .

# =============================================================================
# Production Commands
# =============================================================================
build-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

up-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

down-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# =============================================================================
# AWS Deployment Commands
# =============================================================================
ecr-login:
	@echo "Logging in to ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | \
		docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

ecr-setup:
	@echo "Creating ECR repositories..."
	chmod +x infra/aws/ecr-setup.sh
	./infra/aws/ecr-setup.sh $(AWS_REGION)

push: ecr-login build-prod
	@echo "Pushing images to ECR..."
	docker tag realestate-backend:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/realestate-backend:$(IMAGE_TAG)
	docker tag realestate-frontend:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/realestate-frontend:$(IMAGE_TAG)
	docker tag realestate-rag:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/realestate-rag:$(IMAGE_TAG)
	docker tag realestate-reco:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/realestate-reco:$(IMAGE_TAG)
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/realestate-backend:$(IMAGE_TAG)
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/realestate-frontend:$(IMAGE_TAG)
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/realestate-rag:$(IMAGE_TAG)
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/realestate-reco:$(IMAGE_TAG)

deploy:
	@echo "Deploying to ECS..."
	@echo "Update ECS services with new task definitions"
	aws ecs update-service --cluster realestate-cluster --service backend-service --force-new-deployment --region $(AWS_REGION)
	aws ecs update-service --cluster realestate-cluster --service frontend-service --force-new-deployment --region $(AWS_REGION)
	aws ecs update-service --cluster realestate-cluster --service rag-service --force-new-deployment --region $(AWS_REGION)
	aws ecs update-service --cluster realestate-cluster --service reco-service --force-new-deployment --region $(AWS_REGION)

# =============================================================================
# Utility Commands
# =============================================================================
ps:
	docker compose ps

stats:
	docker stats --no-stream

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/api/health/ && echo " Backend: OK" || echo " Backend: FAIL"
	@curl -s http://localhost:8001/health && echo " RAG: OK" || echo " RAG: FAIL"
	@curl -s http://localhost:3000/api/health && echo " Frontend: OK" || echo " Frontend: FAIL"
