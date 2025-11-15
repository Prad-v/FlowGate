#!/bin/bash

# Gateway onboarding script for FlowGate OpAMP Agent Management
# This script registers the gateway and configures it to connect to OpAMP server

set -e

# Configuration
REGISTRATION_TOKEN="${REGISTRATION_TOKEN:-}"
BACKEND_URL="${BACKEND_URL:-http://backend:8000}"
API_BASE="${BACKEND_URL}/api/v1"
INSTANCE_ID="${INSTANCE_ID:-gateway-1}"
GATEWAY_NAME="${GATEWAY_NAME:-${INSTANCE_ID}}"
CONFIG_FILE="${CONFIG_FILE:-/etc/otelcol/config.yaml}"
HOSTNAME="${HOSTNAME:-$(hostname)}"
IP_ADDRESS="${IP_ADDRESS:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if registration token is provided
if [ -z "$REGISTRATION_TOKEN" ]; then
    log_error "REGISTRATION_TOKEN environment variable is required"
    log_info "To get a registration token:"
    log_info "  1. Go to FlowGate UI or use API: POST ${API_BASE}/registration-tokens"
    log_info "  2. Set REGISTRATION_TOKEN environment variable"
    exit 1
fi

log_info "Starting gateway onboarding process..."
log_info "  Instance ID: $INSTANCE_ID"
log_info "  Gateway Name: $GATEWAY_NAME"
log_info "  Backend URL: $BACKEND_URL"

# Step 1: Register gateway
log_info "Step 1: Registering gateway with FlowGate..."

REGISTRATION_RESPONSE=$(curl -s -X POST "${API_BASE}/gateways" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${REGISTRATION_TOKEN}" \
    -d "{
        \"name\": \"${GATEWAY_NAME}\",
        \"instance_id\": \"${INSTANCE_ID}\",
        \"hostname\": \"${HOSTNAME}\",
        \"ip_address\": \"${IP_ADDRESS}\",
        \"metadata\": {
            \"version\": \"1.0.0\",
            \"otel_version\": \"latest\",
            \"capabilities\": [
                \"AcceptsRemoteConfig\",
                \"ReportsEffectiveConfig\",
                \"ReportsOwnTelemetry\",
                \"ReportsHealth\",
                \"ReportsPackageAvailable\",
                \"ReportsPackageStatus\",
                \"AcceptsPackages\"
            ]
        }
    }" || echo "")

if [ -z "$REGISTRATION_RESPONSE" ]; then
    log_error "Failed to register gateway. Check backend connectivity and registration token."
    exit 1
fi

# Check if response contains error
if echo "$REGISTRATION_RESPONSE" | grep -q "error\|Error\|ERROR"; then
    log_error "Registration failed: $REGISTRATION_RESPONSE"
    exit 1
fi

# Extract OpAMP token and endpoint
OPAMP_TOKEN=$(echo "$REGISTRATION_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('opamp_token', ''))
except:
    print('')
" 2>/dev/null || echo "")

OPAMP_ENDPOINT=$(echo "$REGISTRATION_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('opamp_endpoint', ''))
except:
    print('')
" 2>/dev/null || echo "")

GATEWAY_ID=$(echo "$REGISTRATION_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('id', ''))
except:
    print('')
" 2>/dev/null || echo "")

MANAGEMENT_MODE=$(echo "$REGISTRATION_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('management_mode', 'supervisor'))
except:
    print('supervisor')
" 2>/dev/null || echo "supervisor")

if [ -z "$OPAMP_TOKEN" ] || [ -z "$OPAMP_ENDPOINT" ]; then
    log_error "Failed to extract OpAMP token or endpoint from registration response"
    log_error "Response: $REGISTRATION_RESPONSE"
    exit 1
fi

log_info "Gateway registered successfully!"
log_info "  Gateway ID: $GATEWAY_ID"
log_info "  OpAMP Endpoint: $OPAMP_ENDPOINT"
log_info "  OpAMP Token: ${OPAMP_TOKEN:0:30}..."
log_info "  Management Mode: ${MANAGEMENT_MODE:-supervisor}"

# Save management mode to file for entrypoint to use
MANAGEMENT_MODE_FILE="/var/lib/otelcol/management_mode"
echo "${MANAGEMENT_MODE:-supervisor}" > "$MANAGEMENT_MODE_FILE" 2>/dev/null || log_warn "Could not save management mode to $MANAGEMENT_MODE_FILE"
export USE_SUPERVISOR=$([ "${MANAGEMENT_MODE:-supervisor}" = "supervisor" ] && echo "true" || echo "false")

# Step 2: Update collector configuration
log_info "Step 2: Updating collector configuration with OpAMP settings..."

# Extract the base URL from opamp_endpoint (remove /v1/opamp if present)
# The endpoint should be: http://backend:8000/api/v1/opamp/v1/opamp
OPAMP_SERVER_URL=$(echo "$OPAMP_ENDPOINT" | sed 's|/v1/opamp$||' | sed 's|/api/v1/opamp$||')
# Ensure we have the full path for OpAMP protocol
if [[ "$OPAMP_ENDPOINT" != *"/api/v1/opamp/v1/opamp" ]]; then
    OPAMP_ENDPOINT="${OPAMP_SERVER_URL}/api/v1/opamp/v1/opamp"
fi

# Update the config file
if [ -f "$CONFIG_FILE" ]; then
    # Use the update script if available, otherwise update directly
    if [ -f "/usr/local/bin/update-opamp-config.sh" ] || [ -f "./update-opamp-config.sh" ]; then
        UPDATE_SCRIPT=$(which update-opamp-config.sh || echo "./update-opamp-config.sh")
        "$UPDATE_SCRIPT" "$OPAMP_TOKEN" "$OPAMP_ENDPOINT" "$CONFIG_FILE"
    else
        # Fallback: use environment variables (collector will read them)
        export OPAMP_TOKEN="$OPAMP_TOKEN"
        export OPAMP_SERVER_URL="$OPAMP_SERVER_URL"
        log_info "Config file update script not found, using environment variables"
        log_info "Make sure OPAMP_TOKEN and OPAMP_SERVER_URL are set in collector environment"
    fi
else
    log_warn "Config file $CONFIG_FILE not found, skipping direct update"
    log_info "Setting environment variables for collector to use:"
    log_info "  export OPAMP_TOKEN=\"$OPAMP_TOKEN\""
    log_info "  export OPAMP_SERVER_URL=\"$OPAMP_SERVER_URL\""
fi

# Step 3: Save token to file for persistence
TOKEN_FILE="/var/lib/otelcol/opamp_token"
mkdir -p "$(dirname "$TOKEN_FILE")" 2>/dev/null || true
echo "$OPAMP_TOKEN" > "$TOKEN_FILE" 2>/dev/null || log_warn "Could not save token to $TOKEN_FILE"

log_info "Step 3: Onboarding complete!"
log_info ""
log_info "Next steps:"
log_info "  1. The collector will connect to OpAMP server on next restart/reload"
log_info "  2. Monitor gateway status in FlowGate UI"
log_info "  3. Configuration updates will be pushed via OpAMP"

# Signal collector to reload (if running)
if pgrep -f otelcol > /dev/null; then
    log_info "Sending reload signal to collector..."
    pkill -HUP -f otelcol 2>/dev/null || log_warn "Could not send reload signal"
fi

exit 0

