#!/bin/bash
# Log filter script for OpAMP Supervisor
# Suppresses repetitive "Connected to the server" messages and only shows state transitions

LAST_STATE=""

# Function to extract state from log message
extract_state() {
    local msg="$1"
    # Check for connection state messages in JSON format
    if echo "$msg" | grep -qE '"msg":"Connected to the server"' || echo "$msg" | grep -qE 'Connected to the server'; then
        echo "connected"
    elif echo "$msg" | grep -qE '"msg":"Disconnected from the server"' || echo "$msg" | grep -qE 'Disconnected from the server'; then
        echo "disconnected"
    elif echo "$msg" | grep -qE '"msg":"Connection failed"' || echo "$msg" | grep -qE 'Connection failed'; then
        echo "failed"
    elif echo "$msg" | grep -qE '"msg":"Reconnecting"' || echo "$msg" | grep -qE 'Reconnecting'; then
        echo "reconnecting"
    else
        echo "other"
    fi
}

# Read supervisor output line by line (handle both stdin and stderr)
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines
    [ -z "$line" ] && continue
    
    # Extract state from this line
    CURRENT_STATE=$(extract_state "$line")
    
    # Always show non-connection-related messages (errors, warnings, other info)
    if [ "$CURRENT_STATE" = "other" ]; then
        echo "$line"
        continue
    fi
    
    # For connection-related messages, only show on state change
    if [ "$CURRENT_STATE" != "$LAST_STATE" ]; then
        echo "$line"
        LAST_STATE="$CURRENT_STATE"
    fi
    # Otherwise, suppress the repeated message
    
done

