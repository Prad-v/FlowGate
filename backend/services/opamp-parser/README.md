# OpAMP Protocol Parser (Go)

A Go-based binary for parsing and serializing OpAMP protobuf messages. This ensures 100% compatibility with Go-based OpAMP supervisor and collector.

## Usage

### Parse AgentToServer message

```bash
echo -n "<binary_protobuf_data>" | ./opamp-parser -mode=parse
```

Outputs JSON:
```json
{
  "success": true,
  "message": {
    "instance_uid": "...",
    "sequence_num": 123,
    "capabilities": 18437,
    ...
  }
}
```

### Serialize ServerToAgent message

```bash
echo '{"message": {...}}' | ./opamp-parser -mode=serialize > output.bin
```

## Building

```bash
go mod download
go build -o opamp-parser .
```

## Docker

```bash
docker build -t opamp-parser .
docker run -i opamp-parser -mode=parse < input.bin
```

