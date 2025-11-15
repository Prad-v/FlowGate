# Multi-stage build: build custom collector with OpAMP extension
# Stage 1: Build the custom collector binary
FROM golang:1.23-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git make

# Set GOTOOLCHAIN to allow automatic toolchain downloads if needed
ENV GOTOOLCHAIN=auto

# Install OpenTelemetry Collector Builder
# Using a stable version that's compatible with available component versions
# v0.103.0 is a stable version that works with Go 1.23
RUN go install go.opentelemetry.io/collector/cmd/builder@v0.103.0

# Set working directory
WORKDIR /build

# Copy builder configuration
COPY builder-config.yaml .

# Build the custom collector
RUN builder --config=builder-config.yaml

# Stage 2: Create the final image
FROM debian:bookworm-slim

# Install tools needed for onboarding
RUN apt-get update && \
    apt-get install -y \
    curl \
    python3 \
    python3-pip \
    python3-yaml \
    wget \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy custom collector binary from builder stage
COPY --from=builder /build/dist/otelcol-flowgate /otelcol

# Copy custom configuration
COPY otel-collector-config.yaml /etc/otelcol/config.yaml

# Copy onboarding scripts
COPY onboard.sh /usr/local/bin/onboard.sh
COPY update-opamp-config.sh /usr/local/bin/update-opamp-config.sh
COPY heartbeat.sh /usr/local/bin/heartbeat.sh

# Make scripts executable
RUN chmod +x /usr/local/bin/onboard.sh /usr/local/bin/update-opamp-config.sh /usr/local/bin/heartbeat.sh

# Create directory for token storage
RUN mkdir -p /var/lib/otelcol

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

