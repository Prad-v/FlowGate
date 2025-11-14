# FlowGate OpAMP Agent Management Architecture

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Data Flows](#data-flows)
5. [Security Architecture](#security-architecture)
6. [Deployment Architecture](#deployment-architecture)
7. [Operational Procedures](#operational-procedures)
8. [Scalability Considerations](#scalability-considerations)
9. [Future Enhancements](#future-enhancements)
10. [API Reference](#api-reference)
11. [Error Handling](#error-handling)
12. [Monitoring & Observability](#monitoring--observability)
13. [Security Best Practices](#security-best-practices)

## Overview

FlowGate's OpAMP (Open Agent Management Protocol) Agent Management system provides secure, scalable management of OpenTelemetry Collector gateways. This document describes the architecture, components, data flows, and operational procedures for the agent management system.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FlowGate Control Plane                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Frontend    │    │   Backend    │    │ OpAMP Server │     │
│  │     UI        │◄──►│     API      │◄──►│   (REST)     │     │
│  │  (React)      │    │  (FastAPI)   │    │              │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                   │                       │            │
│         │                   │                       │            │
│         └───────────────────┴───────────────────────┘            │
│                            │                                      │
│                            ▼                                      │
│                   ┌──────────────┐                               │
│                   │  PostgreSQL   │                               │
│                   │   Database    │                               │
│                   └──────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ OpAMP Protocol / REST API
                            │ (Heartbeat, Config, Status)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    Agent Layer (Gateways)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         OpenTelemetry Collector Gateway                  │  │
│  │                                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │   Collector   │  │  Heartbeat   │  │  Onboarding  │  │  │
│  │  │   Process     │  │   Service    │  │    Script    │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  │                                                           │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │         Collector Configuration                   │   │  │
│  │  │  - Receivers (OTLP, Prometheus)                  │   │  │
│  │  │  - Processors (Batch, Memory Limiter)             │   │  │
│  │  │  - Exporters (OTLP, Debug)                        │   │  │
│  │  │  - OpAMP Extension (when available)               │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend (React Application)

**Location**: `frontend/`

**Responsibilities**:
- Agent list display and filtering
- Real-time status monitoring (polling every 8 seconds)
- Agent detail views (health, version, metrics, configuration)
- Configuration viewer with copy/download functionality
- Error handling and user feedback

**Key Components**:
- `AgentManagement.tsx`: Main agent management page
- `AgentStatusBadge.tsx`: Status indicator component
- `HealthIndicator.tsx`: Health metrics display
- `AgentConfigViewer.tsx`: Configuration viewer

**API Integration**:
- Uses React Query for data fetching and caching
- Polls `/api/v1/gateways?org_id={org_id}` for agent list
- Fetches detailed status via `/api/v1/gateways/{gateway_id}/status`

### 2. Backend API (FastAPI)

**Location**: `backend/services/flowgate-backend/`

**Key Endpoints**:

#### Gateway Registration
- `POST /api/v1/gateways` - Register new gateway with registration token
  - Returns: `GatewayRegistrationResponse` with OpAMP token and endpoint
  - Authentication: Registration token (Bearer token)

#### Agent Status & Health
- `GET /api/v1/gateways/{gateway_id}/health` - Get agent health status
- `GET /api/v1/gateways/{gateway_id}/version` - Get agent version info
- `GET /api/v1/gateways/{gateway_id}/config` - Get agent configuration
- `GET /api/v1/gateways/{gateway_id}/metrics` - Get agent metrics
- `GET /api/v1/gateways/{gateway_id}/status` - Combined status (all above)
- `GET /api/v1/gateways?org_id={org_id}` - List all agents for organization

#### OpAMP Protocol Endpoints
- `POST /api/v1/opamp/heartbeat/{instance_id}` - Gateway heartbeat
- `GET /api/v1/opamp/config/{instance_id}` - Get configuration for gateway
- `POST /api/v1/opamp/v1/opamp` - OpAMP protocol endpoint (future)

**Services**:
- `GatewayService`: Gateway CRUD, health calculation, status aggregation
- `OpAMPService`: OpAMP token generation/validation, config distribution
- `RegistrationTokenService`: Registration token management

### 3. Database Schema

**Key Tables**:

#### `gateways`
- `id` (UUID): Primary key
- `instance_id` (String): Unique OpAMP instance identifier
- `org_id` (UUID): Organization identifier
- `name` (String): Human-readable gateway name
- `status` (Enum): `registered`, `active`, `inactive`, `error`
- `last_seen` (DateTime): Last heartbeat timestamp
- `current_config_version` (Integer): Currently deployed config version
- `opamp_token` (String): JWT token for OpAMP authentication
- `registration_token_id` (UUID): Reference to registration token used
- `extra_metadata` (JSONB): Version info, capabilities, metrics

#### `registration_tokens`
- `id` (UUID): Primary key
- `org_id` (UUID): Organization identifier
- `token` (String): Hashed token (SHA256 digest)
- `name` (String): Token description
- `expires_at` (DateTime): Token expiration
- `is_active` (Boolean): Token active status
- `created_by` (UUID): User who created the token

### 4. Gateway Agent

**Location**: `gateway/`

**Components**:

#### OpenTelemetry Collector
- Base image: `otel/opentelemetry-collector:latest` (distroless)
- Custom build: Debian-based with additional tools
- Configuration: `otel-collector-config.yaml`
- Receives telemetry via OTLP (gRPC/HTTP)
- Processes and routes to backends

#### Heartbeat Service
- Script: `heartbeat.sh`
- Sends periodic heartbeats to `/api/v1/opamp/heartbeat/{instance_id}`
- Interval: 30 seconds (configurable)
- Updates gateway `last_seen` timestamp
- Sets gateway status to `active`

#### Onboarding Script
- Script: `onboard.sh`
- Handles initial registration:
  1. Validates registration token
  2. Calls registration API
  3. Extracts OpAMP token and endpoint
  4. Saves token to persistent storage
  5. Updates collector configuration (if needed)

#### Docker Entrypoint
- Script: `docker-entrypoint.sh`
- Orchestrates startup:
  1. Runs onboarding if `REGISTRATION_TOKEN` provided
  2. Loads/saves OpAMP token
  3. Starts heartbeat service in background
  4. Starts collector process

## Data Flows

### 1. Gateway Registration Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Admin/UI   │         │   Backend    │         │  Gateway    │
└──────┬──────┘         └──────┬───────┘         └──────┬──────┘
       │                       │                        │
       │ 1. Create Reg Token   │                        │
       │──────────────────────►│                        │
       │                       │                        │
       │ 2. Return Token        │                        │
       │◄──────────────────────│                        │
       │                       │                        │
       │ 3. Provide Token      │                        │
       │───────────────────────────────────────────────►│
       │                       │                        │
       │                       │ 4. Register Gateway    │
       │                       │    (with reg token)    │
       │                       │◄───────────────────────│
       │                       │                        │
       │                       │ 5. Generate OpAMP Token│
       │                       │    Store in DB         │
       │                       │                        │
       │                       │ 6. Return OpAMP Token  │
       │                       │    & Endpoint          │
       │                       │───────────────────────►│
       │                       │                        │
       │                       │ 7. Save Token          │
       │                       │    Start Heartbeat     │
       │                       │                        │
```

**Steps**:
1. Admin creates registration token via UI or API
2. Backend returns plain token (one-time display)
3. Token provided to gateway (environment variable or manual)
4. Gateway calls `POST /api/v1/gateways` with registration token
5. Backend validates token, creates gateway record, generates OpAMP JWT token
6. Backend returns OpAMP token and endpoint URL
7. Gateway saves token, starts heartbeat service

### 2. Heartbeat Flow

```
┌─────────────┐                    ┌─────────────┐
│  Gateway    │                    │   Backend   │
│ Heartbeat   │                    │     API     │
│  Service    │                    │             │
└──────┬──────┘                    └──────┬──────┘
       │                                   │
       │  Every 30 seconds                  │
       │                                   │
       │ POST /opamp/heartbeat/gateway-1   │
       │ Authorization: Bearer <token>    │
       │──────────────────────────────────►│
       │                                   │
       │                                   │ 1. Validate OpAMP Token
       │                                   │ 2. Update last_seen
       │                                   │ 3. Set status = active
       │                                   │
       │ 200 OK                            │
       │ {status: "ok"}                    │
       │◄──────────────────────────────────│
       │                                   │
```

**Heartbeat Details**:
- **Endpoint**: `POST /api/v1/opamp/heartbeat/{instance_id}`
- **Authentication**: OpAMP JWT token (Bearer token)
- **Frequency**: Every 30 seconds (configurable)
- **Actions**:
  - Updates `gateways.last_seen` timestamp
  - Sets `gateways.status` to `active`
  - Optionally updates `current_config_version`

### 3. Health Calculation Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Frontend   │         │   Backend   │         │  Database   │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                        │
       │ GET /gateways/{id}/   │                        │
       │     status?org_id=...  │                        │
       │──────────────────────►│                        │
       │                       │                        │
       │                       │ Query Gateway          │
       │                       │───────────────────────►│
       │                       │                        │
       │                       │ Gateway Record         │
       │                       │◄───────────────────────│
       │                       │                        │
       │                       │ Calculate Health:     │
       │                       │ - last_seen age        │
       │                       │ - status enum          │
       │                       │ - uptime               │
       │                       │                        │
       │ Health Response       │                        │
       │◄──────────────────────│                        │
       │                       │                        │
```

**Health Calculation Logic**:
- **Healthy**: `last_seen` ≤ 60 seconds ago AND status = `active`
- **Warning**: `last_seen` ≤ 300 seconds (5 minutes) ago
- **Unhealthy**: `last_seen` > 300 seconds ago OR status = `error`
- **Offline**: status = `inactive` OR `error`

**Health Score**:
- 100: Healthy (last_seen ≤ 60s)
- 50: Warning (last_seen ≤ 300s)
- 20: Unhealthy (last_seen > 300s)
- 0: Offline (inactive/error status)

### 4. Configuration Retrieval Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Frontend   │         │   Backend   │         │  Database   │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                        │
       │ GET /gateways/{id}/   │                        │
       │     config?org_id=... │                        │
       │──────────────────────►│                        │
       │                       │                        │
       │                       │ 1. Get Gateway         │
       │                       │───────────────────────►│
       │                       │                        │
       │                       │ 2. Check Active        │
       │                       │    Deployment          │
       │                       │───────────────────────►│
       │                       │                        │
       │                       │ 3a. If Deployment:    │
       │                       │    Get Template Config │
       │                       │───────────────────────►│
       │                       │                        │
       │                       │ 3b. If No Deployment: │
       │                       │    Return Base Config  │
       │                       │                        │
       │ Config Response       │                        │
       │◄──────────────────────│                        │
       │                       │                        │
```

**Configuration Sources**:
1. **Active Deployment**: Configuration from deployed template version
2. **Base Configuration**: Default collector config (fallback)

## Security Architecture

### Authentication & Authorization

#### Registration Token
- **Purpose**: One-time secure registration
- **Format**: 48-byte random token (64 chars base64)
- **Storage**: Hashed using SHA256 (bcrypt has 72-byte limit)
- **Validation**: 
  - Token must be active (`is_active = true`)
  - Token must not be expired (`expires_at > now`)
  - Token must belong to organization
- **Usage**: Single-use for initial gateway registration

#### OpAMP Token
- **Purpose**: Long-term authentication for OpAMP operations
- **Format**: JWT (JSON Web Token)
- **Payload**:
  ```json
  {
    "sub": "<gateway_id>",
    "org_id": "<org_id>",
    "type": "opamp_token",
    "exp": <expiration_timestamp>,
    "iat": <issued_at_timestamp>
  }
  ```
- **Expiration**: 365 days (configurable)
- **Validation**:
  - JWT signature verification
  - Token type check (`type == "opamp_token"`)
  - Gateway existence and org_id match
  - Optional: Token matches stored `gateway.opamp_token`

### Token Flow

```
Registration Token Flow:
Admin → Create Token → Hash & Store → Provide to Gateway → Gateway Registers → Generate OpAMP Token

OpAMP Token Flow:
Gateway → Heartbeat/Config Request → Validate JWT → Verify Gateway → Process Request
```

## Deployment Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Frontend   │  │   Backend    │  │   Gateway    │     │
│  │  (React)     │  │  (FastAPI)   │  │  (OTel Col)  │     │
│  │  Port 5173   │  │  Port 8000   │  │  Port 4317/8  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  PostgreSQL  │  │    Redis     │                        │
│  │  Port 5432   │  │  Port 6379   │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Gateway Container Structure

```
gateway/
├── Dockerfile                 # Multi-stage build
├── docker-entrypoint.sh       # Startup orchestration
├── onboard.sh                 # Registration script
├── heartbeat.sh               # Heartbeat service
├── update-opamp-config.sh     # Config updater
└── otel-collector-config.yaml # Collector configuration
```

### Environment Variables

**Gateway Container**:
- `INSTANCE_ID`: Unique gateway instance identifier
- `GATEWAY_NAME`: Human-readable gateway name
- `REGISTRATION_TOKEN`: (Optional) Token for initial registration
- `OPAMP_TOKEN`: (Optional) OpAMP authentication token
- `OPAMP_SERVER_URL`: OpAMP server endpoint URL
- `BACKEND_URL`: FlowGate backend API URL
- `HEARTBEAT_INTERVAL`: Heartbeat interval in seconds (default: 30)

## Operational Procedures

### Initial Gateway Onboarding

1. **Create Registration Token**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/registration-tokens?org_id={org_id}" \
     -H "Content-Type: application/json" \
     -d '{"name": "Gateway Registration", "expires_in_days": 30}'
   ```

2. **Start Gateway with Registration Token**:
   ```bash
   export REGISTRATION_TOKEN="<token_from_step_1>"
   docker-compose up -d gateway
   ```

3. **Verify Registration**:
   - Check gateway appears in UI at `/agents`
   - Verify status becomes "Active" and "Healthy"
   - Check heartbeat logs: `docker-compose logs gateway | grep HEARTBEAT`

### Manual Heartbeat (Testing)

```bash
curl -X POST "http://localhost:8000/api/v1/opamp/heartbeat/gateway-1" \
  -H "Authorization: Bearer <opamp_token>"
```

### Viewing Agent Status

**Via API**:
```bash
curl "http://localhost:8000/api/v1/gateways/{gateway_id}/status?org_id={org_id}"
```

**Via UI**:
- Navigate to `/agents` page
- Click "Details" on any agent
- View health, version, metrics, and configuration

### Troubleshooting

#### Gateway Not Appearing
- Check registration token is valid and not expired
- Verify backend is accessible from gateway container
- Check gateway logs: `docker-compose logs gateway`

#### Gateway Shows as Unhealthy
- Verify heartbeat service is running: `docker-compose logs gateway | grep HEARTBEAT`
- Check OpAMP token is set: `docker-compose exec gateway env | grep OPAMP_TOKEN`
- Verify token file exists: `docker-compose exec gateway cat /var/lib/otelcol/opamp_token`
- Manually trigger heartbeat to test

#### Configuration Not Loading
- Check if active deployment exists for gateway
- Verify gateway has valid OpAMP token
- Check backend logs for errors
- Review error message in UI (should show clear error)

## Scalability Considerations

### Horizontal Scaling

- **Gateways**: Stateless, can scale horizontally
- **Backend API**: Stateless, can scale horizontally (shared database)
- **Database**: Use connection pooling, read replicas for scale

### Performance Optimizations

- **Heartbeat Batching**: Consider batching multiple gateway heartbeats
- **Caching**: Cache gateway status in Redis (future enhancement)
- **Database Indexing**: Index on `instance_id`, `org_id`, `last_seen`
- **Frontend Polling**: Adjustable polling interval (currently 8 seconds)

## Future Enhancements

### Planned Features

1. **Native OpAMP Extension Support**
   - Build custom collector with OpAMP extension
   - Replace REST-based heartbeat with native OpAMP protocol
   - Support OpAMP configuration push

2. **Real-time Updates**
   - WebSocket support for live status updates
   - Server-Sent Events (SSE) for configuration changes

3. **Advanced Monitoring**
   - Gateway performance metrics collection
   - Alerting on unhealthy gateways
   - Historical health trends

4. **Configuration Management**
   - Version control for configurations
   - Rollback capabilities
   - A/B testing of configurations

5. **Multi-Organization Support**
   - Organization isolation
   - Role-based access control (RBAC)
   - Audit logging

## API Reference

### Gateway Registration

**Endpoint**: `POST /api/v1/gateways`

**Request**:
```json
{
  "name": "FlowGate Gateway",
  "instance_id": "gateway-1",
  "hostname": "gateway.example.com",
  "ip_address": "192.168.1.100",
  "metadata": {
    "version": "1.0.0",
    "otel_version": "0.88.0",
    "capabilities": ["AcceptsRemoteConfig", "ReportsEffectiveConfig"]
  }
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "FlowGate Gateway",
  "instance_id": "gateway-1",
  "org_id": "uuid",
  "status": "registered",
  "opamp_token": "jwt_token",
  "opamp_endpoint": "http://backend:8000/api/v1/opamp/v1/opamp",
  "created_at": "2025-11-14T07:00:00Z"
}
```

### Heartbeat

**Endpoint**: `POST /api/v1/opamp/heartbeat/{instance_id}`

**Headers**:
- `Authorization: Bearer <opamp_token>`

**Response**:
```json
{
  "status": "ok",
  "gateway_id": "uuid"
}
```

### Agent Status

**Endpoint**: `GET /api/v1/gateways/{gateway_id}/status?org_id={org_id}`

**Response**:
```json
{
  "gateway_id": "uuid",
  "instance_id": "gateway-1",
  "name": "FlowGate Gateway",
  "health": {
    "status": "healthy",
    "last_seen": "2025-11-14T07:00:00Z",
    "seconds_since_last_seen": 15,
    "uptime_seconds": 3600,
    "health_score": 100
  },
  "version": {
    "agent_version": "1.0.0",
    "otel_version": "0.88.0",
    "capabilities": ["AcceptsRemoteConfig", "ReportsEffectiveConfig"]
  },
  "config": {
    "config_yaml": "...",
    "config_version": 1,
    "deployment_id": "uuid",
    "last_updated": "2025-11-14T07:00:00Z"
  },
  "metrics": {
    "logs_processed": 1000,
    "errors": 0,
    "latency_ms": 50.5,
    "last_updated": "2025-11-14T07:00:00Z"
  }
}
```

## Error Handling

### Common Errors

1. **Invalid Registration Token**
   - HTTP 401 Unauthorized
   - Message: "Invalid or expired registration token"

2. **Gateway Not Found**
   - HTTP 404 Not Found
   - Message: "Gateway not found"

3. **Invalid OpAMP Token**
   - HTTP 401 Unauthorized
   - Message: "Invalid OpAMP token"

4. **Instance ID Mismatch**
   - HTTP 403 Forbidden
   - Message: "Instance ID does not match token"

5. **Configuration Not Found**
   - HTTP 404 Not Found
   - Message: "Gateway not found or no active config"
   - Fallback: Returns base configuration

## Monitoring & Observability

### Metrics

**Gateway Metrics** (from metadata):
- `logs_processed`: Total logs processed
- `errors`: Error count
- `latency_ms`: Processing latency

**System Metrics**:
- Gateway count per organization
- Active vs inactive gateways
- Average health score
- Heartbeat success rate

### Logging

**Backend Logs**:
- Gateway registration events
- Heartbeat receipts
- Configuration updates
- Authentication failures

**Gateway Logs**:
- Heartbeat service status
- Onboarding process
- Collector startup/shutdown
- Configuration reloads

## Security Best Practices

1. **Token Management**:
   - Registration tokens: Short expiration (30 days default)
   - OpAMP tokens: Longer expiration (365 days), but rotate periodically
   - Never commit tokens to version control
   - Use secrets management in production

2. **Network Security**:
   - Use TLS for all API communications
   - Restrict gateway network access
   - Use private networks for internal communication

3. **Access Control**:
   - Implement RBAC for token creation
   - Audit token usage
   - Monitor for suspicious activity

4. **Data Protection**:
   - Encrypt sensitive data at rest
   - Use secure token storage
   - Implement token revocation

## Conclusion

The FlowGate OpAMP Agent Management system provides a secure, scalable solution for managing OpenTelemetry Collector gateways. The architecture supports:

- Secure registration with token-based authentication
- Real-time health monitoring and status tracking
- Configuration management and distribution
- Horizontal scalability
- Comprehensive error handling and user feedback

For questions or issues, refer to the troubleshooting section or check the gateway and backend logs.

