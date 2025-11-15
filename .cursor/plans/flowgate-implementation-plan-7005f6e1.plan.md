<!-- 7005f6e1-30b2-4c10-9952-c5c7b008b1f7 9a5b8363-ef02-42a6-a971-c87f47eec3a4 -->
# OpAMP Supervisor and Example Server Integration

## Overview

Integrate the official OpAMP Supervisor (from OpenTelemetry Collector releases) and example server functionality into FlowGate, enabling dual-mode operation: direct OpAMP extension connection and supervisor-managed mode. Enhance the existing backend with example server features and add supervisor management UI.

## Requirements

1. **Dual Mode Support**: Support both OpAMP extension (direct) and Supervisor (managed) modes
2. **Supervisor Integration**: Add opampsupervisor binary and configuration to gateway
3. **Example Server Features**: Integrate example server capabilities into existing FastAPI backend
4. **UI Enhancements**: Add supervisor management features to existing agent management UI
5. **Backward Compatibility**: Maintain existing extension-based functionality

## Implementation Plan

### 1. Gateway: OpAMP Supervisor Integration

**File**: `gateway/Dockerfile`

- Add stage to download opampsupervisor binary from GitHub releases
- Support supervisor version configuration via build arg
- Copy supervisor binary to `/usr/local/bin/opampsupervisor`
- Make supervisor executable

**File**: `gateway/supervisor.yaml` (new)

- Create supervisor configuration file
- Configure server endpoint (WebSocket URL to backend)
- Set capabilities (accepts_remote_config, reports_effective_config, reports_own_metrics, reports_own_logs, reports_health, reports_remote_config)
- Configure agent executable path (`/otelcol`)
- Set storage directory (`/var/lib/opampsupervisor`)
- Configure TLS settings (insecure_skip_verify for development)

**File**: `gateway/docker-entrypoint.sh`

- Add environment variable `USE_SUPERVISOR` (default: false)
- If `USE_SUPERVISOR=true`:
- Use supervisor to manage collector (start supervisor instead of collector directly)
- Supervisor will launch collector as subprocess
- If `USE_SUPERVISOR=false` (default):
- Continue using direct OpAMP extension (current behavior)
- Support supervisor configuration via environment variables

**File**: `gateway/README.md`

- Document supervisor mode vs extension mode
- Add supervisor configuration examples
- Document supervisor storage and logs location

### 2. Backend: Example Server Feature Integration

**File**: `backend/services/flowgate-backend/app/services/opamp_supervisor_service.py` (new)

- Service for managing supervisor-specific operations
- Methods:
- `get_supervisor_status(instance_id)`: Get supervisor health/status
- `get_supervisor_logs(instance_id)`: Retrieve supervisor logs
- `get_agent_description(instance_id)`: Get agent description from supervisor
- `restart_agent_via_supervisor(instance_id)`: Request agent restart

**File**: `backend/services/flowgate-backend/app/routers/supervisor.py` (new)

- Endpoints for supervisor management:
- `GET /api/v1/supervisor/agents`: List all supervisor-managed agents
- `GET /api/v1/supervisor/agents/{instance_id}/status`: Get supervisor status for agent
- `GET /api/v1/supervisor/agents/{instance_id}/logs`: Get supervisor logs
- `POST /api/v1/supervisor/agents/{instance_id}/restart`: Restart agent via supervisor
- `GET /api/v1/supervisor/agents/{instance_id}/description`: Get agent description

**File**: `backend/services/flowgate-backend/app/models/gateway.py`

- Add column `management_mode`: Enum (extension, supervisor) - default: extension
- Add column `supervisor_status`: JSONB (store supervisor-specific status)
- Add column `supervisor_logs_path`: String (path to supervisor logs)

**File**: `backend/services/flowgate-backend/alembic/versions/004_add_supervisor_support.py` (new migration)

- Add `management_mode` enum and column to gateways table
- Add `supervisor_status` JSONB column
- Add `supervisor_logs_path` string column

**File**: `backend/services/flowgate-backend/app/services/opamp_protocol_service.py`

- Enhance to detect supervisor vs extension mode
- Handle supervisor-specific message fields (agent_description, health)
- Support supervisor capabilities negotiation

**File**: `backend/services/flowgate-backend/app/routers/opamp_websocket.py`

- Detect if agent is supervisor-managed or extension-based
- Handle supervisor-specific OpAMP messages
- Store supervisor status in gateway model

### 3. Backend: Example Server UI Features

**File**: `backend/services/flowgate-backend/app/routers/supervisor_ui.py` (new)

- Endpoints matching example server UI functionality:
- `GET /api/v1/supervisor/ui/agents`: Get agents list for UI (with supervisor status)
- `GET /api/v1/supervisor/ui/agents/{instance_id}`: Get agent details for UI
- `POST /api/v1/supervisor/ui/agents/{instance_id}/config`: Push config via supervisor UI
- `GET /api/v1/supervisor/ui/agents/{instance_id}/effective-config`: Get effective config

### 4. Frontend: Supervisor Management UI

**File**: `frontend/src/pages/AgentManagement.tsx`

- Add "Management Mode" column (Extension/Supervisor badge)
- Add supervisor status indicator for supervisor-managed agents
- Add "Supervisor Logs" button in agent detail modal
- Add "Restart via Supervisor" button for supervisor-managed agents
- Show supervisor-specific status fields

**File**: `frontend/src/components/SupervisorStatus.tsx` (new)

- Component to display supervisor status
- Shows supervisor health, agent process status
- Displays supervisor logs viewer
- Shows agent description from supervisor

**File**: `frontend/src/components/SupervisorConfigEditor.tsx` (new)

- Component for pushing config via supervisor (similar to example server UI)
- YAML editor with validation
- "Save and Send to Agent" button
- Shows effective config comparison

**File**: `frontend/src/pages/SupervisorManagement.tsx` (new)

- Dedicated page for supervisor management
- List of all supervisor-managed agents
- Supervisor status dashboard
- Bulk operations (restart, config push)

**File**: `frontend/src/services/api.ts`

- Add `supervisorApi` methods:
- `listAgents()`: List supervisor-managed agents
- `getStatus(instanceId)`: Get supervisor status
- `getLogs(instanceId)`: Get supervisor logs
- `restartAgent(instanceId)`: Restart agent
- `getAgentDescription(instanceId)`: Get agent description
- `pushConfig(instanceId, config)`: Push config via supervisor UI

### 5. Docker Compose Updates

**File**: `docker-compose.yml`

- Add environment variable `USE_SUPERVISOR` to gateway service (default: false)
- Add volume mount for supervisor storage: `./gateway/supervisor-storage:/var/lib/opampsupervisor`
- Document supervisor mode usage

### 6. Documentation Updates

**File**: `docs/agent-management-architecture.md`

- Add section on Supervisor vs Extension modes
- Document supervisor architecture
- Add supervisor configuration examples
- Document supervisor storage and logs

**File**: `gateway/README.md`

- Add supervisor setup instructions
- Document supervisor.yaml configuration
- Add troubleshooting for supervisor mode

### 7. Testing & Validation

- Test supervisor mode: Start gateway with `USE_SUPERVISOR=true`
- Verify supervisor launches collector as subprocess
- Test config push via supervisor
- Test supervisor status reporting
- Verify backward compatibility (extension mode still works)
- Test UI supervisor management features

## Implementation Notes

1. **Supervisor Binary**: Download from GitHub releases (cmd/opampsupervisor tags)
2. **Dual Mode**: Use environment variable to switch between modes
3. **Storage**: Supervisor stores state in `/var/lib/opampsupervisor`
4. **Logs**: Supervisor logs available via API endpoint
5. **Backward Compatibility**: Default to extension mode (current behavior)
6. **Example Server UI**: Integrate features but maintain FlowGate UI design consistency

## Migration Path

- Existing agents continue using extension mode (default)
- New agents can opt into supervisor mode via `USE_SUPERVISOR=true`
- Both modes can coexist in the same deployment
- UI shows management mode for each agent

### To-dos

- [ ] Add GET /api/v1/gateways/{gateway_id}/health endpoint to calculate and return agent health status
- [ ] Add GET /api/v1/gateways/{gateway_id}/version endpoint to extract and return version information from metadata
- [ ] Add GET /api/v1/gateways/{gateway_id}/config endpoint to retrieve current agent configuration
- [ ] Add GET /api/v1/gateways/{gateway_id}/status endpoint returning combined health, version, and config info
- [ ] Create Pydantic schemas for AgentHealthResponse, AgentVersionResponse, AgentConfigResponse, AgentStatusResponse
- [ ] Add service methods: get_agent_health, get_agent_version, get_agent_config, get_agent_metrics
- [ ] Create AgentManagement.tsx page with agent list table showing status, health, version, last_seen
- [ ] Create agent detail view/modal showing health metrics, version info, and configuration
- [ ] Add agentApi methods to frontend/src/services/api.ts for health, version, config, status endpoints
- [ ] Create AgentStatusBadge, HealthIndicator, and AgentConfigViewer components
- [ ] Add /agents route to frontend router pointing to AgentManagement page
- [ ] Implement React Query polling for real-time agent status updates (5-10 second interval)