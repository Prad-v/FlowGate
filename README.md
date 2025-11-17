# Flowgate - Observability Optimization Gateway

Flowgate is a vendor-neutral, OpenTelemetry-based gateway that sits between observability agents and backends (Datadog, GCP Monitoring, Grafana, Prometheus/Mimir, etc.). It reduces observability costs by dropping unused metrics, reducing high-cardinality labels, and filtering/sampling logs.

## Features

- **Cost Optimization**: Drop unused metrics, reduce high-cardinality labels
- **AI-Assisted Log Transformation**: Convert unstructured logs to structured JSON
- **Centralized Control**: Manage thousands of gateway instances via OpAMP
- **Versioned Templates**: GitOps-style versioning with rollback support
- **Multi-Tenant**: Isolated configurations per organization
- **Vendor-Neutral**: Works with any OpenTelemetry-compatible backend

## Architecture

```
Agents → Flowgate Gateway → Backends
              ↑
         Control Plane
         (FastAPI + React UI)
```

See [Architecture Documentation](docs/architecture.md) for details.

For OpAMP Agent Management architecture, see [Agent Management Architecture](docs/agent-management-architecture.md).

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd FlowGate
```

2. Quick start (using Makefile):
```bash
make quick-start
```

Or manually:
```bash
# Start services
docker compose up -d

# Initialize database
docker compose exec backend alembic upgrade head
```

#### Using the Makefile

The project includes a comprehensive Makefile for common operations:

**Quick Commands:**
```bash
make help              # Show all available commands
make quick-start       # Build and deploy main stack
make quick-start-vector # Build and deploy with Vector demo
make status            # Show stack status
make logs              # View all logs
make test              # Test the stack
```

**Build & Deploy:**
```bash
make build             # Build all services
make deploy            # Deploy main stack
make deploy-vector     # Deploy with Vector demo services
```

**Service Management:**
```bash
make start             # Start all services
make stop              # Stop all services
make restart           # Restart all services
```

**Logs & Monitoring:**
```bash
make logs              # All logs
make logs-backend      # Backend logs only
make logs-frontend     # Frontend logs only
make logs-gateway      # Gateway logs only
make logs-vector       # Vector demo logs
```

**Testing & Health:**
```bash
make test              # Run stack tests
make test-api          # Test API endpoints
make health            # Check service health
```

**Cleanup:**
```bash
make clean             # Remove containers and volumes
make clean-all         # Remove everything including images
```

See `make help` for the complete list of commands.

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

See [Setup Guide](docs/setup.md) for detailed instructions.

## Project Structure

```
FlowGate/
├── backend/
│   └── services/
│       └── flowgate-backend/    # FastAPI backend
├── frontend/                    # React frontend
├── gateway/                     # OTel Collector configs
├── tests/                       # Unified test directory
├── docs/                        # Documentation
├── helm/                        # Helm charts
└── docker-compose.yml           # Local development
```

## Documentation

- [Architecture](docs/architecture.md) - System architecture and components
- [API Documentation](docs/api.md) - REST API reference
- [Setup Guide](docs/setup.md) - Installation and configuration
- [OTEL Builder Guide](docs/otel-builder.md) - Visual collector configuration builder

## Development

### Backend

```bash
cd backend/services/flowgate-backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend/services/flowgate-backend
pytest tests/

# Frontend tests (when configured)
cd frontend
npm run test
```

## Production Deployment

Deploy using Helm charts:

```bash
helm install flowgate ./helm/flowgate \
  --set postgres.host=your-postgres-host \
  --namespace flowgate
```

See [Setup Guide](docs/setup.md) for production deployment details.

## Contributing

1. Follow the project structure guidelines
2. All tests must be in `tests/` directory
3. Update documentation for new features
4. Follow the coding standards in `rules.yaml`

## License

[Add your license here]

## Support

[Add support information here]


