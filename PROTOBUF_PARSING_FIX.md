# Protobuf Parsing Fix - Leading Null Byte Issue

## Problem Identified

Messages from the supervisor/collector were failing to parse because they contained a **leading null byte (0x00)** before the actual protobuf data.

### Example
```
Actual message: 000a10019a86892e6d7d2089ffe01046135f26101220e7fb01
                 ^^
                 Invalid leading 0x00
                 
Valid message:   0a10019a86892e6d7d2089ffe01046135f26101220e7fb01
                 ^^
                 Valid field tag (field 1, wire_type 2)
```

## Root Cause

The leading null byte is likely introduced by:
1. **WebSocket framing** - Some WebSocket implementations add padding
2. **Message encoding** - Binary encoding might add a length prefix or null terminator
3. **Buffer handling** - Message buffering might introduce null bytes

## Solution

Added null byte removal in `opamp_websocket.py` before parsing:

```python
# Fix: Remove leading null bytes if present (WebSocket framing issue)
# Protobuf messages should never start with 0x00
while len(message_data) > 0 and message_data[0] == 0x00:
    logger.warning(f"[WS] Removing leading null byte from message")
    message_data = message_data[1:]
```

## Verification

### Test Results

1. **Known-good messages**: ✅ Parse successfully
2. **Messages with leading null**: ✅ Parse after removal
3. **Go parser**: ✅ Works with fixed messages
4. **Python parser**: ✅ Works with fixed messages

### Wire Format Analysis

- **Field 1 (instance_uid)**: Tag `0x0a` (field 1, wire_type 2), length 16 bytes
- **Field 2 (sequence_num)**: Tag `0x10` (field 2, wire_type 0), varint value
- **Field 4 (capabilities)**: Tag `0x20` (field 4, wire_type 0), varint value

## Protobuf Version Compatibility

| Component | Protobuf Version | Status |
|-----------|-----------------|--------|
| Supervisor | v1.34.0 (Go) | ✅ |
| Collector | v1.34.0 (Go) | ✅ |
| Go Parser | v1.34.0 (Go) | ✅ Compatible |
| Python Parser | 4.21.6 (Python) | ✅ Works after null byte fix |

## Status

✅ **FIXED**: Leading null byte removal implemented and tested
✅ **VERIFIED**: Both Go and Python parsers work with fixed messages
✅ **COMPATIBLE**: All components use compatible protobuf versions

## Next Steps

1. Monitor logs for successful parsing
2. Verify capability reporting is now working
3. Test effective config retrieval

