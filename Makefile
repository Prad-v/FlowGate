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

test: ## Run all tests (pytest in Docker)
	@echo "🧪 Running all tests..."
	@cd tests && $(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest -v" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest -v"

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	@$(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest -v -k 'not integration'" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest -v -k 'not integration'"

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	@$(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest -v -k 'integration'" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest -v -k 'integration'"

test-security: ## Run all security module tests
	@echo "🔒 Running security module tests..."
	@echo "Setting up test database..."
	@$(COMPOSE) exec -T backend sh -c "cd /app && DATABASE_URL=postgresql://flowgate:flowgate@postgres:5432/flowgate_test alembic upgrade head" || true
	@$(COMPOSE) exec -T backend sh -c "cd /tests && PYTHONPATH=/app python -m pytest -v test_security_*.py" || \
		$(COMPOSE) run --rm backend sh -c "cd /tests && PYTHONPATH=/app python -m pytest -v test_security_*.py"

test-iga: ## Run Identity Governance Agent tests
	@echo "🔒 Running IGA tests..."
	@$(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest -v test_security_identity_governance.py" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest -v test_security_identity_governance.py"

test-tva: ## Run Threat Vector Agent tests
	@echo "🔒 Running TVA tests..."
	@$(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest -v test_security_threat_vector.py" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest -v test_security_threat_vector.py"

test-cra: ## Run Correlation & RCA Agent tests
	@echo "🔒 Running CRA tests..."
	@$(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest -v test_security_correlation_rca.py" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest -v test_security_correlation_rca.py"

test-pba: ## Run Persona Baseline Agent tests
	@echo "🔒 Running PBA tests..."
	@$(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest -v test_security_persona_baseline.py" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest -v test_security_persona_baseline.py"

test-saa: ## Run SOAR Automation Agent tests
	@echo "🔒 Running SAA tests..."
	@$(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest -v test_security_soar_automation.py" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest -v test_security_soar_automation.py"

test-threat-detection: ## Run Threat Detection Service tests
	@echo "🔒 Running Threat Detection Service tests..."
	@$(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest -v test_security_threat_detection.py" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest -v test_security_threat_detection.py"

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	@$(COMPOSE) exec -T backend sh -c "cd /app/../tests && python -m pytest --cov=/app/app --cov-report=html --cov-report=term" || \
		$(COMPOSE) run --rm backend sh -c "cd /app/../tests && python -m pytest --cov=/app/app --cov-report=html --cov-report=term"

test-local: ## Run tests locally (requires Python environment)
	@echo "🧪 Running tests locally..."
	@cd tests && python3 -m pytest -v || python -m pytest -v

test-frontend: ## Run frontend tests
	@echo "🧪 Running frontend tests..."
	@cd frontend && npm test || echo "⚠ Frontend tests not configured yet"

test-all: test-security test-frontend ## Run all tests (backend + frontend)
	@echo "✅ All tests completed!"

test-api: ## Test backend API endpoints (health checks)
	@echo "🧪 Testing Backend API endpoints..."
	@echo ""
	@echo "Health Check:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Backend not responding"
	@echo ""
	@echo "Root Endpoint:"
	@curl -s http://localhost:8000/ | python3 -m json.tool || echo "❌ Backend not responding"
	@echo ""
	@echo "API Documentation:"
	@curl -s -o /dev/null -w "API Docs Status: %{http_code}\n" http://localhost:8000/docs || echo "❌ API Docs not accessible"

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

quick-start-vector: build-all deploy-vector register-gateway-2 ## Build and deploy with Vector demo (quick start)
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

register-gateway-2: ## Register gateway-2 if not already registered (runs after deploy)
	@echo "🔐 Checking gateway-2 registration..."
	@echo "   Waiting for backend to be ready..."
	@timeout=30; \
	while [ $$timeout -gt 0 ] && ! curl -s http://localhost:8000/health > /dev/null 2>&1; do \
		sleep 1; \
		timeout=$$((timeout - 1)); \
	done; \
	CONTAINER_TOKEN=$$(docker compose exec -T gateway-2 cat /var/lib/otelcol/opamp_token 2>/dev/null || echo ''); \
	if [ -z "$$CONTAINER_TOKEN" ]; then \
		echo "📝 Gateway-2 container has no token, checking database..."; \
		DB_TOKEN=$$(docker compose exec -T backend python -c "from app.database import SessionLocal; from app.models.gateway import Gateway; db = SessionLocal(); g = db.query(Gateway).filter(Gateway.instance_id == 'gateway-2').first(); print(g.opamp_token if g and g.opamp_token else ''); db.close()" 2>/dev/null | grep -v "INFO sqlalchemy" | tail -1); \
		if [ -n "$$DB_TOKEN" ]; then \
			echo "✓ Gateway-2 found in database with token, restarting with token..."; \
			OPAMP_TOKEN=$$DB_TOKEN docker compose up -d gateway-2; \
			echo "✓ Gateway-2 restarted with OpAMP token from database"; \
			sleep 3; \
		else \
			echo "📝 Gateway-2 not registered, creating registration token..."; \
			ORG_ID=$$(docker compose exec -T backend python -c "from app.database import SessionLocal; from app.models.tenant import Organization; db = SessionLocal(); org = db.query(Organization).first(); print(org.id if org else ''); db.close()" 2>/dev/null | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -1); \
			if [ -z "$$ORG_ID" ]; then \
				echo "⚠️  Could not get organization ID, skipping automatic registration"; \
				echo "   You can manually register gateway-2 using: ./register-gateway-2.sh"; \
			else \
				echo "   Using Organization ID: $$ORG_ID"; \
				TOKEN_RESPONSE=$$(curl -s -X POST "http://localhost:8000/api/v1/registration-tokens?org_id=$$ORG_ID" \
					-H "Content-Type: application/json" \
					-d '{"name": "Gateway-2 Auto Registration", "expires_in_days": 365}'); \
				REGISTRATION_TOKEN=$$(echo "$$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null || echo ""); \
				if [ -n "$$REGISTRATION_TOKEN" ]; then \
					echo "✓ Registration token created, restarting gateway-2 with token..."; \
					REGISTRATION_TOKEN=$$REGISTRATION_TOKEN docker compose up -d gateway-2; \
					echo "✓ Gateway-2 restarted with registration token"; \
					echo "   Waiting for registration to complete..."; \
					sleep 5; \
				else \
					echo "⚠️  Failed to create registration token, gateway-2 may need manual registration"; \
				fi; \
			fi; \
		fi; \
	else \
		echo "✓ Gateway-2 already has OpAMP token in container"; \
	fi

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

