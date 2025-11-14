# Multi-stage build: extract collector binary from distroless image
FROM otel/opentelemetry-collector:latest AS collector-binary
# The collector binary is at /otelcol in the distroless image

# Use debian base for tools and shell
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

# Copy collector binary from distroless image
COPY --from=collector-binary /otelcol /otelcol

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

