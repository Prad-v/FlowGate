#!/bin/bash

# Test script for OpAMP Gateway Registration

BASE_URL="http://localhost:8000/api/v1"

# Get organization ID from database (use existing org)
echo "0. Getting organization ID..."
ORG_ID=$(docker-compose exec -T backend python -c "
from app.database import SessionLocal
from app.models.tenant import Organization
import sys, re
db = SessionLocal()
org = db.query(Organization).first()
if org:
    sys.stdout.write(str(org.id))
db.close()
" 2>&1 | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -1)

if [ -z "$ORG_ID" ] || [ "$ORG_ID" = "00000000-0000-0000-0000-000000000000" ]; then
  echo "ERROR: No organization found. Please create one first."
  exit 1
fi

echo "Using Organization ID: $ORG_ID"
echo ""

echo "=== Testing OpAMP Gateway Registration ==="
echo ""

# Step 1: Create a registration token
echo "1. Creating registration token..."
TOKEN_RESPONSE=$(curl -s -X POST "${BASE_URL}/registration-tokens?org_id=${ORG_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Registration Token",
    "expires_in_days": 30
  }')

echo "Response: $TOKEN_RESPONSE"
REGISTRATION_TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$REGISTRATION_TOKEN" ]; then
  echo "ERROR: Failed to create registration token"
  exit 1
fi

echo "Registration Token: ${REGISTRATION_TOKEN:0:20}..."
echo ""

# Step 2: Register a gateway using the token
echo "2. Registering gateway with registration token..."
GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/gateways" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${REGISTRATION_TOKEN}" \
  -d '{
    "name": "Test Gateway",
    "instance_id": "test-gateway-1",
    "hostname": "test-gateway.example.com",
    "ip_address": "192.168.1.100",
    "metadata": {
      "version": "1.0.0",
      "otel_version": "0.88.0",
      "capabilities": ["AcceptsRemoteConfig", "ReportsEffectiveConfig"]
    }
  }')

echo "Response: $GATEWAY_RESPONSE"
GATEWAY_ID=$(echo $GATEWAY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
OPAMP_TOKEN=$(echo $GATEWAY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['opamp_token'])" 2>/dev/null)
OPAMP_ENDPOINT=$(echo $GATEWAY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['opamp_endpoint'])" 2>/dev/null)

if [ -z "$GATEWAY_ID" ]; then
  echo "ERROR: Failed to register gateway"
  exit 1
fi

echo "Gateway ID: $GATEWAY_ID"
echo "OpAMP Token: ${OPAMP_TOKEN:0:30}..."
echo "OpAMP Endpoint: $OPAMP_ENDPOINT"
echo ""

# Step 3: List gateways
echo "3. Listing gateways..."
LIST_RESPONSE=$(curl -s "${BASE_URL}/gateways?org_id=${ORG_ID}")
echo "Response: $LIST_RESPONSE"
echo ""

# Step 4: Test OpAMP config endpoint
echo "4. Testing OpAMP config endpoint..."
CONFIG_RESPONSE=$(curl -s -X GET "${BASE_URL}/opamp/config/test-gateway-1" \
  -H "Authorization: Bearer ${OPAMP_TOKEN}")
echo "Config Response: $CONFIG_RESPONSE"
echo ""

# Step 5: Test OpAMP heartbeat
echo "5. Testing OpAMP heartbeat..."
HEARTBEAT_RESPONSE=$(curl -s -X POST "${BASE_URL}/opamp/heartbeat/test-gateway-1?config_version=1" \
  -H "Authorization: Bearer ${OPAMP_TOKEN}")
echo "Heartbeat Response: $HEARTBEAT_RESPONSE"
echo ""

echo "=== Registration Test Complete ==="

