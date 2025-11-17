# Multi-stage build: Go parser + Python backend
# Stage 1: Build Go parser
FROM golang:1.23-alpine AS go-builder
WORKDIR /build
# Copy Go parser source (build context is ./backend/services)
COPY opamp-parser/go.mod opamp-parser/go.sum* ./
RUN go mod download 2>/dev/null || true
COPY opamp-parser/*.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -o opamp-parser .

# Stage 2: Python backend with Go parser
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY flowgate-backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Go parser binary from builder stage
COPY --from=go-builder /build/opamp-parser /app/bin/opamp-parser
RUN chmod +x /app/bin/opamp-parser && \
    mkdir -p /usr/local/bin && \
    ln -s /app/bin/opamp-parser /usr/local/bin/opamp-parser

# Copy application code
COPY flowgate-backend/ .

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
