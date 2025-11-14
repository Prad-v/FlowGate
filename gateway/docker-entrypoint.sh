#!/bin/bash

# Docker entrypoint script for OpenTelemetry Collector with OpAMP onboarding support

set -e

# If REGISTRATION_TOKEN is set, run onboarding first
if [ -n "${REGISTRATION_TOKEN:-}" ]; then
    echo "Registration token detected, running onboarding..."
    /usr/local/bin/onboard.sh || {
        echo "Warning: Onboarding failed, but continuing with collector startup"
        echo "You can manually run: /usr/local/bin/onboard.sh"
    }
fi

# Load OpAMP token from environment or file
if [ -z "${OPAMP_TOKEN:-}" ] && [ -f /var/lib/otelcol/opamp_token ]; then
    # Load token from file if not in environment
    export OPAMP_TOKEN=$(cat /var/lib/otelcol/opamp_token)
    echo "Loaded OpAMP token from file"
elif [ -n "${OPAMP_TOKEN:-}" ]; then
    # Save token to file for persistence
    mkdir -p /var/lib/otelcol
    echo "${OPAMP_TOKEN}" > /var/lib/otelcol/opamp_token
    echo "Saved OpAMP token to file"
fi

# Start heartbeat service in background if OpAMP token is available
if [ -n "${OPAMP_TOKEN:-}" ]; then
    echo "Starting heartbeat service..."
    export OPAMP_TOKEN="${OPAMP_TOKEN}"
    export INSTANCE_ID="${INSTANCE_ID:-gateway-1}"
    export BACKEND_URL="${BACKEND_URL:-http://backend:8000}"
    /usr/local/bin/heartbeat.sh > /proc/1/fd/1 2>&1 &
    HEARTBEAT_PID=$!
    echo "Heartbeat service started (PID: $HEARTBEAT_PID)"
else
    echo "Warning: OpAMP token not found. Heartbeat service will not start."
    echo "  Set OPAMP_TOKEN environment variable or ensure token file exists at /var/lib/otelcol/opamp_token"
fi

# Start the collector with the provided arguments
exec /otelcol "$@"

