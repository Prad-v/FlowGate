# Flowgate OTEL Gateway --- OpAMP Supervisor Mode Guide

This document describes how to run the **Flowgate Gateway** in
**OpenTelemetry OpAMP Supervisor mode**, allowing the Flowgate Control
Plane to centrally manage configuration, lifecycle, and health of all
gateway instances.

## 1. Architecture Summary

The system follows a standard OpAMP Supervisor pattern:

    Flowgate Control Plane  =  OpAMP Server
    Flowgate Gateway Pod    =  OpAMP Client (Supervisor) + OTel Collector

### Inside Each Gateway Pod

-   **opampsupervisor**\
    Runs as PID 1, connects to Flowgate's OpAMP server, receives remote
    config, applies it, restarts collector when needed, reports
    health/metrics/logs.

-   **otelcol-contrib**\
    The actual OpenTelemetry Collector process. Its configuration is
    managed remotely by the Flowgate control plane.

### Flow

1.  Supervisor starts → reads `supervisor.yaml`.
2.  Connects to Flowgate OpAMP server.
3.  Receives remote config bundles.
4.  Applies config → starts or restarts `otelcol-contrib`.
5.  Reports:
    -   Effective config\
    -   Health + heartbeat\
    -   Self-metrics/logs\
    -   Remote config status

------------------------------------------------------------------------

## 2. Gateway Dockerfile (Supervisor + Collector)

``` dockerfile
# Stage 1: OpAMP supervisor binary
FROM otel/opentelemetry-collector-opampsupervisor:latest AS supervisor

# Stage 2: OTel collector binary (contrib distro)
FROM otel/opentelemetry-collector-contrib:latest AS otel

# Final image
FROM alpine:3.20

WORKDIR /flowgate-gateway

COPY --from=supervisor /usr/local/bin/opampsupervisor ./opampsupervisor
COPY --from=otel /otelcol-contrib ./otelcol-contrib

COPY supervisor.yaml ./supervisor.yaml
COPY collector-base.yaml ./collector-base.yaml

RUN mkdir -p /flowgate-gateway/storage

EXPOSE 4317 4318

ENTRYPOINT ["./opampsupervisor", "--config", "supervisor.yaml"]
```

------------------------------------------------------------------------

## 3. supervisor.yaml --- OpAMP Supervisor Configuration

``` yaml
server:
  endpoint: wss://flowgate-control-plane.your-domain.com/v1/opamp
  tls:
    insecure_skip_verify: true

capabilities:
  accepts_remote_config: true
  reports_effective_config: true
  reports_own_metrics: true
  reports_own_logs: true
  reports_own_traces: false
  reports_health: true
  reports_remote_config: true
  accepts_packages: false
  accepts_other_connection_settings: false
  accepts_restart_command: true
  reports_heartbeat: true

agent:
  executable: ./otelcol-contrib

storage:
  directory: ./storage
```

------------------------------------------------------------------------

## 4. collector-base.yaml --- Base Collector Config

``` yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch: {}

exporters:
  debug:
    verbosity: normal

service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
```

------------------------------------------------------------------------

## 5. Kubernetes Deployment Example

``` yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flowgate-gateway
  namespace: flowgate
spec:
  replicas: 2
  selector:
    matchLabels:
      app: flowgate-gateway
  template:
    metadata:
      labels:
        app: flowgate-gateway
    spec:
      containers:
        - name: gateway
          image: your-registry/flowgate-gateway:latest
          ports:
            - containerPort: 4317
            - containerPort: 4318
          volumeMounts:
            - name: gateway-config
              mountPath: /flowgate-gateway/supervisor.yaml
              subPath: supervisor.yaml
            - name: gateway-config
              mountPath: /flowgate-gateway/collector-base.yaml
              subPath: collector-base.yaml
            - name: gateway-storage
              mountPath: /flowgate-gateway/storage
      volumes:
        - name: gateway-config
          configMap:
            name: flowgate-gateway-config
        - name: gateway-storage
          emptyDir: {}
```

------------------------------------------------------------------------

## 6. Flowgate Control Plane Responsibilities

-   Gateway identity tracking\
-   Remote config orchestration\
-   Effective config ingestion\
-   Health & heartbeat monitoring\
-   UI integration for configuration states

------------------------------------------------------------------------
