#!/bin/bash
# Log filter for supervisor that filters repetitive messages without interfering with pipes
# This script filters stdout only, leaving stderr and internal communication intact

LAST_STATE=""
STATE_COUNT=0

# Function to extract state from log message
extract_state() {
    local msg="$1"
    if echo "$msg" | grep -qE '"msg":"Connected to the server"'; then
        echo "connected"
    elif echo "$msg" | grep -qE '"msg":"Disconnected from the server"'; then
        echo "disconnected"
    elif echo "$msg" | grep -qE '"msg":"Connection failed"'; then
        echo "failed"
    elif echo "$msg" | grep -qE '"msg":"Reconnecting"'; then
        echo "reconnecting"
    else
        echo "other"
    fi
}

# Read line by line, but don't block or close pipes
while IFS= read -r line 2>/dev/null || true; do
    [ -z "$line" ] && echo "$line" && continue
    
    CURRENT_STATE=$(extract_state "$line")
    
    # Always show non-connection-related messages
    if [ "$CURRENT_STATE" = "other" ]; then
        echo "$line"
        continue
    fi
    
    # For connection-related messages, only show on state change or every 10th message
    if [ "$CURRENT_STATE" != "$LAST_STATE" ]; then
        echo "$line"
        LAST_STATE="$CURRENT_STATE"
        STATE_COUNT=0
    elif [ "$CURRENT_STATE" = "connected" ]; then
        # For repeated "connected" messages, only show every 10th one
        STATE_COUNT=$((STATE_COUNT + 1))
        if [ $((STATE_COUNT % 10)) -eq 0 ]; then
            echo "$line"
        fi
    fi
done

