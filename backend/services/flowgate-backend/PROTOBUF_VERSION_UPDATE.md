# Protobuf Version Update

## Summary

Protobuf version has been pinned to **4.21.6** (closest available to the requested v0.12.0 compatibility) to address parsing issues with OpAMP messages.

## Changes Made

1. **Updated `requirements.txt`**:
   - Changed `protobuf==4.25.1` → `protobuf==4.21.6`
   - This is the minimum version required by `grpcio-tools==1.60.0`

2. **Created `regenerate_protobuf.sh`**:
   - Script to regenerate Protobuf Python bindings from `.proto` files
   - Uses `python -m grpc_tools.protoc` to ensure compatibility
   - Automatically fixes relative imports in generated code

## Why 4.21.6?

- **Compatibility**: Minimum version required by `grpcio-tools==1.60.0` (requires `protobuf>=4.21.6`)
- **Stability**: Older, more stable version that may have better compatibility with Go protobuf v0.12.0
- **Version Alignment**: Attempts to align with Go's protobuf v0.12.0 (though Python and Go use different versioning schemes)

## Note on Version Mismatch

The user requested `v0.12.0`, but:
- **Go protobuf** uses versioning like `v0.12.0` (e.g., `google.golang.org/protobuf v0.12.0`)
- **Python protobuf** uses versioning like `3.x.x` or `4.x.x` (e.g., `protobuf==4.21.6`)

Since we cannot change the Go protobuf version in pre-built supervisor/collector binaries, we've pinned Python protobuf to the oldest compatible version (4.21.6) to maximize compatibility.

## Regenerating Bindings

To regenerate Protobuf bindings after version changes:

```bash
docker compose exec backend bash /tmp/regenerate_protobuf.sh
```

Or copy the script and run it:

```bash
docker compose cp backend/services/flowgate-backend/regenerate_protobuf.sh backend:/tmp/regenerate_protobuf.sh
docker compose exec backend bash /tmp/regenerate_protobuf.sh
```

## Testing

After updating the protobuf version, monitor backend logs for:
- Reduced parsing errors
- Successful message parsing
- Capability reporting

## Current Status

- ✅ Protobuf version pinned to 4.21.6
- ✅ Regeneration script created
- ⚠️ Parsing errors may still occur if the issue is not version-related
- ⚠️ Monitor logs to verify improvement

## Next Steps

1. Monitor backend logs for parsing errors
2. If errors persist, consider:
   - Checking Go protobuf version in supervisor/collector
   - Verifying message format compatibility
   - Testing with different protobuf versions

