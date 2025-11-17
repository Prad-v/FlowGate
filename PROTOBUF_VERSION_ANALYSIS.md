# Protobuf Version Analysis

## Summary

Analysis of protobuf versions across OpAMP components to identify compatibility issues.

## Component Versions

### Supervisor
- **Version**: v0.139.0 (from Dockerfile)
- **Binary**: `/usr/local/bin/opampsupervisor`
- **Protobuf**: Uses `github.com/open-telemetry/opamp-go v0.12.0` which depends on `google.golang.org/protobuf v1.34.0`

### Collector
- **Version**: v0.139.0 (from builder-config.yaml)
- **Binary**: `/otelcol`
- **Protobuf**: Uses same as supervisor (built with collector-contrib)

### Go Parser (Backend)
- **OpAMP Library**: `github.com/open-telemetry/opamp-go v0.12.0`
- **Protobuf**: `google.golang.org/protobuf v1.34.0` (from go.sum)

### Python Parser (Backend)
- **Protobuf**: `protobuf==4.21.6` (pinned)
- **Generated from**: Latest opamp.proto from opamp-spec

## Version Compatibility

| Component | Protobuf Version | Status |
|-----------|-----------------|--------|
| Supervisor | v1.34.0 (Go) | ✅ |
| Collector | v1.34.0 (Go) | ✅ |
| Go Parser | v1.34.0 (Go) | ✅ Compatible |
| Python Parser | 4.21.6 (Python) | ⚠️ May have compatibility issues |

## Issue Analysis

### Message Format Analysis

Sample message from logs:
```
Hex: 000a10019a86892e6d7d2089ffe01046135f26101220e7fb01
Size: 25 bytes
```

Wire format breakdown:
- `0a` = Field 1 (instance_uid), wire_type 2 (length-delimited)
- `10` = Length 16 bytes
- `019a86892e6d7d2089ffe01046135f26` = 16-byte instance_uid
- `10` = Field 2 (sequence_num), wire_type 0 (varint)
- `12` = Varint value 18
- `20` = Field 4 (capabilities), wire_type 0 (varint)
- `e7 fb 01` = Varint value (decoded: 0x8DE7 = 36327)

### Parsing Failures

Both Go and Python parsers fail on the same messages, suggesting:
1. **Message corruption** - Messages may be corrupted during transmission
2. **Wire format mismatch** - Protobuf wire format may not match expected structure
3. **Version incompatibility** - Python protobuf 4.21.6 may not fully support Go protobuf v1.34.0 wire format

## Recommendations

1. **Upgrade Python Protobuf**: Consider upgrading to protobuf 4.25.x or 5.x for better Go compatibility
2. **Use Go Parser Only**: Since Go parser uses same protobuf version as supervisor/collector, it should be most compatible
3. **Message Validation**: Add message validation to detect corruption early
4. **Wire Format Logging**: Add detailed wire format logging to identify exact parsing failures

## Next Steps

1. ✅ Check protobuf versions - COMPLETED
2. 🔄 Verify message format at wire level - IN PROGRESS
3. ⏳ Test with known-good OpAMP messages - PENDING

