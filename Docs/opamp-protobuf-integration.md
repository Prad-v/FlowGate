# OpAMP Protobuf Integration

## Status: ✅ COMPLETED

The OpAMP Protobuf definitions have been integrated and the backend now uses proper Protobuf message serialization/deserialization.

## Implementation

The official OpAMP Protobuf definitions have been integrated from:
- https://github.com/open-telemetry/opamp-spec/tree/main/proto

### Files Generated

- `backend/services/flowgate-backend/app/protobufs/opamp_pb2.py` - Generated OpAMP Protobuf messages
- `backend/services/flowgate-backend/app/protobufs/anyvalue_pb2.py` - Generated AnyValue Protobuf messages
- `backend/services/flowgate-backend/app/protobufs/__init__.py` - Package initialization

### Integration Details

The `opamp_protocol_service.py` has been updated to:
1. Use `opamp_pb2.AgentToServer` and `opamp_pb2.ServerToAgent` Protobuf messages
2. Properly serialize/deserialize Protobuf messages using `SerializeToString()` and `ParseFromString()`
3. Handle instance UID as 16-byte UUID format (per OpAMP spec)
4. Build proper `AgentRemoteConfig` messages with `AgentConfigMap` and `AgentConfigFile`

### Dependencies Added

- `grpcio-tools==1.60.0` - For Protobuf code generation (already had `protobuf==4.25.1`)

### Option 1: Use opamp-proto Python Package (if available)

```bash
pip install opamp-proto
```

### Option 2: Generate Python Code from .proto Files

1. Clone the opamp-spec repository:
```bash
git clone https://github.com/open-telemetry/opamp-spec.git
cd opamp-spec/proto
```

2. Generate Python code using protoc:
```bash
protoc --python_out=. opamp.proto
```

3. Copy the generated files to the backend service

### Option 3: Use opamp-go Protobuf Definitions

The Go implementation includes Protobuf definitions that can be used as reference:
- https://github.com/open-telemetry/opamp-go/tree/main/protobufs

## Required Message Types

According to the OpAMP spec, we need to implement:

1. **ServerToAgent** message with fields:
   - `instance_uid` (string)
   - `capabilities` (uint64 bit-field)
   - `remote_config` (RemoteConfig message)
   - `command` (Command message)
   - etc.

2. **AgentToServer** message parsing with fields:
   - `instance_uid` (string)
   - `sequence_num` (uint64)
   - `capabilities` (uint64 bit-field)
   - `effective_config` (EffectiveConfig message)
   - `remote_config_status` (RemoteConfigStatus message)
   - `health` (Health message)
   - etc.

## Implementation Steps

1. Add Protobuf definitions to the project
2. Update `opamp_protocol_service.py` to use Protobuf serialization/deserialization
3. Update `opamp_websocket.py` to send/receive proper Protobuf messages
4. Test with the OpAMP extension

## Current Workaround

Until proper Protobuf support is added, the OpAMP extension will continue to show parsing errors. The WebSocket connection is established, but message exchange requires proper Protobuf format.

## References

- OpAMP Specification: https://opentelemetry.io/docs/specs/opamp/
- OpAMP Spec Repository: https://github.com/open-telemetry/opamp-spec
- OpAMP Go Implementation: https://github.com/open-telemetry/opamp-go

