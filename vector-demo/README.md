# OpenTelemetry Demo Integration

This directory contains demo services for demonstrating the Flowgate Gateway pipeline.

## Architecture

```
OTEL Demo Service (Python) → Flowgate Gateway → Observability Backend Vector → Console
```

## Components

### 1. OpenTelemetry Demo Service (`otel-demo-service/`)
- **Language**: Python 3.11
- **Framework**: OpenTelemetry SDK
- **Functionality**: Generates metrics, logs, and traces using OTLP
- **Protocol**: OTLP HTTP (port 4318)
- **Features**:
  - Generates sample logs with various severity levels (INFO, WARN, ERROR, DEBUG)
  - Creates distributed traces with parent/child spans
  - Emits metrics (counters, histograms, up-down counters)
  - Sends all telemetry data to Flowgate Gateway via OTLP HTTP

### 2. Observability Backend Vector (`vector-observability-backend.toml`)
- **Source**: `http_server` - Receives logs from Flowgate Gateway
- **Sink**: `console` - Outputs logs to stdout in JSON format
- **Ports**: 
  - 4319 (gRPC) - Exposed for external access
  - 4321 (HTTP) - Exposed for external access

## Usage

Start the demo services:

```bash
docker compose -f docker-compose.yml -f docker-compose.vector-demo.yml up -d otel-demo-service vector-observability-backend
```

View logs:

```bash
# View demo service logs
docker compose -f docker-compose.yml -f docker-compose.vector-demo.yml logs -f otel-demo-service

# View backend receiving transformed telemetry
docker compose -f docker-compose.yml -f docker-compose.vector-demo.yml logs -f vector-observability-backend
```

Rebuild the demo service after code changes:

```bash
docker compose -f docker-compose.yml -f docker-compose.vector-demo.yml build otel-demo-service
docker compose -f docker-compose.yml -f docker-compose.vector-demo.yml up -d otel-demo-service
```

## Gateway Configuration

The Flowgate Gateway is configured to:
- Receive telemetry via OTLP (ports 4317 gRPC, 4318 HTTP)
- Process and transform metrics, logs, and traces
- Export to the observability backend Vector via OTLP (port 4317)

## Demo Service Configuration

The Python demo service generates:
- **Logs**: Every 1 second with random severity levels and messages
- **Traces**: Every 2 seconds with parent/child spans
- **Metrics**: Every 5 seconds (counters, histograms, up-down counters)

All telemetry is sent to the Flowgate Gateway at `http://gateway:4318` using OTLP HTTP protocol.

## Service Details

- **Service Name**: `otel-demo-service`
- **Version**: `1.0.0`
- **Environment**: `demo`
- **OTLP Endpoints**:
  - Logs: `http://gateway:4318/v1/logs`
  - Metrics: `http://gateway:4318/v1/metrics`
  - Traces: `http://gateway:4318/v1/traces`

