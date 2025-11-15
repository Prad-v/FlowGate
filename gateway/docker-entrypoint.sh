#!/bin/bash

# Docker entrypoint script for OpenTelemetry Collector with OpAMP onboarding support

set -e

# Track registration status
OPAMP_REGISTRATION_FAILED=false

# If REGISTRATION_TOKEN is set, run onboarding first
if [ -n "${REGISTRATION_TOKEN:-}" ]; then
    echo "=========================================="
    echo "Registration token detected, running onboarding..."
    echo "=========================================="
    if /usr/local/bin/onboard.sh; then
        echo "✓ Registration successful"
    else
        REGISTRATION_EXIT_CODE=$?
        echo "=========================================="
        echo "✗ REGISTRATION FAILED (exit code: $REGISTRATION_EXIT_CODE)"
        echo "=========================================="
        echo "The collector will start, but OpAMP connection will fail."
        echo "To retry registration:"
        echo "  1. Ensure REGISTRATION_TOKEN is set correctly"
        echo "  2. Check backend connectivity"
        echo "  3. Restart the container or run: /usr/local/bin/onboard.sh"
        echo ""
        OPAMP_REGISTRATION_FAILED=true
        export OPAMP_REGISTRATION_FAILED=true
    fi
fi

# Load OpAMP token from environment or file
if [ -z "${OPAMP_TOKEN:-}" ] && [ -f /var/lib/otelcol/opamp_token ]; then
    # Load token from file if not in environment
    export OPAMP_TOKEN=$(cat /var/lib/otelcol/opamp_token)
    echo "✓ Loaded OpAMP token from file"
elif [ -n "${OPAMP_TOKEN:-}" ]; then
    # Save token to file for persistence
    mkdir -p /var/lib/otelcol
    echo "${OPAMP_TOKEN}" > /var/lib/otelcol/opamp_token
    echo "✓ Saved OpAMP token to file"
fi

# Ensure INSTANCE_ID is set (required for collector config)
export INSTANCE_ID="${INSTANCE_ID:-gateway-1}"
export OPAMP_SERVER_URL="${OPAMP_SERVER_URL:-http://backend:8000}"
export BACKEND_URL="${BACKEND_URL:-http://backend:8000}"

# Convert HTTP endpoint to WebSocket for OpAMP extension
# OpAMP extension uses WebSocket, so convert http:// to ws://
OPAMP_WS_URL=$(echo "$OPAMP_SERVER_URL" | sed 's|^http://|ws://|' | sed 's|^https://|wss://|')
export OPAMP_WS_URL="${OPAMP_WS_URL}"

# Check if OpAMP token is available
if [ -z "${OPAMP_TOKEN:-}" ]; then
    echo "=========================================="
    echo "⚠ WARNING: OpAMP token not found"
    echo "=========================================="
    echo "The collector will start, but:"
    echo "  - OpAMP extension will fail to connect"
    echo "  - Heartbeat service will not start"
    echo ""
    echo "To enable OpAMP functionality:"
    echo "  1. Register the gateway using REGISTRATION_TOKEN"
    echo "  2. Or set OPAMP_TOKEN environment variable"
    echo "  3. Or ensure token file exists at /var/lib/otelcol/opamp_token"
    echo ""
else
    # Start heartbeat service in background if OpAMP token is available
    # Only start if registration didn't fail (to avoid repeated failures)
    if [ "$OPAMP_REGISTRATION_FAILED" = "false" ]; then
        echo "Starting heartbeat service..."
        /usr/local/bin/heartbeat.sh > /proc/1/fd/1 2>&1 &
        HEARTBEAT_PID=$!
        echo "✓ Heartbeat service started (PID: $HEARTBEAT_PID)"
    else
        echo "⚠ Skipping heartbeat service (registration failed)"
    fi
fi

# Check if supervisor mode is enabled
# Priority: 1. Environment variable, 2. Management mode file from registration, 3. Default to supervisor
if [ -z "${USE_SUPERVISOR:-}" ]; then
    # Check if management mode was set during registration
    MANAGEMENT_MODE_FILE="/var/lib/otelcol/management_mode"
    if [ -f "$MANAGEMENT_MODE_FILE" ]; then
        MANAGEMENT_MODE=$(cat "$MANAGEMENT_MODE_FILE" 2>/dev/null || echo "supervisor")
        USE_SUPERVISOR=$([ "$MANAGEMENT_MODE" = "supervisor" ] && echo "true" || echo "false")
        echo "✓ Using management mode from registration: $MANAGEMENT_MODE"
    else
        # Default to supervisor mode
        USE_SUPERVISOR="true"
        echo "✓ Using default management mode: supervisor"
    fi
else
    echo "✓ Using management mode from environment: $([ "$USE_SUPERVISOR" = "true" ] && echo "supervisor" || echo "extension")"
fi

if [ "$USE_SUPERVISOR" = "true" ]; then
    echo "=========================================="
    echo "Starting OpAMP Supervisor (Managed Mode)..."
    echo "=========================================="
    
    # In supervisor mode, use collector config without OpAMP extension
    # The supervisor handles OpAMP communication, not the collector
    SUPERVISOR_COLLECTOR_CONFIG="/etc/otelcol/config-supervisor.yaml"
    if [ ! -f "$SUPERVISOR_COLLECTOR_CONFIG" ]; then
        # Copy supervisor-specific config if not present
        if [ -f /usr/local/share/otel-collector-config-supervisor.yaml ]; then
            mkdir -p /etc/otelcol
            cp /usr/local/share/otel-collector-config-supervisor.yaml "$SUPERVISOR_COLLECTOR_CONFIG"
            echo "✓ Created supervisor collector config"
        else
            # Fallback: create a config without OpAMP extension from the default config
            mkdir -p /etc/otelcol
            # Remove OpAMP extension from config
            sed '/^extensions:/,/^service:/ { /opamp:/d; /extensions: \[opamp\]/d; }' /etc/otelcol/config.yaml > "$SUPERVISOR_COLLECTOR_CONFIG" 2>/dev/null || \
            cp /etc/otelcol/config.yaml "$SUPERVISOR_COLLECTOR_CONFIG"
            echo "⚠ WARNING: Using fallback supervisor config (OpAMP extension may cause issues)"
        fi
    fi
    
    # Ensure supervisor config exists and expand environment variables
    if [ ! -f /etc/opampsupervisor/supervisor.yaml ]; then
        # Copy default supervisor config if not present
        if [ -f /usr/local/share/supervisor.yaml ]; then
            mkdir -p /etc/opampsupervisor
            # Expand environment variables in supervisor config
            envsubst < /usr/local/share/supervisor.yaml > /etc/opampsupervisor/supervisor.yaml
            # Update the config path in supervisor.yaml to use supervisor-specific collector config
            sed -i "s|--config=/etc/otelcol/config-supervisor.yaml|--config=$SUPERVISOR_COLLECTOR_CONFIG|g" /etc/opampsupervisor/supervisor.yaml 2>/dev/null || true
            echo "✓ Created supervisor config with environment variables expanded"
        else
            echo "⚠ WARNING: Supervisor config not found, using default location"
        fi
    else
        # Expand environment variables in existing config
        envsubst < /etc/opampsupervisor/supervisor.yaml > /etc/opampsupervisor/supervisor.yaml.tmp && \
        mv /etc/opampsupervisor/supervisor.yaml.tmp /etc/opampsupervisor/supervisor.yaml
    fi
    
    # Set supervisor config path
    SUPERVISOR_CONFIG="${SUPERVISOR_CONFIG:-/etc/opampsupervisor/supervisor.yaml}"
    
    # Ensure supervisor storage directory exists
    mkdir -p /var/lib/opampsupervisor
    
    # Start supervisor (supervisor will launch collector as subprocess)
    exec /usr/local/bin/opampsupervisor --config="${SUPERVISOR_CONFIG}"
else
    echo "=========================================="
    echo "Starting OpenTelemetry Collector (Direct Mode)..."
    echo "=========================================="
    
    # Start the collector with the provided arguments (current behavior)
    exec /otelcol "$@"
fi

