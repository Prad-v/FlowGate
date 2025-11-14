# Flowgate Setup Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd FlowGate
```

### 2. Environment Configuration

Copy the example environment file:

```bash
cp backend/services/flowgate-backend/.env.example backend/services/flowgate-backend/.env
```

Edit `.env` if needed (defaults should work for local development).

### 3. Start Services

```bash
docker compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- OpAMP Server (port 4320)
- Frontend (port 5173)
- Gateway (ports 4317, 4318, 8888)

### 4. Initialize Database

```bash
docker compose exec backend alembic upgrade head
```

Or if running locally:

```bash
cd backend/services/flowgate-backend
alembic upgrade head
```

### 5. Access Services

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **OpAMP Server**: http://localhost:4320
- **Gateway Health**: http://localhost:8888

## Development Workflow

### Backend Development

1. Make changes to Python files
2. Backend auto-reloads (if using `--reload` flag)
3. Run tests:
   ```bash
   cd backend/services/flowgate-backend
   pytest tests/
   ```

### Frontend Development

1. Make changes to React files
2. Frontend auto-reloads via Vite
3. Run tests (when configured):
   ```bash
   cd frontend
   npm run test
   ```

### Database Migrations

Create a new migration:

```bash
cd backend/services/flowgate-backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Production Deployment

### Using Helm

1. Install Helm chart:

```bash
helm install flowgate ./helm/flowgate \
  --set postgres.host=your-postgres-host \
  --set postgres.password=your-password \
  --namespace flowgate
```

2. Update values in `helm/flowgate/values.yaml` for your environment

3. Upgrade:

```bash
helm upgrade flowgate ./helm/flowgate \
  --namespace flowgate
```

### Environment Variables

Key environment variables for production:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Secret key for JWT tokens
- `CORS_ORIGINS`: Allowed CORS origins
- `OPAMP_SERVER_HOST`: OpAMP server host
- `OPAMP_SERVER_PORT`: OpAMP server port

## Troubleshooting

### Database Connection Issues

Check PostgreSQL is running:

```bash
docker compose ps postgres
docker compose logs postgres
```

### Backend Not Starting

Check logs:

```bash
docker compose logs backend
```

### Frontend Not Loading

Check if backend is accessible:

```bash
curl http://localhost:8000/health
```

### Gateway Not Connecting

Check OpAMP server:

```bash
curl http://localhost:4320/health
```

## Next Steps

1. Set up authentication (JWT/OIDC)
2. Configure backend integrations (Datadog, GCP, etc.)
3. Set up CI/CD pipeline
4. Configure monitoring and alerting


