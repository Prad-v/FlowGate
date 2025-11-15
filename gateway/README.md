# FlowGate Gateway - OpAMP Agent Management

This directory contains the OpenTelemetry Collector gateway configuration and onboarding scripts for FlowGate's OpAMP Agent Management system.

## Overview

The gateway is a **custom-built OpenTelemetry Collector** instance that includes the OpAMP extension for agent management. The collector is built from source using the OpenTelemetry Collector Builder to include OpAMP support.

The gateway:
- Receives telemetry data (logs, metrics, traces) via OTLP
- Applies transformations and routing rules (managed via OpAMP)
- Forwards processed data to observability backends
- Connects to FlowGate's OpAMP server for remote configuration management
- Supports all standard OpAMP capabilities for comprehensive agent management

## Quick Start

### 1. Get a Registration Token

First, you need to obtain a registration token from FlowGate:

```bash
# Via API (replace ORG_ID with your organization ID)
curl -X POST "http://localhost:8000/api/v1/registration-tokens?org_id=<ORG_ID>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Gateway Registration Token", "expires_in_days": 30}'
```

Save the `token` value from the response - you'll need it for onboarding.

### 2. Onboard the Gateway

#### Option A: Using Docker Compose (Recommended)

Set the `REGISTRATION_TOKEN` environment variable and start the gateway:

```bash
export REGISTRATION_TOKEN="your-registration-token-here"
docker-compose up gateway
```

The gateway will automatically:
1. Register with FlowGate using the registration token
2. Receive an OpAMP access token
3. Configure itself to connect to the OpAMP server
4. Start the collector with OpAMP extension enabled

#### Option B: Manual Onboarding

If the gateway is already running, you can onboard it manually:

```bash
docker-compose exec gateway /usr/local/bin/onboard.sh
```

Or set the environment variable and restart:

```bash
docker-compose exec gateway bash -c "export REGISTRATION_TOKEN='your-token' && /usr/local/bin/onboard.sh"
```

### 3. Verify Registration

Check that the gateway appears in FlowGate:

```bash
# List gateways (replace ORG_ID)
curl "http://localhost:8000/api/v1/gateways?org_id=<ORG_ID>"
```

Or visit the FlowGate UI at `http://localhost:5173/agents` to see the registered gateway.

### 4. Registration Failure Handling

If registration fails:

**Behavior**:
- The collector will still start (for telemetry collection)
- OpAMP extension will fail to connect (no OPAMP_TOKEN)
- Heartbeat service will not start (requires OPAMP_TOKEN)
- Clear error messages will be logged

**Recovery**:
1. Check the error message in the gateway logs
2. Verify the registration token is valid and not expired
3. Ensure backend connectivity
4. Restart registration using the restart endpoint:

```bash
# Restart registration (requires registration token)
curl -X POST "http://localhost:8000/api/v1/gateways/{gateway_id}/restart-registration?org_id=<ORG_ID>" \
  -H "Authorization: Bearer <registration-token>" \
  -H "Content-Type: application/json"
```

Or use the FlowGate UI: Navigate to the agent detail view and click "Restart Registration" if registration failed.

## Configuration

### Environment Variables

The gateway supports the following environment variables:

- `INSTANCE_ID`: Unique identifier for this gateway instance (default: `gateway-1`)
- `GATEWAY_NAME`: Display name for the gateway (default: same as `INSTANCE_ID`)
- `REGISTRATION_TOKEN`: Registration token for initial onboarding (optional if already onboarded)
  - **Required** for first-time registration
  - If registration fails, collector still starts but OpAMP connection will fail
- `OPAMP_TOKEN`: OpAMP access token (auto-set after onboarding, persisted to `/var/lib/otelcol/opamp_token`)
  - **Required** for OpAMP extension and heartbeat service
  - If missing, OpAMP extension fails to connect and heartbeat service does not start
- `OPAMP_SERVER_URL`: OpAMP server endpoint (default: `http://backend:8000`)
- `BACKEND_URL`: FlowGate backend URL (default: `http://backend:8000`)

### Custom Collector Build

The gateway uses a custom-built OpenTelemetry Collector that includes the OpAMP extension. The build process:

1. **Builder Configuration**: `builder-config.yaml` defines the collector components
   - OpAMP extension from `github.com/open-telemetry/opentelemetry-collector-contrib/extension/opampextension`
   - Standard receivers (OTLP, Prometheus)
   - Standard processors (batch, memory_limiter)
   - Standard exporters (OTLP, OTLP HTTP, debug)

2. **Build Process**: The Dockerfile uses a multi-stage build:
   - Stage 1: Builds the custom collector binary using the OpenTelemetry Collector Builder
   - Stage 2: Creates the final image with the custom binary and necessary tools

3. **Build Requirements**:
   - Go 1.21+ (installed in builder stage)
   - OpenTelemetry Collector Builder tool
   - All dependencies are handled during the Docker build

To build the gateway image:
```bash
make build-gateway
# or
docker-compose build gateway
```

### OpAMP Configuration

**Status**: OpAMP extension is **enabled** and fully compliant with the [OpAMP specification](https://opentelemetry.io/docs/specs/opamp/).

The gateway uses the OpAMP extension for agent management with the following features:

**Transport**: WebSocket (ws:// or wss://) - preferred transport per OpAMP spec
- Endpoint: `${OPAMP_WS_URL}/api/v1/opamp/v1/opamp`
- Persistent bidirectional connection
- Real-time configuration updates
- Automatic reconnection

**Configuration**:
```yaml
extensions:
  opamp:
    server:
      ws:
        endpoint: ${OPAMP_WS_URL}/api/v1/opamp/v1/opamp
        headers:
          Authorization: "Bearer ${OPAMP_TOKEN}"

service:
  extensions: [opamp]
```

**OpAMP Protocol Features**:
- **Capability Negotiation**: Automatic negotiation of agent and server capabilities using bit-fields
- **Remote Configuration**: Server can push configuration updates to agents
- **Status Reporting**: Agents report effective configuration, health, and telemetry
- **Message Sequencing**: Proper message sequencing and state management
- **Error Handling**: Proper error responses per OpAMP specification

**Protocol Compliance**:
- Implements AgentToServer and ServerToAgent message types
- Supports capability bit-fields as per specification
- Handles WebSocket transport with proper connection lifecycle
- Supports HTTP transport (alternative) for long-polling scenarios
- Implements proper error responses and throttling

**Note**: The gateway also maintains a heartbeat script for backward compatibility, but the primary communication channel is via the OpAMP protocol extension.

## Files

- `builder-config.yaml`: OpenTelemetry Collector Builder configuration for building custom collector
- `otel-collector-config.yaml`: OpenTelemetry Collector configuration with OpAMP extension
- `onboard.sh`: Onboarding script that registers the gateway
- `update-opamp-config.sh`: Script to update OpAMP token in config
- `docker-entrypoint.sh`: Docker entrypoint that handles onboarding
- `Dockerfile`: Multi-stage Dockerfile that builds custom collector and creates final image
- `heartbeat.sh`: Script for sending periodic heartbeats to OpAMP server

## Troubleshooting

### Gateway Not Appearing in UI

1. Check gateway logs: `docker-compose logs gateway`
2. Verify registration token is valid: Check token hasn't expired
3. Ensure backend is accessible from gateway container
4. Check that organization exists in database

### OpAMP Connection Issues

1. Verify OpAMP token is set: `docker-compose exec gateway env | grep OPAMP_TOKEN`
2. Check OpAMP server is running: `docker-compose ps opamp-server`
3. Verify network connectivity: `docker-compose exec gateway curl http://backend:8000/health`
4. Check collector logs for OpAMP extension errors: `docker-compose logs gateway | grep -i opamp`
5. Verify OpAMP extension is loaded: Check logs for "OpAMP extension started" or similar messages
6. Ensure custom collector was built correctly: Check build logs for builder errors

### Build Issues

If the custom collector build fails:

1. **Builder not found**: Ensure Go is available in the build environment
2. **Module download errors**: Check network connectivity during build
3. **Version conflicts**: Verify `builder-config.yaml` uses compatible component versions
4. **Binary not found**: Check that builder output path matches Dockerfile COPY path

To rebuild from scratch:
```bash
docker-compose build --no-cache gateway
```

### Configuration Not Updating

1. Ensure gateway is registered and has valid OpAMP token
2. Check that a deployment/template is active for this gateway
3. Verify OpAMP extension is enabled in collector config
4. Check collector logs for OpAMP protocol errors

## Manual Operations

### Update OpAMP Token

If you need to update the OpAMP token manually:

```bash
docker-compose exec gateway /usr/local/bin/update-opamp-config.sh <new_token> <opamp_endpoint> /etc/otelcol/config.yaml
```

### Re-onboard Gateway

To re-register a gateway:

```bash
docker-compose exec gateway /usr/local/bin/onboard.sh
```

Make sure `REGISTRATION_TOKEN` is set in the environment.

## Security Notes

- Registration tokens are one-time use credentials - store them securely
- OpAMP tokens are long-lived (default 365 days) - rotate periodically
- Never commit tokens to version control
- Use environment variables or secrets management for production

## Supervisor Mode

FlowGate supports two management modes for agents:

### Extension Mode (Default)

The gateway uses the OpAMP extension built into the collector. This is the default mode and provides direct OpAMP protocol communication.

**Configuration**: No special configuration needed - this is the default behavior.

### Supervisor Mode

The gateway uses the OpAMP Supervisor to manage the collector lifecycle. The supervisor launches the collector as a subprocess and provides enhanced management capabilities.

**To enable Supervisor Mode**:

1. Set the `USE_SUPERVISOR` environment variable to `true`:
   ```bash
   export USE_SUPERVISOR=true
   docker-compose up gateway
   ```

2. The supervisor will:
   - Launch the collector as a subprocess
   - Manage collector lifecycle (restart on failure)
   - Provide enhanced status reporting
   - Store state in `/var/lib/opampsupervisor`

**Supervisor Configuration**:

The supervisor uses `/etc/opampsupervisor/supervisor.yaml` (or the default at `/usr/local/share/supervisor.yaml`). Key settings:

```yaml
server:
  endpoint: ${OPAMP_WS_URL}/api/v1/opamp/v1/opamp
  tls:
    insecure_skip_verify: true

capabilities:
  accepts_remote_config: true
  reports_effective_config: true
  reports_own_logs: true
  reports_health: true
  reports_remote_config: true

agent:
  executable: /otelcol

storage:
  directory: /var/lib/opampsupervisor
```

**Supervisor Features**:

- **Lifecycle Management**: Supervisor automatically restarts the collector if it crashes
- **Enhanced Status**: Reports agent description and health information
- **Log Management**: Supervisor logs available via API
- **Process Monitoring**: Tracks collector process status

**Switching Between Modes**:

- To switch from Extension to Supervisor: Set `USE_SUPERVISOR=true` and restart
- To switch from Supervisor to Extension: Set `USE_SUPERVISOR=false` and restart
- Both modes can coexist in the same deployment

**Supervisor Logs**:

Supervisor logs are stored in `/var/lib/opampsupervisor` and can be accessed via:
- FlowGate UI: Click "Logs" button for supervisor-managed agents
- API: `GET /api/v1/supervisor/agents/{instance_id}/logs`

## Next Steps

After onboarding:
1. Gateway will appear in FlowGate UI under "Agents"
2. You can deploy configurations to the gateway via FlowGate
3. Gateway will receive configuration updates via OpAMP
4. Monitor gateway health and metrics in the UI
5. For supervisor-managed agents, use supervisor-specific features (logs, restart, config push)

