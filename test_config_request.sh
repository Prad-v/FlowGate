#!/bin/bash
# Test script for config request functionality

ORG_ID="8057ca8e-4f71-4a19-b821-5937f129a0ec"
INSTANCE_ID="gateway-1"
BASE_URL="http://localhost:8000/api/v1/supervisor/ui/agents"

echo "=== Testing Config Request Functionality ==="
echo ""

# Step 1: Check agent connection status
echo "1. Checking agent connection status..."
AGENT_STATUS=$(curl -s "${BASE_URL}/${INSTANCE_ID}?org_id=${ORG_ID}" 2>&1)
CONNECTION_STATUS=$(echo "$AGENT_STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('opamp_connection_status', 'unknown'))" 2>&1)
CAPABILITIES=$(echo "$AGENT_STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(hex(d.get('opamp_agent_capabilities', 0)))" 2>&1)
echo "   Connection Status: $CONNECTION_STATUS"
echo "   Capabilities: $CAPABILITIES"
echo ""

if [ "$CONNECTION_STATUS" != "connected" ]; then
    echo "ERROR: Agent is not connected!"
    exit 1
fi

# Step 2: Create a config request
echo "2. Creating config request..."
REQUEST_RESPONSE=$(curl -s -X POST "${BASE_URL}/${INSTANCE_ID}/request-effective-config?org_id=${ORG_ID}" -H 'Content-Type: application/json' 2>&1)
TRACKING_ID=$(echo "$REQUEST_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('tracking_id', 'error'))" 2>&1)
echo "   Tracking ID: $TRACKING_ID"
echo "   Response: $REQUEST_RESPONSE"
echo ""

if [ "$TRACKING_ID" = "error" ] || [ -z "$TRACKING_ID" ]; then
    echo "ERROR: Failed to create config request!"
    exit 1
fi

# Step 3: Wait and check status multiple times
echo "3. Monitoring config request status (checking every 5 seconds for 60 seconds)..."
for i in {1..12}; do
    sleep 5
    STATUS_RESPONSE=$(curl -s "${BASE_URL}/${INSTANCE_ID}/config-requests/${TRACKING_ID}?org_id=${ORG_ID}" 2>&1)
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('status', 'unknown'))" 2>&1)
    HAS_CONTENT=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print('yes' if d.get('effective_config_content') else 'no')" 2>&1)
    echo "   Check $i: Status=$STATUS, Has Content=$HAS_CONTENT"
    
    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo "✓ SUCCESS: Config request completed!"
        echo "   Config size: $(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('effective_config_content', '')))" 2>&1) bytes"
        exit 0
    fi
done

echo ""
echo "✗ TIMEOUT: Config request still pending after 60 seconds"
echo "   Final status: $STATUS_RESPONSE"
exit 1

