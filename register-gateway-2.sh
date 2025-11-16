#!/bin/bash

# Script to register and start gateway-2
# This script creates a registration token and starts gateway-2 with it

set -e

ORG_ID="${ORG_ID:-8057ca8e-4f71-4a19-b821-5937f129a0ec}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "=========================================="
echo "Registering Gateway-2"
echo "=========================================="

# Create a registration token
echo "Creating registration token..."
REGISTRATION_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/v1/registration-tokens" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Gateway-2 Registration Token\",
    \"expires_in_days\": 365,
    \"org_id\": \"${ORG_ID}\"
  }")

if [ -z "$REGISTRATION_RESPONSE" ]; then
    echo "❌ Failed to create registration token. Check backend connectivity."
    exit 1
fi

# Extract token from response
REGISTRATION_TOKEN=$(echo "$REGISTRATION_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('token', ''))
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "$REGISTRATION_TOKEN" ]; then
    echo "❌ Failed to extract registration token from response:"
    echo "$REGISTRATION_RESPONSE"
    exit 1
fi

echo "✓ Registration token created"
echo ""

# Export token and start gateway-2
echo "Starting gateway-2 with registration token..."
export REGISTRATION_TOKEN="$REGISTRATION_TOKEN"
docker compose up -d gateway-2

echo ""
echo "✓ Gateway-2 started"
echo ""
echo "To check registration status:"
echo "  docker compose logs gateway-2 | grep -E 'Registration|token|OpAMP'"
echo ""
echo "Note: The registration token has been used to start gateway-2."
echo "If you need to restart gateway-2, you can either:"
echo "  1. Use the same REGISTRATION_TOKEN environment variable"
echo "  2. Or gateway-2 will use its stored OpAMP token after first registration"

