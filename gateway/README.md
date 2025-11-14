# FlowGate Gateway - OpAMP Agent Management

This directory contains the OpenTelemetry Collector gateway configuration and onboarding scripts for FlowGate's OpAMP Agent Management system.

## Overview

The gateway is an OpenTelemetry Collector instance that:
- Receives telemetry data (logs, metrics, traces) via OTLP
- Applies transformations and routing rules (managed via OpAMP)
- Forwards processed data to observability backends
- Connects to FlowGate's OpAMP server for remote configuration management

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

## Configuration

### Environment Variables

The gateway supports the following environment variables:

- `INSTANCE_ID`: Unique identifier for this gateway instance (default: `gateway-1`)
- `GATEWAY_NAME`: Display name for the gateway (default: same as `INSTANCE_ID`)
- `REGISTRATION_TOKEN`: Registration token for initial onboarding (optional if already onboarded)
- `OPAMP_TOKEN`: OpAMP access token (auto-set after onboarding)
- `OPAMP_SERVER_URL`: OpAMP server endpoint (default: `http://backend:8000`)
- `BACKEND_URL`: FlowGate backend URL (default: `http://backend:8000`)

### OpAMP Configuration

The OpAMP extension is configured in `otel-collector-config.yaml`:

```yaml
extensions:
  opamp:
    server:
      endpoint: ${OPAMP_SERVER_URL}/api/v1/opamp/v1/opamp
      headers:
        Authorization: "Bearer ${OPAMP_TOKEN}"
    instance_id: ${INSTANCE_ID}
    capabilities:
      - AcceptsRemoteConfig
      - ReportsEffectiveConfig
      - ReportsOwnTelemetry
```

## Files

- `otel-collector-config.yaml`: OpenTelemetry Collector configuration
- `onboard.sh`: Onboarding script that registers the gateway
- `update-opamp-config.sh`: Script to update OpAMP token in config
- `docker-entrypoint.sh`: Docker entrypoint that handles onboarding
- `Dockerfile`: Gateway container image definition

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
4. Check collector logs for OpAMP extension errors

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

## Next Steps

After onboarding:
1. Gateway will appear in FlowGate UI under "Agents"
2. You can deploy configurations to the gateway via FlowGate
3. Gateway will receive configuration updates via OpAMP
4. Monitor gateway health and metrics in the UI

