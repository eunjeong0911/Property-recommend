.PHONY: help setup up down logs clean migrate ingest

help:
	@echo "Available commands:"
	@echo "  make setup      - Initial setup (install dependencies)"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - View logs"
	@echo "  make clean      - Clean volumes and cache"
	@echo "  make migrate    - Run Django migrations"
	@echo "  make ingest     - Ingest listing data"

setup:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

migrate:
	docker-compose exec backend python manage.py migrate

ingest:
	docker-compose exec backend python ../scripts/ingest_listings.py
