.PHONY: help up down restart logs clean build test lint format migrate

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services
	cd infra && docker-compose up -d
	@echo "Services starting... Use 'make logs' to view logs"

down: ## Stop all services
	cd infra && docker-compose down

restart: ## Restart all services
	cd infra && docker-compose restart

logs: ## View logs from all services
	cd infra && docker-compose logs -f

logs-backend: ## View backend logs
	cd infra && docker-compose logs -f backend

logs-frontend: ## View frontend logs
	cd infra && docker-compose logs -f frontend

logs-keycloak: ## View Keycloak logs
	cd infra && docker-compose logs -f keycloak

build: ## Build all Docker images
	cd infra && docker-compose build

clean: ## Stop and remove all containers, volumes, and networks
	cd infra && docker-compose down -v
	docker system prune -f

migrate: ## Run database migrations
	cd infra && docker-compose exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create NAME=migration_name)
	cd infra && docker-compose exec backend alembic revision --autogenerate -m "$(NAME)"

test-backend: ## Run backend tests
	cd infra && docker-compose exec backend python -m pytest

test-frontend: ## Run frontend tests
	cd frontend && npm test

lint-backend: ## Lint backend code
	cd infra && docker-compose exec backend flake8 app/ || true
	cd infra && docker-compose exec backend black --check app/ || true

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint || true

format-backend: ## Format backend code
	cd infra && docker-compose exec backend black app/
	cd infra && docker-compose exec backend isort app/

format-frontend: ## Format frontend code
	cd frontend && npm run format || true

shell-backend: ## Open shell in backend container
	cd infra && docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	cd infra && docker-compose exec frontend /bin/sh

shell-db: ## Open PostgreSQL shell
	cd infra && docker-compose exec postgres psql -U ztnauser -d ztna

keycloak-admin: ## Open Keycloak admin console (browser)
	@echo "Keycloak Admin Console: http://localhost:8080"
	@echo "Username: admin"
	@echo "Password: adminsecure123"

status: ## Show status of all services
	cd infra && docker-compose ps

