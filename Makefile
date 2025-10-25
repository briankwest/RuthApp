# Makefile for Ruth - Civic Engagement Platform

.PHONY: help install dev prod stop clean test migrate shell logs

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Ruth - Civic Engagement Platform$(NC)"
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install all dependencies (Python and Node)
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd backend && pip install -r requirements.txt
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

dev: ## Start development environment with Docker
	@echo "$(BLUE)Starting development environment...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/api/docs"

dev-build: ## Build and start development environment
	@echo "$(BLUE)Building and starting development environment...$(NC)"
	docker-compose up -d --build
	@echo "$(GREEN)Development environment built and started!$(NC)"

prod: ## Start production environment with Docker
	@echo "$(BLUE)Starting production environment...$(NC)"
	docker-compose --profile production up -d
	@echo "$(GREEN)Production environment started!$(NC)"

stop: ## Stop all Docker containers
	@echo "$(BLUE)Stopping all containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)All containers stopped!$(NC)"

clean: ## Stop containers and remove volumes (WARNING: Deletes data)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(BLUE)Cleaning up...$(NC)"
	docker-compose down -v
	rm -rf backend/__pycache__ backend/**/__pycache__ backend/**/**/__pycache__
	rm -rf frontend/node_modules frontend/build
	@echo "$(GREEN)Cleanup complete!$(NC)"

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	docker-compose exec backend alembic upgrade head
	@echo "$(GREEN)Migrations complete!$(NC)"

migrate-create: ## Create a new migration (usage: make migrate-create name="migration name")
	@echo "$(BLUE)Creating new migration: $(name)$(NC)"
	docker-compose exec backend alembic revision --autogenerate -m "$(name)"
	@echo "$(GREEN)Migration created!$(NC)"

migrate-down: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	docker-compose exec backend alembic downgrade -1
	@echo "$(GREEN)Rollback complete!$(NC)"

seed: ## Seed database with sample data
	@echo "$(BLUE)Seeding database...$(NC)"
	docker-compose exec backend python -m app.scripts.seed_data
	@echo "$(GREEN)Database seeded!$(NC)"

test: ## Run all tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	docker-compose exec backend pytest
	@echo "$(BLUE)Running frontend tests...$(NC)"
	docker-compose exec frontend npm test
	@echo "$(GREEN)All tests complete!$(NC)"

test-backend: ## Run backend tests only
	@echo "$(BLUE)Running backend tests...$(NC)"
	docker-compose exec backend pytest -v

test-frontend: ## Run frontend tests only
	@echo "$(BLUE)Running frontend tests...$(NC)"
	docker-compose exec frontend npm test

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	docker-compose exec backend pytest --cov=app --cov-report=html --cov-report=term

format: ## Format code with black and prettier
	@echo "$(BLUE)Formatting backend code...$(NC)"
	docker-compose exec backend black .
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	docker-compose exec frontend npm run format
	@echo "$(GREEN)Code formatted!$(NC)"

lint: ## Run linters (flake8 and eslint)
	@echo "$(BLUE)Linting backend code...$(NC)"
	docker-compose exec backend flake8 app/
	@echo "$(BLUE)Linting frontend code...$(NC)"
	docker-compose exec frontend npm run lint
	@echo "$(GREEN)Linting complete!$(NC)"

shell: ## Access backend shell
	@echo "$(BLUE)Opening backend shell...$(NC)"
	docker-compose exec backend /bin/bash

shell-db: ## Access database shell
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	docker-compose exec postgres psql -U ruth_user -d ruth_db

shell-redis: ## Access Redis CLI
	@echo "$(BLUE)Opening Redis CLI...$(NC)"
	docker-compose exec redis redis-cli

logs: ## View all container logs
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

logs-db: ## View database logs only
	docker-compose logs -f postgres

logs-worker: ## View Celery worker logs
	docker-compose logs -f celery_worker

ps: ## Show running containers
	@docker-compose ps

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)Build complete!$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)Services restarted!$(NC)"

restart-backend: ## Restart backend service only
	@echo "$(BLUE)Restarting backend...$(NC)"
	docker-compose restart backend
	@echo "$(GREEN)Backend restarted!$(NC)"

restart-frontend: ## Restart frontend service only
	@echo "$(BLUE)Restarting frontend...$(NC)"
	docker-compose restart frontend
	@echo "$(GREEN)Frontend restarted!$(NC)"

env: ## Copy environment example file
	@echo "$(BLUE)Creating .env file from example...$(NC)"
	cp backend/.env.example backend/.env
	@echo "$(YELLOW)Please edit backend/.env with your API keys!$(NC)"

check-env: ## Verify environment variables are set
	@echo "$(BLUE)Checking environment configuration...$(NC)"
	@docker-compose exec backend python -c "from app.core.config import settings; print('Environment configured successfully!')"

backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U ruth_user ruth_db > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backed up to backups/ directory!$(NC)"

restore: ## Restore database from backup (usage: make restore file=backup.sql)
	@echo "$(BLUE)Restoring database from $(file)...$(NC)"
	docker-compose exec -T postgres psql -U ruth_user ruth_db < $(file)
	@echo "$(GREEN)Database restored!$(NC)"

clean-addresses: ## Clean representative addresses using Google Address Validation API
	@echo "$(BLUE)Cleaning representative addresses...$(NC)"
	docker-compose exec backend python -m app.scripts.clean_representative_addresses
	@echo "$(GREEN)Address cleaning complete!$(NC)"

update-addresses: ## Update recipient addresses from representative data
	@echo "$(BLUE)Updating recipient addresses...$(NC)"
	docker-compose exec backend python -m app.scripts.update_recipient_addresses
	@echo "$(GREEN)Address update complete!$(NC)"

regenerate-pdfs: ## Regenerate all PDFs in database with updated format
	@echo "$(BLUE)Regenerating all PDFs...$(NC)"
	docker-compose exec backend python -m app.scripts.regenerate_pdfs
	@echo "$(GREEN)PDF regeneration complete!$(NC)"

refresh-pdfs: update-addresses regenerate-pdfs ## Update addresses and regenerate all PDFs

refresh-all: clean-addresses update-addresses regenerate-pdfs ## Clean, update, and regenerate everything

.DEFAULT_GOAL := help