# Vector Demo Integration

This directory contains Vector configurations for demonstrating the Flowgate Gateway pipeline.

## Architecture

```
Vector Demo Logs → Flowgate Gateway → Observability Backend Vector → Console
```

## Components

### 1. Vector Demo Logs (`vector-demo-logs.toml`)
- **Source**: `demo_logs` - Generates fake Apache common log format entries
- **Sink**: `http` - Sends logs to Flowgate Gateway
- **Note**: Vector 0.34.0 doesn't have native OpenTelemetry sink support. For production use, consider:
  - Using a newer Vector version with OpenTelemetry support
  - Using the OTLP HTTP endpoint directly with proper OTLP JSON format
  - Using a Vector transform to convert logs to OTLP format

### 2. Observability Backend Vector (`vector-observability-backend.toml`)
- **Source**: `http_server` - Receives logs from Flowgate Gateway
- **Sink**: `console` - Outputs logs to stdout in JSON format
- **Ports**: 
  - 4319 (gRPC) - Exposed for external access
  - 4321 (HTTP) - Exposed for external access

## Usage

Start the Vector demo services:

```bash
docker compose -f docker-compose.yml -f docker-compose.vector-demo.yml up -d vector-demo-logs vector-observability-backend
```

View logs:

```bash
# View demo logs being generated
docker compose -f docker-compose.yml -f docker-compose.vector-demo.yml logs -f vector-demo-logs

# View backend receiving transformed logs
docker compose -f docker-compose.yml -f docker-compose.vector-demo.yml logs -f vector-observability-backend
```

## Gateway Configuration

The Flowgate Gateway is configured to:
- Receive logs via OTLP (ports 4317 gRPC, 4318 HTTP)
- Process and transform logs
- Export to the observability backend Vector via OTLP (port 4317)

## Limitations

- Vector 0.34.0 doesn't support native OpenTelemetry sink/source
- Current implementation uses HTTP as a workaround
- For full OTLP support, upgrade to a newer Vector version or use proper OTLP formatting

