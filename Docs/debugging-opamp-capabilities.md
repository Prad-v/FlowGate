# Debugging OpAMP Capabilities

This document explains how to debug if the collector/supervisor is sending all capability data to the server.

## Overview

The OpAMP protocol requires agents to report their capabilities in the `AgentToServer` message. The capabilities are sent as a bit-field (uint64) where each bit represents a specific capability.

## What Capabilities Should Be Sent

Based on the `supervisor.yaml` configuration, the supervisor should report these capabilities:

1. **ReportsStatus** (bit 0, 0x01) - Always enabled
2. **AcceptsRemoteConfig** (bit 1, 0x02)
3. **ReportsEffectiveConfig** (bit 2, 0x04)
4. **ReportsRemoteConfig** (bit 3, 0x08)
5. **ReportsOwnTraces** (bit 5, 0x20)
6. **ReportsOwnMetrics** (bit 6, 0x40)
7. **ReportsOwnLogs** (bit 7, 0x80)
8. **ReportsHealth** (bit 11, 0x800)
9. **ReportsHeartbeat** (bit 13, 0x2000)
10. **AcceptsOpAMPConnectionSettings** (bit 8, 0x100)
11. **ReportsAvailableComponents** (bit 14, 0x4000)
12. **AcceptsRestartCommand** (bit 10, 0x400)

Expected bit-field: `0x7DE7` (32231 in decimal)

## Debugging Steps

### 1. Check Backend Logs

The backend now logs capabilities at INFO level. Look for these log messages:

```
[OpAMP] Processing AgentToServer message from {instance_id}
[OpAMP] Message details: seq={seq}, capabilities=0x{capabilities:X}, ...
[OpAMP] Agent {instance_id} raw capabilities from message: 0x{capabilities:X} ({capabilities})
[OpAMP] Agent {instance_id} decoded capabilities: {list of capabilities}
[OpAMP] Go parser extracted capabilities: 0x{capabilities:X} ({capabilities}) from raw message ({size} bytes)
[OpAMP] After conversion to protobuf, capabilities: 0x{capabilities:X} ({capabilities})
[OpAMP] Storing capabilities for {instance_id}: agent=0x{agent_capabilities:X}, server=0x{server_capabilities:X}
[OpAMP] Verified stored capabilities for {instance_id}: agent=0x{agent_capabilities:X}, server=0x{server_capabilities:X}
```

### 2. Check if Supervisor Reports 0x0

If you see:
```
[OpAMP] Agent {instance_id} reported ZERO capabilities (0x0) - this may indicate a problem
[OpAMP] Agent {instance_id} (supervisor mode) reported capabilities as 0x0 - inferring from supervisor.yaml configuration
```

This means:
- The supervisor is not properly reading capabilities from `supervisor.yaml`
- OR the supervisor is not including capabilities in the AgentToServer message
- The backend will infer capabilities from the supervisor.yaml configuration as a workaround

### 3. Verify Supervisor Configuration

Check that `gateway/supervisor.yaml` has all capabilities enabled:

```yaml
capabilities:
  accepts_remote_config: true
  reports_remote_config: true
  reports_effective_config: true
  reports_own_metrics: true
  reports_own_logs: true
  reports_own_traces: true
  reports_health: true
  reports_heartbeat: true
  accepts_opamp_connection_settings: true
  reports_available_components: true
  accepts_restart_command: true
```

### 4. Check Supervisor Logs

Check the supervisor container logs to see if there are any errors reading the configuration:

```bash
docker logs flowgate-gateway-2 | grep -i "capabilit"
docker logs flowgate-gateway-2 | grep -i "supervisor.yaml"
```

### 5. Verify Database Storage

Check what's actually stored in the database:

```sql
SELECT 
    instance_id,
    opamp_agent_capabilities,
    opamp_server_capabilities,
    management_mode
FROM gateways
WHERE instance_id = 'your-instance-id';
```

The `opamp_agent_capabilities` should be `32231` (0x7DE7) for supervisor-managed agents.

### 6. Check API Response

Query the agent details API to see what capabilities are returned:

```bash
curl -X GET "http://localhost:8000/api/v1/supervisor/ui/agents/{instance_id}?org_id={org_id}" \
  -H "Authorization: Bearer {token}"
```

Look for:
- `opamp_agent_capabilities`: Should be 32231 (0x7DE7)
- `opamp_agent_capabilities_decoded`: Should list all 12 capabilities

## Common Issues

### Issue 1: Supervisor Reports 0x0

**Symptoms:**
- Logs show `capabilities=0x0`
- Backend infers capabilities from supervisor.yaml

**Possible Causes:**
1. Supervisor.yaml not being read correctly
2. Supervisor not including capabilities in AgentToServer message
3. Supervisor version bug

**Solutions:**
1. Verify supervisor.yaml is mounted correctly in the container
2. Check supervisor version - may need to update
3. The backend workaround will infer capabilities, but this should be fixed at the supervisor level

### Issue 2: Capabilities Not Stored in Database

**Symptoms:**
- Logs show capabilities being received, but database has NULL or 0

**Possible Causes:**
1. Database update failing silently
2. Transaction rollback

**Solutions:**
1. Check database logs for errors
2. Verify `update_opamp_capabilities` method is being called
3. Check for transaction rollbacks in logs

### Issue 3: Go Parser Not Extracting Capabilities

**Symptoms:**
- Go parser succeeds but capabilities are 0
- Python parser shows different capabilities

**Solutions:**
1. Check Go parser logs
2. Verify Go parser binary is up to date
3. Check if protobuf version mismatch

## Expected Behavior

For a properly configured supervisor-managed agent:

1. **Supervisor reads** `supervisor.yaml` and builds capability bit-field
2. **Supervisor sends** AgentToServer message with `capabilities=0x7DE7` (32231)
3. **Backend receives** message and logs: `capabilities=0x7DE7`
4. **Backend decodes** and logs: `ReportsStatus, AcceptsRemoteConfig, ReportsEffectiveConfig, ...`
5. **Backend stores** in database: `opamp_agent_capabilities=32231`
6. **API returns** capabilities in agent details response
7. **Frontend displays** capabilities in minified view

## Testing

To test if capabilities are being sent:

1. **Restart the gateway** to force a new connection:
   ```bash
   docker restart flowgate-gateway-2
   ```

2. **Watch backend logs** in real-time:
   ```bash
   docker logs -f flowgate-backend | grep -i "capabilit"
   ```

3. **Check the first message** - capabilities should be sent in the initial AgentToServer message

4. **Verify in UI** - Go to Agent Details page and check the OpAMP Capabilities section

## Next Steps

If capabilities are still not being sent correctly:

1. Check supervisor source code to see how it reads capabilities from supervisor.yaml
2. Verify supervisor.yaml is being loaded correctly
3. Check if there's a supervisor version that fixes this issue
4. Consider adding a supervisor health check that validates capabilities are being read

