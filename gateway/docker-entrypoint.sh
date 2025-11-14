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

# If OPAMP_TOKEN is set but config doesn't have it, try to load from file
if [ -n "${OPAMP_TOKEN:-}" ] && [ -f /var/lib/otelcol/opamp_token ]; then
    # Token file exists, use it
    export OPAMP_TOKEN=$(cat /var/lib/otelcol/opamp_token)
elif [ -f /var/lib/otelcol/opamp_token ]; then
    # Load token from file if not in environment
    export OPAMP_TOKEN=$(cat /var/lib/otelcol/opamp_token)
fi

# Start heartbeat service in background if OpAMP token is available
if [ -n "${OPAMP_TOKEN:-}" ] || [ -f /var/lib/otelcol/opamp_token ]; then
    echo "Starting heartbeat service..."
    /usr/local/bin/heartbeat.sh &
    HEARTBEAT_PID=$!
    echo "Heartbeat service started (PID: $HEARTBEAT_PID)"
fi

# Start the collector with the provided arguments
exec /otelcol "$@"

