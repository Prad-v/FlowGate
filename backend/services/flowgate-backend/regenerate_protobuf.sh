#!/bin/bash
# Regenerate Protobuf Python bindings from .proto files
# This script should be run after updating protobuf version

set -e

# When running in Docker, use /app/app/protobufs
# When running locally, use the script directory
if [ -d "/app/app/protobufs" ]; then
    PROTOBUF_DIR="/app/app/protobufs"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROTOBUF_DIR="${SCRIPT_DIR}/app/protobufs"
fi

echo "Regenerating Protobuf Python bindings..."
echo "Protobuf directory: ${PROTOBUF_DIR}"

# Use python -m grpc_tools.protoc instead of protoc directly
# This ensures we use the protoc bundled with grpcio-tools
PROTOC_CMD="python -m grpc_tools.protoc"

# Check Python protobuf version
PYTHON_PROTOBUF_VERSION=$(python -c "import google.protobuf; print(google.protobuf.__version__)" 2>&1)
echo "Using Python protobuf version: ${PYTHON_PROTOBUF_VERSION}"

cd "${PROTOBUF_DIR}"

# Generate anyvalue_pb2.py first (opamp.proto depends on it)
echo "Generating anyvalue_pb2.py..."
${PROTOC_CMD} --python_out=. --proto_path="${PROTOBUF_DIR}" "${PROTOBUF_DIR}/anyvalue.proto"

# Generate opamp_pb2.py
echo "Generating opamp_pb2.py..."
${PROTOC_CMD} --python_out=. --proto_path="${PROTOBUF_DIR}" "${PROTOBUF_DIR}/opamp.proto"

# Fix import in opamp_pb2.py to use relative import
if [ -f "opamp_pb2.py" ]; then
    echo "Fixing import statement in opamp_pb2.py..."
    # Replace absolute import with relative import
    sed -i.bak 's/^import anyvalue_pb2 as anyvalue__pb2$/from . import anyvalue_pb2 as anyvalue__pb2/' opamp_pb2.py
    rm -f opamp_pb2.py.bak
    echo "✓ Fixed import in opamp_pb2.py"
fi

echo ""
echo "✓ Protobuf bindings regenerated successfully!"
echo "  - anyvalue_pb2.py"
echo "  - opamp_pb2.py"

