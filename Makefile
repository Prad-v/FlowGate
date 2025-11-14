.PHONY: help build up down restart logs ps clean test health deploy deploy-vector stop start

# Variables
COMPOSE_FILES = -f docker-compose.yml
VECTOR_COMPOSE = -f docker-compose.vector-demo.yml
COMPOSE = docker compose $(COMPOSE_FILES)
COMPOSE_VECTOR = docker compose $(COMPOSE_FILES) $(VECTOR_COMPOSE)

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Flowgate - Makefile Commands"
	@echo "=============================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Build targets
build: ## Build all Docker images
	@echo "🔨 Building Flowgate services..."
	$(COMPOSE) build

build-backend: ## Build backend service only
	@echo "🔨 Building backend service..."
	$(COMPOSE) build backend

build-frontend: ## Build frontend service only
	@echo "🔨 Building frontend service..."
	$(COMPOSE) build frontend

build-gateway: ## Build gateway service only
	@echo "🔨 Building gateway service..."
	$(COMPOSE) build gateway

build-vector: ## Build Vector demo services
	@echo "🔨 Building Vector demo services..."
	$(COMPOSE_VECTOR) build

build-all: build build-vector ## Build all services including Vector demo

# Deploy targets
deploy: ## Deploy the main Flowgate stack
	@echo "🚀 Deploying Flowgate stack..."
	$(COMPOSE) up -d
	@echo "✅ Flowgate stack deployed!"
	@echo "📊 Services:"
	@$(COMPOSE) ps

deploy-vector: ## Deploy Flowgate stack with Vector demo services
	@echo "🚀 Deploying Flowgate stack with Vector demo..."
	$(COMPOSE_VECTOR) up -d
	@echo "✅ Flowgate stack with Vector demo deployed!"
	@echo "📊 Services:"
	@$(COMPOSE_VECTOR) ps

# Start/Stop targets
start: ## Start all services
	@echo "▶️  Starting Flowgate services..."
	$(COMPOSE) start

start-vector: ## Start all services including Vector demo
	@echo "▶️  Starting Flowgate services with Vector demo..."
	$(COMPOSE_VECTOR) start

stop: ## Stop all services
	@echo "⏹️  Stopping Flowgate services..."
	$(COMPOSE) stop

stop-vector: ## Stop all services including Vector demo
	@echo "⏹️  Stopping Flowgate services with Vector demo..."
	$(COMPOSE_VECTOR) stop

restart: ## Restart all services
	@echo "🔄 Restarting Flowgate services..."
	$(COMPOSE) restart

restart-vector: ## Restart all services including Vector demo
	@echo "🔄 Restarting Flowgate services with Vector demo..."
	$(COMPOSE_VECTOR) restart

# Status and logs
ps: ## Show running containers
	@echo "📊 Container Status:"
	@$(COMPOSE) ps

ps-vector: ## Show running containers including Vector demo
	@echo "📊 Container Status (with Vector demo):"
	@$(COMPOSE_VECTOR) ps

logs: ## Show logs from all services
	$(COMPOSE) logs -f

logs-backend: ## Show backend logs
	$(COMPOSE) logs -f backend

logs-frontend: ## Show frontend logs
	$(COMPOSE) logs -f frontend

logs-gateway: ## Show gateway logs
	$(COMPOSE) logs -f gateway

logs-vector: ## Show Vector demo logs
	$(COMPOSE_VECTOR) logs -f vector-demo-logs vector-observability-backend

logs-all: ## Show all logs including Vector demo
	$(COMPOSE_VECTOR) logs -f

# Cleanup targets
down: ## Stop and remove containers, networks
	@echo "🧹 Stopping and removing containers..."
	$(COMPOSE) down

down-vector: ## Stop and remove containers including Vector demo
	@echo "🧹 Stopping and removing containers (with Vector demo)..."
	$(COMPOSE_VECTOR) down

clean: ## Remove containers, networks, and volumes
	@echo "🧹 Cleaning up containers, networks, and volumes..."
	$(COMPOSE) down -v
	@echo "✅ Cleanup complete!"

clean-vector: ## Remove containers, networks, and volumes including Vector demo
	@echo "🧹 Cleaning up containers, networks, and volumes (with Vector demo)..."
	$(COMPOSE_VECTOR) down -v
	@echo "✅ Cleanup complete!"

clean-all: ## Remove all containers, networks, volumes, and images
	@echo "🧹 Deep cleaning (containers, networks, volumes, images)..."
	$(COMPOSE_VECTOR) down -v --rmi all
	@echo "✅ Deep cleanup complete!"

# Health and testing
health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@echo ""
	@echo "Backend API:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Backend not responding"
	@echo ""
	@echo "Frontend:"
	@curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:5173 || echo "❌ Frontend not responding"
	@echo ""
	@echo "OpAMP Server:"
	@curl -s http://localhost:4320/health | python3 -m json.tool || echo "❌ OpAMP Server not responding"
	@echo ""
	@echo "Gateway:"
	@curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8888 || echo "❌ Gateway not responding"

test: ## Run tests against the stack
	@echo "🧪 Testing Flowgate stack..."
	@echo ""
	@echo "1. Testing Backend API..."
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo ""
	@echo "2. Testing Frontend..."
	@curl -s -o /dev/null -w "Frontend Status: %{http_code}\n" http://localhost:5173
	@echo ""
	@echo "3. Testing API Documentation..."
	@curl -s -o /dev/null -w "API Docs Status: %{http_code}\n" http://localhost:8000/docs
	@echo ""
	@echo "✅ Tests complete!"

test-api: ## Test backend API endpoints
	@echo "🧪 Testing Backend API..."
	@echo ""
	@echo "Health Check:"
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo ""
	@echo "Root Endpoint:"
	@curl -s http://localhost:8000/ | python3 -m json.tool
	@echo ""
	@echo "Templates Endpoint (should require org_id):"
	@curl -s http://localhost:8000/api/v1/templates | python3 -m json.tool | head -10

# Database targets
db-migrate: ## Run database migrations
	@echo "🗄️  Running database migrations..."
	$(COMPOSE) exec backend alembic upgrade head

db-shell: ## Open database shell
	$(COMPOSE) exec postgres psql -U flowgate -d flowgate

# Development targets
dev: ## Start development environment
	@echo "🛠️  Starting development environment..."
	$(COMPOSE) up

dev-vector: ## Start development environment with Vector demo
	@echo "🛠️  Starting development environment with Vector demo..."
	$(COMPOSE_VECTOR) up

# Quick start
quick-start: build deploy ## Build and deploy the stack (quick start)
	@echo "✅ Quick start complete!"
	@echo "📊 Services:"
	@$(COMPOSE) ps
	@echo ""
	@echo "🌐 Access points:"
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - OpAMP Server: http://localhost:4320/health"

quick-start-vector: build-all deploy-vector ## Build and deploy with Vector demo (quick start)
	@echo "✅ Quick start with Vector demo complete!"
	@echo "📊 Services:"
	@$(COMPOSE_VECTOR) ps
	@echo ""
	@echo "🌐 Access points:"
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - OpAMP Server: http://localhost:4320/health"
	@echo "  - Vector Observability Backend: ports 4319 (gRPC), 4321 (HTTP)"

# Update targets
pull: ## Pull latest images
	@echo "📥 Pulling latest images..."
	$(COMPOSE) pull

pull-vector: ## Pull latest images including Vector
	@echo "📥 Pulling latest images (including Vector)..."
	$(COMPOSE_VECTOR) pull

# Status summary
status: ## Show comprehensive status
	@echo "📊 Flowgate Stack Status"
	@echo "========================"
	@echo ""
	@echo "Containers:"
	@$(COMPOSE) ps
	@echo ""
	@echo "Service URLs:"
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - Backend: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - OpAMP: http://localhost:4320/health"
	@echo "  - Gateway: ports 4317 (gRPC), 4318 (HTTP), 8888 (metrics)"

status-vector: ## Show comprehensive status including Vector
	@echo "📊 Flowgate Stack Status (with Vector Demo)"
	@echo "============================================="
	@echo ""
	@echo "Containers:"
	@$(COMPOSE_VECTOR) ps
	@echo ""
	@echo "Service URLs:"
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - Backend: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - OpAMP: http://localhost:4320/health"
	@echo "  - Gateway: ports 4317 (gRPC), 4318 (HTTP), 8888 (metrics)"
	@echo "  - Vector Backend: ports 4319 (gRPC), 4321 (HTTP)"

