# Flowgate Architecture

## Overview

Flowgate is an observability optimization gateway that sits between observability agents and backends (Datadog, GCP Monitoring, Grafana, etc.). It reduces costs by dropping unused metrics, reducing high-cardinality labels, and transforming logs.

> **📊 For a detailed architecture diagram with all components and data flows, see [Architecture Diagram](architecture-diagram.md)**

> **🔧 For comprehensive OpAMP implementation details and protocol compliance, see [OpAMP Implementation](opamp-implementation.md)**

## High-Level Architecture

```
┌─────────────────┐
│  Agents         │
│  (Prometheus,   │
│   OTLP, etc.)   │
└────────┬────────┘
         │
         │ OTLP / Metrics / Logs
         ▼
┌─────────────────┐
│  Flowgate       │
│  Gateway        │
│  (OTel Collector│
│   + OpAMP)      │
└────────┬────────┘
         │
         │ Transformed/Optimized
         ▼
┌─────────────────┐
│  Backends        │
│  (Datadog, GCP,  │
│   Grafana, etc.) │
└─────────────────┘

         ▲
         │
         │ Config Management
         │
┌────────┴────────┐
│  Control Plane   │
│  (FastAPI)       │
│  + React UI      │
└─────────────────┘
```

## Components

### 1. Flowgate Gateway (Data Plane)

> **See [Agent Management Architecture](agent-management-architecture.md) for detailed OpAMP agent management documentation.**

- **Technology**: OpenTelemetry Collector v0.130.0 (custom build)
- **Components**:
  - **Receivers**: OTLP (gRPC/HTTP), Prometheus
  - **Processors**: Batch, Memory Limiter
  - **Exporters**: OTLP, OTLP HTTP, Debug
  - **Extensions**: OpAMP Extension
- **Dual Mode Support**:
  - **Supervisor Mode** (Default): OpAMP Supervisor v0.139.0 manages collector lifecycle
  - **Extension Mode**: Collector connects directly via OpAMP extension
- **Responsibilities**:
  - Ingests telemetry from agents (OTLP, Prometheus, FluentBit)
  - Applies transformations (drop, filter, transform, route)
  - Routes optimized data to backends
  - Managed via OpAMP (no manual config)
  - Remote configuration support

### 2. Control Plane (Backend)

- **Technology**: FastAPI (Python 3.11+)
- **API Endpoints**:
  - `/api/v1/templates` - Template management
  - `/api/v1/deployments` - Config deployment
  - `/api/v1/gateways` - Gateway registration/management
  - `/api/v1/opamp-config` - OpAMP configuration
  - `/api/v1/validation` - Config validation
  - `/api/v1/registration-tokens` - Registration token management
  - `/api/v1/supervisor` - Supervisor management
  - `/api/v1/supervisor/agents` - Supervisor UI endpoints
  - `/api/v1/settings` - System settings
  - `/api/v1/agent-tags` - Agent tagging
- **Services**:
  - TemplateService - Template CRUD and versioning
  - DeploymentService - Deployment orchestration
  - GatewayService - Gateway lifecycle management
  - OpAMPService - OpAMP token and config management
  - OpAMPProtocolService - OpAMP protocol message handling
  - OpAMPConfigService - Config distribution
  - ValidationService - Config validation
  - ConfigValidator - Component whitelist validation
  - SettingsService - System configuration
- **Responsibilities**:
  - Template management and versioning
  - Config validation and dry-run
  - Deployment orchestration
  - Gateway registration and health tracking
  - OpAMP server for config distribution
  - Component validation (ensures only supported components are used)

### 3. Frontend

- **Technology**: React + TypeScript + TailwindCSS
- **Responsibilities**:
  - Dashboard with metrics and health
  - Template management UI
  - Log transformer studio
  - Deployment management

### 4. OpAMP Server

- **Technology**: FastAPI
- **Endpoints**:
  - `/api/v1/opamp/v1/opamp` - WebSocket transport (preferred)
  - `/api/v1/opamp/v1/opamp` - HTTP POST transport (polling)
- **Features**:
  - Token-based authentication (JWT)
  - Capability negotiation
  - Remote configuration distribution
  - Health status tracking
  - Effective config reporting
  - Supervisor mode support
- **Responsibilities**:
  - Config distribution to gateways
  - Gateway registration
  - Health monitoring
  - Supervisor agent management

## Data Flow

1. **Template Creation**: User creates template in UI → Backend validates → Stored in PostgreSQL
2. **Deployment**: User creates deployment → Backend generates config bundle → OpAMP pushes to gateway
3. **Telemetry Processing**: Agents send data → Gateway applies transforms → Data sent to backends
4. **Monitoring**: Gateway reports health → Backend tracks status → UI displays metrics

## Multi-Tenancy

All entities are scoped by `org_id`:
- Templates
- Deployments
- Gateways
- Users

## Security

- JWT/OIDC for authentication (to be implemented)
- mTLS for OpAMP communication (to be implemented)
- Secrets management via Kubernetes Secrets
- PII redaction configurable per tenant

## Scalability

- **Backend**: Stateless, horizontally scalable
- **Frontend**: Stateless, horizontally scalable
- **Gateway**: Can be deployed as Deployment or DaemonSet
- **Database**: PostgreSQL with connection pooling

## Current Implementation Details

### Component Versions
- **OpenTelemetry Collector**: v0.130.0 (custom build with specific components)
- **OpAMP Supervisor**: v0.139.0
- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React + TypeScript + Vite
- **Database**: PostgreSQL 15
- **Cache**: Redis 7

### Gateway Modes

#### Supervisor Mode (Default)
- OpAMP Supervisor manages collector lifecycle
- Supervisor connects to backend OpAMP server
- Collector connects to supervisor's local OpAMP server (port 4321)
- Enhanced features: auto-restart, log management, status reporting
- Storage: `/var/lib/opampsupervisor`

#### Extension Mode
- Collector connects directly to backend OpAMP server
- Heartbeat service for status reporting
- Simpler architecture, fewer dependencies

### Supported Collector Components

**Receivers:**
- `otlp` (gRPC and HTTP)
- `prometheus`

**Processors:**
- `batch`
- `memory_limiter`

**Exporters:**
- `otlp`
- `otlphttp`
- `debug`

**Extensions:**
- `opamp`

All configurations are validated against this component whitelist to ensure compatibility.

### Network Ports

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Frontend | 5173 | HTTP | React dev server |
| Backend | 8000 | HTTP | REST API |
| OpAMP Server | 4320 | WebSocket/HTTP | OpAMP protocol |
| Gateway OTLP gRPC | 4317 | gRPC | Telemetry ingress |
| Gateway OTLP HTTP | 4318 | HTTP | Telemetry ingress |
| Gateway Metrics | 8888 | HTTP | Health/metrics |
| Supervisor Local | 4321 | WebSocket | Local OpAMP server |
| PostgreSQL | 5432 | TCP | Database |
| Redis | 6379 | TCP | Cache |

## Deployment Models

### Local Development
- Docker Compose with all services
- Hot-reload for development
- Volume mounts for live code updates

### Production
- Kubernetes with Helm charts
- Separate values for dev/staging/prod
- HA with multiple replicas
- Helm charts located in `helm/flowgate/`


