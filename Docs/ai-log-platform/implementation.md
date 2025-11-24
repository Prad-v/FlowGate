# AI-Augmented IT Log Management Platform

## Implementation Guide (React UI + Python Backend + Vector.dev Pipeline)

This README describes how to implement the architecture in this repo using:

- **React** frontend (suitable for Cursor IDE)
- **Python** backend (FastAPI or similar)
- **Vector.dev** as the primary log pipeline
- **NATS/Kafka**, **OTEL**, and **AI agents** as described in `ai-log-platform-architecture.md`

The goal is a modular, production-friendly structure you can gradually harden.

---

## 1. High-Level System Overview

**Frontend (React):**

- SecOps & AIOps dashboards
- Identity governance views (risk scores, access requests)
- Threat and incident views (MITRE TTP mapping, timelines)
- Policy authoring & JITA/JITP workflows
- SOAR playbook viewer & run history

**Backend (Python):**

- REST/GraphQL APIs for UI
- Log/alert query APIs (proxy to SIEM/log store)
- AI agent orchestration layer
- Identity governance/JITA decision APIs
- SOAR orchestration hooks
- Integration with Vector.dev/OTEL ingestion and NATS/Kafka

**Pipeline (Vector.dev + OTEL):**

- Agents on hosts, services, and network devices
- Normalization, routing, enrichment, and multi-tenant metadata
- Output to log store, SIEM, graph DB, and feature store

---

## 2. Suggested Repository Structure

```bash
repo-root/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── access.py          # JITA/JITP access APIs
│   │   │   │   ├── identity.py        # Identity governance endpoints
│   │   │   │   ├── threats.py         # Threat alerts, TTP mappings
│   │   │   │   ├── incidents.py       # Correlation & RCA APIs
│   │   │   │   ├── personas.py        # Persona baseline & anomalies
│   │   │   │   └── soar.py            # Playbook-trigger and status APIs
│   │   ├── core/
│   │   │   ├── config.py              # Settings, env vars
│   │   │   ├── db.py                  # DB connections (Postgres, Neo4j, etc.)
│   │   │   ├── messaging.py           # NATS/Kafka clients
│   │   │   └── logging.py             # Structured logging, OTEL traces
│   │   ├── models/
│   │   │   ├── access.py
│   │   │   ├── identity.py
│   │   │   ├── events.py
│   │   │   ├── incidents.py
│   │   │   └── personas.py
│   │   ├── services/
│   │   │   ├── identity_governance.py # IGA agent orchestration
│   │   │   ├── threat_vector.py       # TVA agent orchestration
│   │   │   ├── correlation_rca.py     # CRA orchestration
│   │   │   ├── persona_baseline.py    # PBA orchestration
│   │   │   └── soar_automation.py     # SAA orchestration
│   │   ├── agents/
│   │   │   ├── embeddings.py          # Embedding model helpers
│   │   │   ├── rules_engine.py        # Policy/rule evaluation
│   │   │   └── ml_models.py           # ML model wrappers (if local)
│   │   ├── main.py                    # FastAPI entrypoint
│   │   └── __init__.py
│   ├── tests/
│   └── pyproject.toml / requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts              # Axios/fetch wrapper
│   │   │   ├── access.ts              # Access/JITA APIs
│   │   │   ├── threats.ts             # Threat data APIs
│   │   │   ├── incidents.ts           # RCA APIs
│   │   │   └── personas.ts            # Persona anomaly APIs
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── charts/
│   │   │   ├── tables/
│   │   │   └── common/
│   │   ├── pages/
│   │   │   ├── AccessRequests/
│   │   │   ├── Threats/
│   │   │   ├── Incidents/
│   │   │   ├── Personas/
│   │   │   └── SoarPlaybooks/
│   │   ├── hooks/
│   │   ├── store/                     # Zustand/Redux if needed
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts / next.config.js
│
├── pipeline/
│   ├── vector/
│   │   ├── vector.yaml                # Vector pipeline configuration
│   ├── otel/
│   │   ├── collector-config.yaml      # OTEL collector configuration
│   └── docker-compose.pipeline.yaml   # Optional local stack
│
├── docs/
│   ├── ai-log-platform-architecture.md
│   └── diagrams/
│
├── docker-compose.yaml
└── README.md
```

---

## 3. Backend: Python (FastAPI) Essentials

### 3.1 Tech Stack

- **FastAPI** for HTTP APIs
- **Uvicorn**/Gunicorn for serving FastAPI
- **SQL DB**: Postgres (potentially with **pgvector**)
- **Graph DB**: Neo4j/Arango for access graph
- **Vector store**: pgvector/Weaviate for embeddings
- **Messaging**: NATS/Kafka client
- **OTEL**: `opentelemetry-instrumentation-fastapi`, `opentelemetry-exporter-otlp`

### 3.2 Example FastAPI Entrypoint

```python
# backend/app/main.py
from fastapi import FastAPI
from app.api.v1 import access, identity, threats, incidents, personas, soar

app = FastAPI(title="AI-Augmented Log Platform API")

app.include_router(access.router, prefix="/api/v1/access", tags=["access"])
app.include_router(identity.router, prefix="/api/v1/identity", tags=["identity"])
app.include_router(threats.router, prefix="/api/v1/threats", tags=["threats"])
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(personas.router, prefix="/api/v1/personas", tags=["personas"])
app.include_router(soar.router, prefix="/api/v1/soar", tags=["soar"])
```

Each router calls into **services** which orchestrate messages to the AI agents and storage.

---

## 4. Frontend: React UI Essentials

### 4.1 Tech Stack

- **React + TypeScript**
- **Vite** or Next.js
- Component library (e.g., MUI, Chakra, shadcn/ui)
- Charting library (e.g., Recharts, ECharts)
- State management (Zustand/Redux) if needed

### 4.2 Example: Threats Dashboard Page

- Table of current threats: severity, TTP, entity, status.
- MITRE ATT&CK mapping visual (matrix or tags).
- Timeline of events via RCA data from backend.
- Actions: trigger SOAR playbook, assign to analyst, add notes.

The frontend should **not** do heavy logic; it calls backend APIs that already provide enriched, filtered data.

---

## 5. Vector.dev Pipeline

### 5.1 Core Pattern

- Collect logs from identity providers, PAM, endpoints, and network infrastructure.
- Normalize and add labels (tenant, cluster, region, environment, auth_provider, etc).
- Send to:
  - SIEM/log store (Loki/VictoriaLogs/OpenSearch)
  - OTEL collector (for metrics/traces/logs)
  - NATS/Kafka for real-time agents

### 5.2 Sample Vector Configuration (Skeleton)

```toml
# pipeline/vector/vector.yaml (TOML or YAML depending on version)

[sources.identity_logs]
  type = "file"
  include = ["/var/log/identity/*.log"]

[transforms.normalize_identity]
  type = "remap"
  inputs = ["identity_logs"]
  source = '''
  .tenant = .labels.tenant ?? "default"
  .provider = .labels.provider ?? "okta"
  '''

[sinks.to_siem]
  type = "http"
  inputs = ["normalize_identity"]
  uri = "https://siem.example.com/ingest"
  encoding.codec = "json"

[sinks.to_bus]
  type = "kafka"
  inputs = ["normalize_identity"]
  bootstrap_servers = "kafka:9092"
  topic = "normalized-identity-logs"
```

Extend this for other sources (PAM, endpoints, network, app logs) and destinations (OTEL, NATS).

---

## 6. Running Locally (Dev)

### 6.1 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker / Docker Compose
- Optional: Kafka/NATS/Neo4j/Postgres via compose

### 6.2 Steps

1. **Backend**

   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Pipeline (Optional Local Stack)**

   ```bash
   docker-compose -f pipeline/docker-compose.pipeline.yaml up
   ```

4. Configure **Vector.dev agents** on your local machine or containers to send logs to the pipeline.

---

## 7. Best Practices

- Treat **AI agents** as **stateless orchestration + stateless inference**, with state offloaded to DBs and vector stores.
- Use **OpenTelemetry** everywhere for observability of the platform itself.
- Define **RBAC and tenancy boundaries** early in the backend architecture.
- Keep **playbook definitions** (SOAR) as code in a version-controlled repo.
- Integrate **policy-as-code** (OPA/Kyverno style) for IAM and JITA guardrails.

For a deep-dive on the architecture and flows, see `docs/ai-log-platform-architecture.md`.
