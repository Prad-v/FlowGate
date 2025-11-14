# Flowgate Architecture

## Overview

Flowgate is an observability optimization gateway that sits between observability agents and backends (Datadog, GCP Monitoring, Grafana, etc.). It reduces costs by dropping unused metrics, reducing high-cardinality labels, and transforming logs.

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

- **Technology**: OpenTelemetry Collector distribution
- **Responsibilities**:
  - Ingests telemetry from agents (OTLP, Prometheus, FluentBit)
  - Applies transformations (drop, filter, transform, route)
  - Routes optimized data to backends
  - Managed via OpAMP (no manual config)

### 2. Control Plane (Backend)

- **Technology**: FastAPI (Python)
- **Responsibilities**:
  - Template management and versioning
  - Config validation and dry-run
  - Deployment orchestration
  - Gateway registration and health tracking
  - OpAMP server for config distribution

### 3. Frontend

- **Technology**: React + TypeScript + TailwindCSS
- **Responsibilities**:
  - Dashboard with metrics and health
  - Template management UI
  - Log transformer studio
  - Deployment management

### 4. OpAMP Server

- **Technology**: FastAPI
- **Responsibilities**:
  - Config distribution to gateways
  - Gateway registration
  - Health monitoring

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

## Deployment Models

### Local Development
- Docker Compose with all services
- Hot-reload for development

### Production
- Kubernetes with Helm charts
- Separate values for dev/staging/prod
- HA with multiple replicas


