#!/bin/bash

# Gateway heartbeat script
# Sends periodic heartbeats to FlowGate OpAMP server to keep gateway status active

# Don't exit on error - keep retrying
set +e

# Configuration
INSTANCE_ID="${INSTANCE_ID:-gateway-1}"
OPAMP_TOKEN="${OPAMP_TOKEN:-}"
BACKEND_URL="${BACKEND_URL:-http://backend:8000}"
API_BASE="${BACKEND_URL}/api/v1"
HEARTBEAT_INTERVAL="${HEARTBEAT_INTERVAL:-30}"  # seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[HEARTBEAT]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[HEARTBEAT]${NC} $1"
}

log_error() {
    echo -e "${RED}[HEARTBEAT]${NC} $1"
}

# Check if OpAMP token is available (REQUIRED)
if [ -z "$OPAMP_TOKEN" ]; then
    # Try to load from file
    TOKEN_FILE="/var/lib/otelcol/opamp_token"
    if [ -f "$TOKEN_FILE" ]; then
        OPAMP_TOKEN=$(cat "$TOKEN_FILE")
        log_info "Loaded OpAMP token from $TOKEN_FILE"
    else
        log_error "OPAMP_TOKEN is REQUIRED for heartbeat service."
        log_error "Gateway must be registered first to obtain an OpAMP token."
        log_error "Set OPAMP_TOKEN environment variable or ensure token file exists at $TOKEN_FILE"
        log_error "Heartbeat service will not start without a valid OpAMP token."
        exit 1
    fi
fi

log_info "Starting heartbeat service for gateway: $INSTANCE_ID"
log_info "  Backend URL: $BACKEND_URL"
log_info "  Heartbeat interval: ${HEARTBEAT_INTERVAL}s"

# Send heartbeat function
send_heartbeat() {
    local response
    response=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/opamp/heartbeat/${INSTANCE_ID}" \
        -H "Authorization: Bearer ${OPAMP_TOKEN}" \
        -H "Content-Type: application/json" 2>&1)
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        log_info "Heartbeat sent successfully"
        return 0
    else
        log_error "Heartbeat failed (HTTP $http_code): $body"
        return 1
    fi
}

# Main loop
while true; do
    send_heartbeat
    sleep "$HEARTBEAT_INTERVAL"
done

