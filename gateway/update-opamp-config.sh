#!/bin/bash

# Script to update OpAMP configuration in the collector config file
# Usage: update-opamp-config.sh <opamp_token> <opamp_endpoint> [config_file]

set -e

OPAMP_TOKEN="${1}"
OPAMP_ENDPOINT="${2}"
CONFIG_FILE="${3:-/etc/otelcol/config.yaml}"

if [ -z "$OPAMP_TOKEN" ] || [ -z "$OPAMP_ENDPOINT" ]; then
    echo "Usage: $0 <opamp_token> <opamp_endpoint> [config_file]"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file $CONFIG_FILE not found"
    exit 1
fi

# Create a temporary file for the updated config
TMP_FILE=$(mktemp)

# Use yq or python to update the YAML file
# If yq is not available, use python
if command -v yq &> /dev/null; then
    # Update using yq
    yq eval ".extensions.opamp.server.endpoint = \"$OPAMP_ENDPOINT\"" "$CONFIG_FILE" | \
    yq eval ".extensions.opamp.server.headers.Authorization = \"Bearer $OPAMP_TOKEN\"" - > "$TMP_FILE"
else
    # Update using python
    python3 << EOF
import yaml
import sys

with open("$CONFIG_FILE", 'r') as f:
    config = yaml.safe_load(f)

# Ensure extensions section exists
if 'extensions' not in config:
    config['extensions'] = {}

# Ensure opamp extension exists
if 'opamp' not in config['extensions']:
    config['extensions']['opamp'] = {
        'server': {'endpoint': '', 'headers': {}},
        'instance_id': '${INSTANCE_ID:-gateway-1}',
        'capabilities': ['AcceptsRemoteConfig', 'ReportsEffectiveConfig', 'ReportsOwnTelemetry']
    }

# Update OpAMP configuration
config['extensions']['opamp']['server']['endpoint'] = "$OPAMP_ENDPOINT"
config['extensions']['opamp']['server']['headers']['Authorization'] = "Bearer $OPAMP_TOKEN"

# Ensure opamp is in service.extensions
if 'service' not in config:
    config['service'] = {}
if 'extensions' not in config['service']:
    config['service']['extensions'] = []

if 'opamp' not in config['service']['extensions']:
    config['service']['extensions'].append('opamp')

with open("$TMP_FILE", 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

EOF
fi

# Replace the original file
mv "$TMP_FILE" "$CONFIG_FILE"

echo "OpAMP configuration updated successfully"
echo "  Endpoint: $OPAMP_ENDPOINT"
echo "  Token: ${OPAMP_TOKEN:0:20}..."

