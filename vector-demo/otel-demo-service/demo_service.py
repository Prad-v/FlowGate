#!/usr/bin/env python3
"""
OpenTelemetry Demo Service
Generates metrics, logs, and traces and sends them to Flowgate Gateway via OTLP HTTP.
"""

import time
import random
import logging
import signal
import sys
from datetime import datetime
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

# Configuration
GATEWAY_ENDPOINT = "http://gateway:4318"
SERVICE_NAME = "otel-demo-service"
SERVICE_VERSION = "1.0.0"
LOG_INTERVAL = 1  # seconds
METRIC_INTERVAL = 5  # seconds
TRACE_INTERVAL = 2  # seconds

# Setup resource
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: SERVICE_NAME,
    ResourceAttributes.SERVICE_VERSION: SERVICE_VERSION,
    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "demo",
})

# Setup Tracer
trace_provider = TracerProvider(resource=resource)
otlp_trace_exporter = OTLPSpanExporter(
    endpoint=f"{GATEWAY_ENDPOINT}/v1/traces",
    headers={"Content-Type": "application/json"},
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Setup Metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(
        endpoint=f"{GATEWAY_ENDPOINT}/v1/metrics",
        headers={"Content-Type": "application/json"},
    ),
    export_interval_millis=METRIC_INTERVAL * 1000,
)
metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metric_provider)
meter = metrics.get_meter(__name__)

# Create metrics
request_counter = meter.create_counter(
    name="demo_requests_total",
    description="Total number of requests",
    unit="1",
)
request_duration = meter.create_histogram(
    name="demo_request_duration_seconds",
    description="Request duration in seconds",
    unit="s",
)
active_connections = meter.create_up_down_counter(
    name="demo_active_connections",
    description="Number of active connections",
    unit="1",
)

# Setup Logs
log_provider = LoggerProvider(resource=resource)
otlp_log_exporter = OTLPLogExporter(
    endpoint=f"{GATEWAY_ENDPOINT}/v1/logs",
    headers={"Content-Type": "application/json"},
)
log_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
handler = LoggingHandler(level=logging.NOTSET, logger_provider=log_provider)

# Configure Python logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    global running
    print("\nShutting down gracefully...")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def generate_trace():
    """Generate a sample trace"""
    with tracer.start_as_current_span("demo_operation") as span:
        span.set_attribute("operation.type", "demo")
        span.set_attribute("operation.id", random.randint(1000, 9999))
        
        # Simulate some work
        time.sleep(random.uniform(0.01, 0.1))
        
        # Create a child span
        with tracer.start_as_current_span("demo_sub_operation") as child_span:
            child_span.set_attribute("sub_operation.type", "processing")
            time.sleep(random.uniform(0.01, 0.05))
            child_span.set_status(trace.Status(trace.StatusCode.OK))
        
        span.set_status(trace.Status(trace.StatusCode.OK))

def generate_logs():
    """Generate sample logs"""
    log_levels = [logging.INFO, logging.WARNING, logging.ERROR, logging.DEBUG]
    log_messages = [
        "Processing user request",
        "Database query executed successfully",
        "Cache hit for key: user_123",
        "Failed to connect to external service",
        "Authentication successful",
        "Rate limit exceeded",
        "Configuration reloaded",
        "Health check passed",
    ]
    
    level = random.choice(log_levels)
    message = random.choice(log_messages)
    
    extra_attrs = {
        "user_id": f"user_{random.randint(1, 1000)}",
        "request_id": f"req_{random.randint(10000, 99999)}",
        "component": random.choice(["api", "database", "cache", "auth"]),
    }
    
    logger.log(level, message, extra=extra_attrs)

def generate_metrics():
    """Generate sample metrics"""
    # Increment request counter
    request_counter.add(
        random.randint(1, 10),
        {
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "status": random.choice(["200", "404", "500"]),
            "endpoint": random.choice(["/api/users", "/api/orders", "/api/products"]),
        }
    )
    
    # Record request duration
    request_duration.record(
        random.uniform(0.01, 2.0),
        {
            "method": random.choice(["GET", "POST"]),
            "endpoint": random.choice(["/api/users", "/api/orders"]),
        }
    )
    
    # Update active connections (simulate connections)
    connections = random.randint(5, 50)
    active_connections.add(
        connections - 25,  # Relative change
        {"server": "demo-server-1"},
    )

def main():
    """Main service loop"""
    print(f"Starting OpenTelemetry Demo Service")
    print(f"  Service: {SERVICE_NAME} v{SERVICE_VERSION}")
    print(f"  Gateway: {GATEWAY_ENDPOINT}")
    print(f"  Log interval: {LOG_INTERVAL}s")
    print(f"  Metric interval: {METRIC_INTERVAL}s")
    print(f"  Trace interval: {TRACE_INTERVAL}s")
    print("Press Ctrl+C to stop\n")
    
    log_count = 0
    trace_count = 0
    metric_count = 0
    
    try:
        while running:
            # Generate logs
            if log_count % LOG_INTERVAL == 0:
                generate_logs()
            
            # Generate traces
            if trace_count % TRACE_INTERVAL == 0:
                generate_trace()
            
            # Generate metrics (handled by PeriodicExportingMetricReader)
            if metric_count % METRIC_INTERVAL == 0:
                generate_metrics()
            
            log_count += 1
            trace_count += 1
            metric_count += 1
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Flush all exporters
        trace_provider.force_flush()
        metric_provider.force_flush()
        log_provider.force_flush()
        print("Exporters flushed. Goodbye!")

if __name__ == "__main__":
    main()

