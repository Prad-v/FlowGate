# FlowGate OpAMP Implementation

## Overview

FlowGate implements the [Open Agent Management Protocol (OpAMP)](https://opentelemetry.io/docs/specs/opamp/) specification for managing OpenTelemetry Collector agents. This document describes the implementation details, architecture, and compliance with the OpAMP specification.

**Specification Reference**: [OpAMP Specification v1.0](https://opentelemetry.io/docs/specs/opamp/)

## Table of Contents

1. [Protocol Compliance](#protocol-compliance)
2. [Architecture Overview](#architecture-overview)
3. [Message Handling](#message-handling)
4. [Capabilities](#capabilities)
5. [Transport Mechanisms](#transport-mechanisms)
6. [Configuration Management](#configuration-management)
7. [Agent Modes](#agent-modes)
8. [Security Implementation](#security-implementation)
9. [Implementation Details](#implementation-details)
10. [Capability Negotiation](#capability-negotiation)
11. [Error Handling](#error-handling)
12. [Status Reporting](#status-reporting)

## Protocol Compliance

FlowGate's OpAMP implementation is **fully compliant** with the OpAMP v1.0 specification:

- ✅ **Protobuf Message Format**: All messages use the official OpAMP Protobuf schema
- ✅ **WebSocket Transport**: Primary transport mechanism (preferred per spec)
- ✅ **HTTP POST Transport**: Fallback transport for polling scenarios
- ✅ **Capability Negotiation**: Bit-field based capability exchange
- ✅ **Remote Configuration**: Full support for dynamic config distribution
- ✅ **Status Reporting**: Agent status, health, and effective config reporting
- ✅ **Sequence Numbers**: Proper message sequencing and ordering
- ✅ **Error Handling**: Spec-compliant error responses

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FlowGate OpAMP Server                    │
│  (FastAPI - backend/services/flowgate-backend)             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ OpAMP WebSocket  │  │  OpAMP HTTP     │               │
│  │    Router        │  │    Router       │               │
│  └────────┬─────────┘  └────────┬────────┘               │
│           │                     │                         │
│           └──────────┬──────────┘                         │
│                      │                                    │
│           ┌──────────▼──────────┐                        │
│           │ OpAMP Protocol      │                        │
│           │    Service          │                        │
│           └──────────┬──────────┘                        │
│                      │                                    │
│    ┌─────────────────┼─────────────────┐                │
│    │                 │                 │                │
│  ┌─▼──┐  ┌─────────▼────┐  ┌─────────▼────┐            │
│  │GW  │  │ Config        │  │ Package     │            │
│  │Svc │  │ Service       │  │ Service     │            │
│  └────┘  └───────────────┘  └─────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
                        │
                        │ OpAMP Protocol
                        │ (WebSocket/HTTP)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    OpAMP Agent (Gateway)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │  OpAMP Supervisor (v0.139.0)                  │          │
│  │  - Lifecycle Management                       │          │
│  │  - Local OpAMP Server (port 4321)            │          │
│  │  - Capability Reporting                       │          │
│  └──────────────┬───────────────────────────────┘          │
│                 │                                          │
│                 │ Local OpAMP                              │
│                 ▼                                          │
│  ┌──────────────────────────────────────────────┐          │
│  │  OTel Collector (v0.139.0)                   │          │
│  │  - OpAMP Extension                           │          │
│  │  - Telemetry Processing                      │          │
│  └────────────────────────────────────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Implementation Files

- **Backend**:
  - `backend/services/flowgate-backend/app/routers/opamp_websocket.py` - WebSocket transport
  - `backend/services/flowgate-backend/app/routers/opamp_protocol.py` - HTTP transport
  - `backend/services/flowgate-backend/app/services/opamp_protocol_service.py` - Protocol message handling
  - `backend/services/flowgate-backend/app/services/opamp_capabilities.py` - Capability definitions

- **Agent**:
  - `gateway/supervisor.yaml` - Supervisor configuration
  - `gateway/otel-collector-config-supervisor.yaml` - Collector config for supervisor mode
  - `gateway/otel-collector-config.yaml` - Collector config for extension mode

## Message Handling

### AgentToServer Messages

FlowGate processes the following `AgentToServer` message fields per the OpAMP specification:

#### Status Reporting
- **`agent_description`**: Agent identification and attributes
- **`capabilities`**: Agent capability bit-field
- **`sequence_num`**: Message sequence number for ordering

#### Remote Configuration
- **`remote_config_status`**: Status of remote config application
  - `UNSET`: No remote config applied
  - `APPLIED`: Remote config successfully applied
  - `APPLYING`: Remote config is being applied
  - `FAILED`: Remote config application failed
- **`last_remote_config_hash`**: Hash of last remote config received

#### Effective Configuration
- **`effective_config`**: Current effective configuration running on agent
  - `config_map`: Map of config files
  - `hash`: Hash of effective config

#### Telemetry Data
- **`metrics`**: Agent's own metrics (resource metrics, scope metrics)
- **`logs`**: Agent's own logs
- **`traces`**: Agent's own traces

#### Package Management
- **`package_statuses`**: Status of package installations/updates

#### Connection Settings
- **`connection_settings_status`**: Status of connection settings application

### ServerToAgent Messages

FlowGate sends the following `ServerToAgent` message fields:

#### Initial Message
- **`instance_uid`**: Unique instance identifier (16 bytes, UUID format)
- **`capabilities`**: Server capability bit-field
- **`remote_config`**: Initial remote configuration (if available)

#### Configuration Updates
- **`remote_config`**: Updated configuration when changes occur
  - `config`: Configuration map
  - `config_hash`: Hash of configuration

#### Package Offers
- **`packages_available`**: Available packages for download
  - Package metadata, download URLs, signatures

#### Connection Settings
- **`connection_settings`**: Connection settings offers
  - OpAMP connection settings
  - Other connection settings (TLS certificates, etc.)

#### Error Responses
- **`error_response`**: Error information when processing fails
  - `type`: Error type (INTERNAL_ERROR, BAD_REQUEST, etc.)
  - `message`: Human-readable error message

## Capabilities

### Agent Capabilities

FlowGate agents report capabilities differently depending on the management mode (supervisor vs extension). The following table shows all OpAMP capabilities and their status:

| Bit | Capability | Description | Supervisor Mode | Extension Mode |
|-----|------------|-------------|-----------------|----------------|
| 0 | `ReportsStatus` | Agent reports status | ✅ Always enabled | ✅ Always enabled |
| 1 | `AcceptsRemoteConfig` | Agent accepts remote configuration | ✅ Enabled | ⚠️ Not configurable |
| 2 | `ReportsEffectiveConfig` | Agent reports effective config | ✅ Enabled | ✅ Enabled |
| 3 | `AcceptsPackages` | Agent accepts package offers | ⚠️ Not supported | ⚠️ Not supported |
| 4 | `ReportsPackageStatuses` | Agent reports package status | ⚠️ Not supported | ⚠️ Not supported |
| 5 | `ReportsOwnTraces` | Agent reports own traces | ✅ Enabled | ⚠️ Not configurable |
| 6 | `ReportsOwnMetrics` | Agent reports own metrics | ✅ Enabled | ⚠️ Not configurable |
| 7 | `ReportsOwnLogs` | Agent reports own logs | ✅ Enabled | ⚠️ Not configurable |
| 8 | `AcceptsOpAMPConnectionSettings` | Agent accepts OpAMP connection settings | ✅ Enabled | ⚠️ Not configurable |
| 9 | `AcceptsOtherConnectionSettings` | Agent accepts other connection settings | ⚠️ Not supported | ⚠️ Not supported |
| 10 | `AcceptsRestartCommand` | Agent accepts restart commands | ✅ Enabled | ⚠️ Not configurable |
| 11 | `ReportsHealth` | Agent reports health status | ✅ Enabled | ✅ Enabled |
| 12 | `ReportsRemoteConfig` | Agent reports remote config status | ✅ Enabled | ⚠️ Not configurable |
| 13 | `ReportsHeartbeat` | Agent sends heartbeat messages | ✅ Enabled | ⚠️ Not configurable |
| 14 | `ReportsAvailableComponents` | Agent reports available components | ✅ Enabled | ✅ Enabled |
| 15 | `ReportsConnectionSettingsStatus` | Agent reports connection settings status | ⚠️ Not supported | ⚠️ Not supported |

**Supervisor Mode Capabilities**: 
- In supervisor mode, capabilities are configured in `gateway/supervisor.yaml` and reported by the OpAMP Supervisor.
- The supervisor supports **11 configurable capabilities** plus `ReportsStatus` (always enabled).
- Capabilities not in the supervisor's config struct (e.g., `AcceptsPackages`) are not supported.
- If the supervisor reports 0x0 capabilities, the backend automatically infers capabilities from the supervisor.yaml configuration.
- **Expected bit-field**: `0x1FFF` (8191) - All 12 supervisor-supported capabilities enabled.

**Extension Mode Capabilities**:
- In extension mode, capabilities are reported directly by the collector's OpAMP extension.
- The OpAMP extension supports **3 configurable capabilities** (all default to true per [config.go](https://raw.githubusercontent.com/open-telemetry/opentelemetry-collector-contrib/main/extension/opampextension/config.go)):
  - `ReportsEffectiveConfig` (bit 2, 0x04)
  - `ReportsHealth` (bit 11, 0x800)
  - `ReportsAvailableComponents` (bit 14, 0x4000)
- Plus `ReportsStatus` (bit 0, 0x01) - always enabled, hardcoded in extension's `toAgentCapabilities()` method.
- **Expected bit-field**: `0x4805` (18437) = ReportsStatus (0x01) + ReportsEffectiveConfig (0x04) + ReportsHealth (0x800) + ReportsAvailableComponents (0x4000)
- Other capabilities are not configurable in the extension and may be handled automatically or via protocol negotiation.
- Reference: https://raw.githubusercontent.com/open-telemetry/opentelemetry-collector-contrib/main/extension/opampextension/config.go

**Supervisor Mode with Extension**:
- In supervisor mode, the collector's OpAMP extension connects to the supervisor's local OpAMP server (not directly to FlowGate).
- The supervisor acts as a proxy between the collector extension and FlowGate server.
- The supervisor reports its own capabilities to FlowGate (from `supervisor.yaml`).
- The collector extension reports limited capabilities to the supervisor (from collector config).
- **Known Limitation**: The OpAMP extension may report incomplete `effective_config` (missing some components like debug exporters, telemetry settings).
  - Reference: https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/29117
  - The effective_config should be treated as a partial view, not the complete configuration.

**Reference**: 
- Supervisor config: https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/cmd/opampsupervisor/supervisor/config/config.go
- Extension config: https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/extension/opampextension/config.go
- Extension code: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/extension/opampextension

### Server Capabilities

FlowGate server reports all standard capabilities:

| Bit | Capability | Description | Status |
|-----|------------|-------------|--------|
| 0 | `AcceptsStatus` | Server accepts status reports | ✅ Enabled |
| 1 | `OffersRemoteConfig` | Server offers remote configuration | ✅ Enabled |
| 2 | `AcceptsEffectiveConfig` | Server accepts effective config | ✅ Enabled |
| 3 | `OffersPackages` | Server offers packages | ✅ Enabled |
| 4 | `AcceptsPackagesStatus` | Server accepts package status | ✅ Enabled |
| 5 | `OffersConnectionSettings` | Server offers connection settings | ✅ Enabled |
| 6 | `AcceptsConnectionSettingsRequest` | Server accepts connection settings requests | ✅ Enabled |

**Server Capability Bit-Field**: `0x7F` (127) - All 7 standard capabilities enabled

## Transport Mechanisms

### WebSocket Transport (Preferred)

**Endpoint**: `ws://backend:8000/api/v1/opamp/v1/opamp?token={OPAMP_TOKEN}`

**Implementation**: `backend/services/flowgate-backend/app/routers/opamp_websocket.py`

**Features**:
- Bidirectional real-time communication
- Binary Protobuf message encoding
- Automatic reconnection handling
- Connection status tracking

**Message Flow**:
1. Agent initiates WebSocket connection with token
2. Server validates token and accepts connection
3. Server sends initial `ServerToAgent` message
4. Agent sends `AgentToServer` messages
5. Server responds with `ServerToAgent` messages
6. Continuous bidirectional message exchange

**Authentication**:
- Token via query parameter: `?token={OPAMP_TOKEN}`
- Token via Authorization header: `Authorization: Bearer {OPAMP_TOKEN}`

### HTTP POST Transport (Polling)

**Endpoint**: `POST http://backend:8000/api/v1/opamp/v1/opamp?token={OPAMP_TOKEN}`

**Implementation**: `backend/services/flowgate-backend/app/routers/opamp_protocol.py`

**Features**:
- Polling-based communication
- Binary Protobuf message encoding
- Suitable for environments where WebSocket is not available

**Message Flow**:
1. Agent sends `AgentToServer` message via POST
2. Server responds with `ServerToAgent` message
3. Agent polls for updates periodically

## Configuration Management

### Remote Configuration

FlowGate implements full remote configuration support per OpAMP specification:

#### Configuration Distribution
- **Deployment-Based**: Configurations are organized into deployments
- **Versioning**: Each deployment has a version number
- **Targeting**: Deployments can target specific agents via tags
- **Rollout Strategies**: Immediate or gradual rollout

#### Configuration Validation
- **Component Whitelist**: Only allowed components can be used
  - Receivers: `otlp`, `prometheus`
  - Processors: `batch`, `memory_limiter`
  - Exporters: `otlp`, `otlphttp`, `debug`
  - Extensions: `opamp`
- **YAML Validation**: Syntax and structure validation
- **Dry-Run Support**: Test configurations before deployment

#### Configuration Application
1. Server sends `remote_config` in `ServerToAgent` message
2. Agent validates configuration
3. Agent applies configuration
4. Agent reports status via `remote_config_status`
5. Agent reports effective config via `effective_config`

#### Configuration Hashing
- Configurations are hashed for change detection
- Agent reports `last_remote_config_hash` to confirm receipt
- Server tracks `remote_config_hash` and `effective_config_hash`

### Effective Configuration

Agents report their effective configuration:
- **Format**: YAML configuration map
- **Hash**: SHA-256 hash of configuration
- **Purpose**: Server can verify what agent is actually running

## Agent Modes

### Supervisor Mode (Default)

**Configuration**: `gateway/supervisor.yaml`

**Architecture**:
```
OpAMP Server (FlowGate Backend)
    ↕ OpAMP Protocol (WebSocket)
OpAMP Supervisor (v0.139.0)
    ↕ Local OpAMP (ws://localhost:4321/v1/opamp)
OTel Collector (v0.139.0) with OpAMP Extension
```

**Features**:
- Lifecycle management (auto-restart on crash)
- Enhanced status reporting
- Log management
- Process monitoring
- Capability reporting from supervisor config

**Supervisor Configuration**:
```yaml
capabilities:
  accepts_remote_config: true
  reports_remote_config: true
  reports_effective_config: true
  reports_own_metrics: true
  reports_own_logs: true
  reports_own_traces: true
  reports_health: true
  reports_heartbeat: true
  accepts_opamp_connection_settings: true
  reports_available_components: true
  accepts_restart_command: true
```

**Reference**: [Supervisor Config Source](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/cmd/opampsupervisor/supervisor/config/config.go)

### Extension Mode

**Configuration**: `gateway/otel-collector-config.yaml`

**Architecture**:
```
OpAMP Server (FlowGate Backend)
    ↕ OpAMP Protocol (WebSocket/HTTP)
OTel Collector (v0.139.0) with OpAMP Extension
```

**Features**:
- Direct connection to OpAMP server
- Simpler architecture
- Heartbeat service for status reporting

**Extension Configuration**:
```yaml
extensions:
  opamp:
    server:
      ws:
        endpoint: ${OPAMP_WS_URL}/api/v1/opamp/v1/opamp
        headers:
          Authorization: "Bearer ${OPAMP_TOKEN}"
    capabilities:
      reports_effective_config: true
      reports_health: true
      reports_available_components: true
      # Note: ReportsStatus is always enabled (hardcoded in extension)
```

**Reference**: [Extension Config Source](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/extension/opampextension/config.go)

## Security Implementation

### Authentication

**Token-Based Authentication**:
- JWT tokens issued during gateway registration
- Tokens contain `instance_id` and `org_id`
- Tokens validated on every OpAMP message

**Token Validation**:
```python
# Token structure
{
  "sub": "instance_id",
  "org_id": "organization_id",
  "type": "opamp_token",
  "exp": expiration_timestamp
}
```

### Transport Security

**TLS Support**:
- TLS configuration available in supervisor and extension configs
- `insecure_skip_verify: true` for development (should be `false` in production)
- Certificate validation per OpAMP spec recommendations

### Configuration Security

**Component Restrictions**:
- Only whitelisted components can be used in remote configs
- Prevents execution of arbitrary code
- Validates against known safe components

**Configuration Validation**:
- All remote configs validated before distribution
- YAML syntax validation
- Component existence validation
- Structure validation

## Implementation Details

### Message Processing Flow

```python
# 1. Receive AgentToServer message
agent_message = parse_agent_message(message_bytes)

# 2. Extract and store data
- Update heartbeat timestamp
- Store sequence number
- Extract and store capabilities
- Extract remote config status
- Extract effective config
- Extract telemetry data

# 3. Process based on capabilities
if agent_capabilities & ACCEPTS_REMOTE_CONFIG:
    # Send remote config if available
    server_message.remote_config = get_remote_config()

if agent_capabilities & REPORTS_OWN_METRICS:
    # Store agent metrics
    store_agent_metrics(agent_message.metrics)

# 4. Build ServerToAgent response
server_message = build_server_message(instance_id)

# 5. Send response
send_server_message(server_message)
```

### Capability Inference

For supervisor-managed agents that report 0x0 capabilities, FlowGate infers capabilities from the supervisor configuration:

```python
if agent_capabilities == 0 and management_mode == "supervisor":
    # Infer from supervisor.yaml
    inferred_capabilities = calculate_from_supervisor_config()
    agent_capabilities = inferred_capabilities
```

This ensures capabilities are properly displayed even if the supervisor doesn't report them correctly.

### Sequence Number Handling

- Sequence numbers track message ordering
- Used for detecting out-of-order messages
- Stored in database for tracking
- Per OpAMP spec: sequence numbers are optional but recommended

### Status Tracking

FlowGate tracks the following agent status:

- **Connection Status**: `connected`, `disconnected`, `failed`, `never_connected`
- **Remote Config Status**: `UNSET`, `APPLIED`, `APPLYING`, `FAILED`
- **Transport Type**: `websocket`, `http`, `none`
- **Last Seen**: Timestamp of last heartbeat
- **Sequence Number**: Last received sequence number

## Capability Negotiation

### Negotiation Process

1. **Initial Exchange**:
   - Agent sends `AgentToServer` with `capabilities` bit-field
   - Server sends `ServerToAgent` with `capabilities` bit-field

2. **Capability Matching**:
   - Server only uses capabilities that agent supports
   - Agent only uses capabilities that server supports
   - Intersection of capabilities determines available features

3. **Dynamic Updates**:
   - Capabilities can change over time
   - Both sides adjust behavior based on peer capabilities

### Capability Bit-Field Calculation

```python
# Agent capabilities from supervisor.yaml
capabilities = {
    REPORTS_STATUS,                    # 0x01
    ACCEPTS_REMOTE_CONFIG,             # 0x02
    REPORTS_EFFECTIVE_CONFIG,          # 0x04
    REPORTS_OWN_METRICS,               # 0x40
    REPORTS_OWN_LOGS,                  # 0x80
    REPORTS_OWN_TRACES,                # 0x20
    REPORTS_HEALTH,                    # 0x800
    REPORTS_REMOTE_CONFIG,             # 0x1000
    REPORTS_HEARTBEAT,                 # 0x2000
    ACCEPTS_OPAMP_CONNECTION_SETTINGS, # 0x100
    REPORTS_AVAILABLE_COMPONENTS,      # 0x4000
    ACCEPTS_RESTART_COMMAND,           # 0x400
}

# Calculate bit-field
bit_field = 0
for cap in capabilities:
    bit_field |= (1 << cap)

# Result: 0x1FFF (or similar depending on enabled capabilities)
```

## Error Handling

### Error Response Types

FlowGate implements the following error types per OpAMP spec:

- **`INTERNAL_ERROR`**: Server internal error
- **`BAD_REQUEST`**: Invalid message format or content
- **`UNAVAILABLE`**: Server overloaded (triggers retry with backoff)

### Error Response Format

```protobuf
error_response {
    type: INTERNAL_ERROR
    message: "Human-readable error message"
    retry_info {
        retry_after_nanoseconds: 30000000000  // 30 seconds
    }
}
```

### Retry Logic

- **WebSocket**: Client disconnects and reconnects with exponential backoff
- **HTTP**: Client respects `Retry-After` header or implements exponential backoff
- **Minimum Retry Interval**: 30 seconds (per OpAMP spec recommendation)

## Status Reporting

### Agent Status

Agents report status via `agent_description`:

- **Identifying Attributes**: Unique agent identification
  - `service.name`: Service name
  - `service.instance.id`: Instance identifier
- **Non-Identifying Attributes**: Additional metadata
  - `host.name`: Hostname
  - `os.type`: Operating system
  - `os.description`: OS description

### Health Reporting

Agents report health status:
- **Health Status**: Included in status messages
- **Health Metrics**: Reported via `reports_own_metrics` capability
- **Health Checks**: Server can query agent health

### Effective Config Reporting

Agents report effective configuration:
- **Config Map**: YAML configuration files
- **Config Hash**: SHA-256 hash for verification
- **Purpose**: Server verifies what agent is actually running

## Package Management

FlowGate supports OpAMP package management:

### Package Offers

Server can offer packages to agents:
- **Package Metadata**: Name, version, type
- **Download URL**: URL for package download
- **Content Hash**: SHA-256 hash for verification
- **Signature**: Optional code signature for verification

### Package Status

Agents report package installation status:
- **Status**: `INSTALLED`, `INSTALLING`, `INSTALL_FAILED`
- **Version**: Installed package version
- **Error Message**: Error details if installation failed

## Connection Settings Management

FlowGate supports OpAMP connection settings:

### OpAMP Connection Settings

- **TLS Certificates**: Server can provide TLS certificates
- **Connection Parameters**: Server can update connection parameters
- **Status Reporting**: Agents report connection settings application status

### Other Connection Settings

- **Destination Settings**: Settings for telemetry destinations
- **TLS Configuration**: TLS certificates for exporters
- **Authentication**: Credentials for backend connections

## Implementation Compliance Checklist

### Protocol Compliance

- ✅ Protobuf message format (binary encoding)
- ✅ WebSocket transport (preferred)
- ✅ HTTP POST transport (polling)
- ✅ Capability bit-fields
- ✅ Sequence numbers
- ✅ Error responses
- ✅ Status reporting
- ✅ Remote configuration
- ✅ Effective config reporting
- ✅ Telemetry data extraction

### Security Compliance

- ✅ Token-based authentication
- ✅ TLS support
- ✅ Configuration validation
- ✅ Component whitelisting
- ✅ Hash verification

### Interoperability

- ✅ Partial implementation support
- ✅ Capability negotiation
- ✅ Graceful degradation
- ✅ Future capability extensions (reserved bits)

## References

- **OpAMP Specification**: https://opentelemetry.io/docs/specs/opamp/
- **Supervisor Config Reference**: https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/cmd/opampsupervisor/supervisor/config/config.go
- **Supervisor Test Config**: https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/cmd/opampsupervisor/supervisor/testdata/merged_local_config.yaml
- **FlowGate Architecture**: [Architecture Documentation](architecture.md)
- **Agent Management**: [Agent Management Architecture](agent-management-architecture.md)

## Version Information

- **OpAMP Specification**: v1.0
- **OpAMP Supervisor**: v0.139.0
- **OpenTelemetry Collector**: v0.139.0
- **OpAMP Extension**: v0.139.0
- **Backend**: FastAPI (Python 3.11+)

## Troubleshooting

### Agent Capabilities Not Reported (0x0)

**Symptoms**: Agent capabilities show as `0x0` in the UI or backend logs.

**Possible Causes**:
1. **Supervisor not reading capabilities from supervisor.yaml**
   - Check that `gateway/supervisor.yaml` has capabilities properly configured
   - Verify supervisor is reading the correct config file
   - Check supervisor logs for configuration errors

2. **Supervisor version issue**
   - Ensure supervisor version is v0.139.0 or later
   - Older versions may have capability reporting bugs

3. **Configuration file not found or not processed**
   - Verify `supervisor.yaml` exists in container at `/etc/opampsupervisor/supervisor.yaml`
   - Check that `envsubst` processed environment variables correctly
   - Review `docker-entrypoint.sh` logs

**Solutions**:
1. **Backend Inference (Automatic)**: FlowGate backend automatically infers capabilities from supervisor.yaml configuration when supervisor reports 0x0. This is a workaround that ensures capabilities are displayed correctly.

2. **Verify Supervisor Configuration**:
   ```bash
   docker compose exec gateway cat /etc/opampsupervisor/supervisor.yaml | grep -A 30 "capabilities:"
   ```

3. **Check Supervisor Logs**:
   ```bash
   docker compose logs gateway | grep -i "capabilit\|error\|fail"
   ```

4. **Rebuild Gateway Image**: If configuration changes aren't being picked up:
   ```bash
   docker compose build gateway
   docker compose restart gateway
   ```

### Capabilities Mismatch Between Supervisor and Extension

**Symptoms**: Different capabilities reported in supervisor mode vs extension mode.

**Explanation**: This is expected behavior:
- **Supervisor mode**: Reports 12 capabilities (0x1FFF)
- **Extension mode**: Reports 4 capabilities (0x4805) - ReportsStatus + ReportsEffectiveConfig + ReportsHealth + ReportsAvailableComponents

The supervisor has more capability support than the OpAMP extension. Use supervisor mode for full capability support.

### Capabilities Not Matching Documentation

**Symptoms**: Agent reports different capabilities than documented.

**Possible Causes**:
1. Supervisor version differences
2. Configuration not properly applied
3. Backend inference logic mismatch

**Solutions**:
1. Verify supervisor version matches documentation (v0.139.0)
2. Check actual supervisor.yaml configuration in container
3. Review backend logs for capability inference messages
4. Compare reported capabilities with expected bit-fields:
   - Supervisor mode: `0x1FFF` (8191)
   - Extension mode: `0x4805` (18437) - ReportsStatus (0x01) + ReportsEffectiveConfig (0x04) + ReportsHealth (0x800) + ReportsAvailableComponents (0x4000)

### Extension Mode Capabilities Limited

**Symptoms**: Extension mode reports fewer capabilities than supervisor mode.

**Explanation**: This is by design. The OpAMP extension in the collector only supports 3 configurable capabilities:
- `ReportsEffectiveConfig`
- `ReportsHealth`
- `ReportsAvailableComponents`

Plus `ReportsStatus` (always enabled).

For full capability support, use supervisor mode.

## Future Enhancements

- [ ] mTLS for OpAMP communication
- [ ] Certificate Authority integration
- [ ] Code signing verification for packages
- [ ] Advanced retry strategies
- [ ] Connection pooling optimization
- [ ] Metrics for OpAMP protocol performance
- [ ] Enhanced capability reporting in OpAMP extension
- [ ] Automatic capability validation on startup

