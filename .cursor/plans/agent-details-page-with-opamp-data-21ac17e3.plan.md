<!-- 21ac17e3-61af-4218-9a68-76f888d03031 92e6ad26-9499-4c24-a8c2-3431ff900c27 -->
# Config Retrieval and Comparison System Implementation

## Overview

Implement comprehensive config retrieval system with tracking IDs, system template management, and git diff comparison view for comparing agent effective configs against standard templates.

## 1. System Template Management

### 1.1 Create System Template Model/Storage

- **File**: `backend/services/flowgate-backend/app/models/system_template.py` (new)
- Add `SystemTemplate` model to store default collector config template
- Fields: `id`, `name`, `config_yaml`, `description`, `is_active`, `created_at`, `updated_at`
- Mark as system template (not org-scoped, global)

### 1.2 Initialize System Template from YAML

- **File**: `backend/services/flowgate-backend/app/services/system_template_service.py` (new)
- Create service to read `gateway/otel-collector-config-supervisor-gateway-2.yaml`
- Load YAML content and store as system template named "Default Collector Config (Supervisor Mode)"
- Add migration or initialization script to populate on first run

### 1.3 System Template API Endpoint

- **File**: `backend/services/flowgate-backend/app/routers/system_template.py` (new)
- `GET /api/v1/system-templates/default` - Get default system template
- `PUT /api/v1/system-templates/default` - Update default system template (admin only)

## 2. Config Request Tracking System

### 2.1 Config Request Model

- **File**: `backend/services/flowgate-backend/app/models/config_request.py` (new)
- Fields: `id` (UUID, tracking ID), `instance_id`, `org_id`, `status` (pending/completed/failed), `requested_at`, `completed_at`, `effective_config_content`, `effective_config_hash`, `error_message`
- Track config requests with unique tracking IDs

### 2.2 Enhanced Request Config Endpoint

- **File**: `backend/services/flowgate-backend/app/routers/supervisor_ui.py`
- Update `POST /agents/{instance_id}/request-effective-config`:
- Create `ConfigRequest` record with tracking ID
- For WebSocket connections: Store WebSocket connection reference, send immediate `ServerToAgent` message with `ReportFullState` flag
- For HTTP connections: Mark pending, will be processed on next agent message
- Return tracking ID in response: `{"tracking_id": "...", "status": "requested", "message": "..."}`

### 2.3 WebSocket Connection Manager

- **File**: `backend/services/flowgate-backend/app/services/websocket_manager.py` (new)
- Maintain active WebSocket connections per instance_id
- Methods: `register_connection(instance_id, websocket)`, `get_connection(instance_id)`, `send_message(instance_id, message)`, `unregister_connection(instance_id)`
- Update `opamp_websocket.py` to register/unregister connections

### 2.4 Config Request Status Endpoint

- **File**: `backend/services/flowgate-backend/app/routers/supervisor_ui.py`
- `GET /agents/{instance_id}/config-requests/{tracking_id}` - Get request status and config
- Return: `{"tracking_id": "...", "status": "...", "effective_config": {...}, "requested_at": "...", "completed_at": "..."}`

### 2.5 Update OpAMP Protocol Service

- **File**: `backend/services/flowgate-backend/app/services/opamp_protocol_service.py`
- When `effective_config` is received in `AgentToServer` message:
- Find pending `ConfigRequest` for this instance_id
- Update `ConfigRequest` with config content and mark as completed
- Store config in gateway's `opamp_effective_config_content`

## 3. Frontend: Enhanced Request Config UI

### 3.1 Update Request Config Button

- **File**: `frontend/src/pages/AgentDetails.tsx`
- Update `handleRequestEffectiveConfig`:
- Show loading state with tracking ID
- Poll for config request status every 2 seconds
- Display tracking ID as clickable link
- Show success/error states

### 3.2 Config Request Status Component

- **File**: `frontend/src/components/ConfigRequestStatus.tsx` (new)
- Display tracking ID, status, timestamps
- Link to view config when completed
- Auto-refresh until completed

### 3.3 API Service Updates

- **File**: `frontend/src/services/api.ts`
- Add `getConfigRequestStatus(instanceId, trackingId, orgId)` method
- Update `requestEffectiveConfig` to return tracking ID

## 4. Config Comparison and Diff View

### 4.1 Backend Comparison Endpoint

- **File**: `backend/services/flowgate-backend/app/routers/supervisor_ui.py`
- `POST /agents/{instance_id}/compare-config`:
- Accept: `{"standard_config_id": "..."}` or `{"standard_config_yaml": "..."}`
- Get agent's effective config from database
- Get standard config (system template or provided YAML)
- Use `difflib` or `diff-match-patch` to generate unified diff
- Return: `{"diff": "...", "agent_config": "...", "standard_config": "...", "diff_stats": {"added": X, "removed": Y, "modified": Z}}`

### 4.2 Diff Calculation Service

- **File**: `backend/services/flowgate-backend/app/services/config_diff_service.py` (new)
- `calculate_unified_diff(agent_config, standard_config)` - Generate git-style unified diff
- `calculate_line_diff(agent_config, standard_config)` - Line-by-line comparison
- `calculate_stats(agent_config, standard_config)` - Calculate diff statistics

### 4.3 Frontend Diff Viewer Component

- **File**: `frontend/src/components/ConfigDiffViewer.tsx` (new)
- Props: `agentConfig`, `standardConfig`, `diff`, `viewMode` ('unified' | 'side-by-side')
- Unified view: Git-style diff with +/- lines, line numbers
- Side-by-side view: Two columns with highlighted differences
- Toggle button to switch between views
- Syntax highlighting for YAML
- Scroll synchronization for side-by-side view

### 4.4 Update Agent Details Page

- **File**: `frontend/src/pages/AgentDetails.tsx`
- Add "Compare with Standard Config" button in Effective Configuration section
- Modal or expandable section showing diff view
- Allow selecting standard config (system template or custom YAML)
- Display diff stats (lines added/removed/modified)

### 4.5 Diff View Styling

- Use `react-syntax-highlighter` for YAML syntax highlighting
- Color coding: green for additions, red for deletions, yellow for modifications
- Line numbers for both views
- Responsive layout for side-by-side view

## 5. Database Migrations

### 5.1 Config Request Table

- **File**: `backend/services/flowgate-backend/alembic/versions/XXX_add_config_requests.py` (new)
- Create `config_requests` table with all required fields
- Add indexes on `instance_id`, `tracking_id`, `status`

### 5.2 System Template Table

- **File**: `backend/services/flowgate-backend/alembic/versions/XXX_add_system_templates.py` (new)
- Create `system_templates` table
- Insert default template from YAML file in migration

## 6. Testing

### 6.1 Backend Tests

- Test config request creation and tracking
- Test WebSocket immediate message sending
- Test config comparison diff generation
- Test system template initialization

### 6.2 Frontend Tests

- Test config request flow with tracking ID
- Test diff viewer component rendering
- Test view mode toggle
- Test config comparison API integration

## Implementation Order

1. System template model and initialization
2. Config request tracking model and endpoints
3. WebSocket connection manager and immediate trigger
4. Frontend request config UI with tracking
5. Config comparison backend service
6. Frontend diff viewer component
7. Integration and testing

### To-dos

- [ ] Create SystemTemplate model and database table for storing default collector config template
- [ ] Create service to initialize system template from otel-collector-config-supervisor-gateway-2.yaml file
- [ ] Create API endpoints for system template management (GET/PUT /system-templates/default)
- [ ] Create ConfigRequest model and database table for tracking config requests with unique IDs
- [ ] Create WebSocket connection manager service to track active connections and send immediate messages
- [ ] Update request-effective-config endpoint to create tracking ID and trigger immediate message for WebSocket connections
- [ ] Create endpoint to get config request status by tracking ID (GET /agents/{instance_id}/config-requests/{tracking_id})
- [ ] Update OpAMP protocol service to update ConfigRequest records when effective_config is received
- [ ] Update opamp_websocket.py to register/unregister connections with WebSocket manager
- [ ] Update frontend Request Config button to show tracking ID and poll for status
- [ ] Create config diff service to calculate unified diff and statistics between agent and standard configs
- [ ] Create POST /agents/{instance_id}/compare-config endpoint to generate diff between agent and standard config
- [ ] Create ConfigDiffViewer React component with unified and side-by-side view modes
- [ ] Integrate diff viewer into AgentDetails page with Compare button and modal/expandable section
- [ ] Create Alembic migrations for config_requests and system_templates tables