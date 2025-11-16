#!/bin/bash
# Wrapper script to run supervisor with log filtering
# Handles signals properly and filters repetitive connection messages

SUPERVISOR_CONFIG="${1}"

# Function to handle signals and forward them to supervisor process group
cleanup() {
    # Kill the entire process group (supervisor and filter)
    kill -TERM -$$ 2>/dev/null
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start supervisor with log filtering in the same process group
# This ensures signals are properly forwarded
set -m  # Enable job control
/usr/local/bin/opampsupervisor --config="${SUPERVISOR_CONFIG}" 2>&1 | /usr/local/bin/filter-supervisor-logs.sh

