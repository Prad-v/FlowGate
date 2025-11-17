# Build stage
FROM golang:1.23-alpine AS builder

WORKDIR /build

# Copy go mod files
COPY go.mod go.sum* ./

# Download dependencies
RUN go mod download

# Copy source
COPY *.go ./

# Build binary
RUN CGO_ENABLED=0 GOOS=linux go build -o opamp-parser .

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /app

COPY --from=builder /build/opamp-parser .

ENTRYPOINT ["./opamp-parser"]

