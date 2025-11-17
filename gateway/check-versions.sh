#!/bin/bash
# Script to check supervisor and collector versions for compatibility

echo "=== OpAMP Supervisor and Collector Version Compatibility Check ==="
echo ""

echo "1. Checking Supervisor Binary:"
if [ -f /usr/local/bin/opampsupervisor ]; then
    echo "   ✓ Supervisor binary exists: $(ls -lh /usr/local/bin/opampsupervisor | awk '{print $5}')"
    SUPERVISOR_VERSION=$(strings /usr/local/bin/opampsupervisor 2>/dev/null | grep -E 'opampsupervisor.*v0\.|github.com.*opampsupervisor.*v0\.' | head -1 | grep -oE 'v0\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$SUPERVISOR_VERSION" ]; then
        echo "   ✓ Supervisor version: $SUPERVISOR_VERSION"
    else
        echo "   ⚠ Could not extract supervisor version from binary"
    fi
else
    echo "   ✗ Supervisor binary not found"
fi

echo ""
echo "2. Checking Collector Binary:"
if [ -f /otelcol ]; then
    echo "   ✓ Collector binary exists: $(ls -lh /otelcol | awk '{print $5}')"
    COLLECTOR_VERSION=$(strings /otelcol 2>/dev/null | grep -E 'go.opentelemetry.io/collector.*v0\.139|github.com.*opampextension.*v0\.139' | head -1 | grep -oE 'v0\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$COLLECTOR_VERSION" ]; then
        echo "   ✓ Collector version: $COLLECTOR_VERSION"
    else
        echo "   ⚠ Could not extract collector version from binary"
    fi
else
    echo "   ✗ Collector binary not found"
fi

echo ""
echo "3. Checking Process Status:"
if pgrep -f opampsupervisor > /dev/null; then
    echo "   ✓ Supervisor process is running (PID: $(pgrep -f opampsupervisor))"
else
    echo "   ✗ Supervisor process is NOT running"
fi

if pgrep -f otelcol > /dev/null; then
    echo "   ✓ Collector process is running (PID: $(pgrep -f otelcol))"
else
    echo "   ⚠ Collector process is NOT running (may be managed by supervisor)"
fi

echo ""
echo "4. Checking Configuration:"
if [ -f /etc/opampsupervisor/supervisor.yaml ]; then
    echo "   ✓ Supervisor config exists"
    EXECUTABLE=$(grep -E '^\s*executable:' /etc/opampsupervisor/supervisor.yaml | awk '{print $2}')
    if [ -n "$EXECUTABLE" ]; then
        echo "   ✓ Collector executable path: $EXECUTABLE"
        if [ -f "$EXECUTABLE" ]; then
            echo "   ✓ Collector executable exists"
        else
            echo "   ✗ Collector executable NOT found at $EXECUTABLE"
        fi
    fi
    OPAMP_PORT=$(grep -E '^\s*opamp_server_port:' /etc/opampsupervisor/supervisor.yaml | awk '{print $2}')
    if [ -n "$OPAMP_PORT" ]; then
        echo "   ✓ Supervisor local OpAMP server port: $OPAMP_PORT"
    fi
else
    echo "   ⚠ Supervisor config not found"
fi

if [ -f /etc/otelcol/config-supervisor.yaml ]; then
    echo "   ✓ Collector config exists"
    OPAMP_ENDPOINT=$(grep -A 5 'opamp:' /etc/otelcol/config-supervisor.yaml | grep -E 'endpoint:' | awk '{print $2}')
    if [ -n "$OPAMP_ENDPOINT" ]; then
        echo "   ✓ Collector OpAMP endpoint: $OPAMP_ENDPOINT"
    fi
else
    echo "   ⚠ Collector config not found"
fi

echo ""
echo "5. Version Compatibility Summary:"
if [ -n "$SUPERVISOR_VERSION" ] && [ -n "$COLLECTOR_VERSION" ]; then
    if [ "$SUPERVISOR_VERSION" = "$COLLECTOR_VERSION" ]; then
        echo "   ✅ COMPATIBLE: Both supervisor and collector are at $SUPERVISOR_VERSION"
    else
        echo "   ⚠ VERSION MISMATCH: Supervisor=$SUPERVISOR_VERSION, Collector=$COLLECTOR_VERSION"
    fi
else
    echo "   ⚠ Could not determine versions for comparison"
fi

echo ""
echo "=== Check Complete ==="

