# Multi-stage build: build custom collector with OpAMP extension
# Stage 1: Build the custom collector binary
FROM golang:1.23-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git make

# Set GOTOOLCHAIN to allow automatic toolchain downloads if needed
ENV GOTOOLCHAIN=auto

# Install OpenTelemetry Collector Builder
# Upgraded to v0.139.0 for full OpAMP capabilities support
# v0.139.0 provides comprehensive OpAMP capability reporting and all standard features
RUN go install go.opentelemetry.io/collector/cmd/builder@v0.139.0

# Set working directory
WORKDIR /build

# Copy builder configuration
COPY builder-config.yaml .

# Build the custom collector
RUN builder --config=builder-config.yaml

# Stage 2: Create the final image
FROM debian:bookworm-slim

# Build argument for supervisor version
# Using v0.139.0 (latest stable) for full OpAMP capabilities support
ARG SUPERVISOR_VERSION=v0.139.0

# Install tools needed for onboarding
RUN apt-get update && \
    apt-get install -y \
    curl \
    python3 \
    python3-pip \
    python3-yaml \
    wget \
    gettext-base \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Download and install OpAMP Supervisor
# Detect architecture and download appropriate binary
RUN ARCH=$(dpkg --print-architecture) && \
    case "$ARCH" in \
        amd64) ARCH_SUFFIX="linux_amd64" ;; \
        arm64) ARCH_SUFFIX="linux_arm64" ;; \
        ppc64el) ARCH_SUFFIX="linux_ppc64le" ;; \
        *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    VERSION_NO_V=$(echo "${SUPERVISOR_VERSION}" | sed 's/^v//') && \
    curl --proto '=https' --tlsv1.2 -fL -o /tmp/opampsupervisor \
    "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/cmd%2Fopampsupervisor%2F${SUPERVISOR_VERSION}/opampsupervisor_${VERSION_NO_V}_${ARCH_SUFFIX}" && \
    chmod +x /tmp/opampsupervisor && \
    mv /tmp/opampsupervisor /usr/local/bin/opampsupervisor

# Copy custom collector binary from builder stage
COPY --from=builder /build/dist/otelcol-flowgate /otelcol

# Copy custom configuration
COPY otel-collector-config.yaml /etc/otelcol/config.yaml

# Copy supervisor-specific collector config (without OpAMP extension)
COPY otel-collector-config-supervisor.yaml /usr/local/share/otel-collector-config-supervisor.yaml

# Copy supervisor configuration
COPY supervisor.yaml /usr/local/share/supervisor.yaml

# Copy onboarding scripts
COPY onboard.sh /usr/local/bin/onboard.sh
COPY update-opamp-config.sh /usr/local/bin/update-opamp-config.sh
COPY heartbeat.sh /usr/local/bin/heartbeat.sh

# Copy log filter script and wrapper
COPY filter-supervisor-logs.sh /usr/local/bin/filter-supervisor-logs.sh
COPY run-supervisor-filtered.sh /usr/local/bin/run-supervisor-filtered.sh

# Make scripts executable
RUN chmod +x /usr/local/bin/onboard.sh /usr/local/bin/update-opamp-config.sh /usr/local/bin/heartbeat.sh /usr/local/bin/filter-supervisor-logs.sh /usr/local/bin/run-supervisor-filtered.sh

# Create directories for token storage and supervisor
RUN mkdir -p /var/lib/otelcol /var/lib/opampsupervisor

# Expose ports
EXPOSE 4317 4318 8888

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8888/ || exit 1

# Entrypoint script that handles onboarding if needed
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["--config=/etc/otelcol/config.yaml"]

