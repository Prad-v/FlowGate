"""Gateway service"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repositories.gateway_repository import GatewayRepository
from app.models.gateway import Gateway, GatewayStatus, OpAMPConnectionStatus, OpAMPRemoteConfigStatus
from app.schemas.gateway import GatewayCreate, GatewayUpdate


class GatewayService:
    """Service for gateway operations"""

    def __init__(self, db: Session):
        self.repository = GatewayRepository(db)
        self.db = db

    def register_gateway(
        self, gateway_data: GatewayCreate, org_id: UUID, registration_token_id: Optional[UUID] = None
    ) -> Gateway:
        """Register a new gateway"""
        # Check if gateway already exists
        existing = self.repository.get_by_instance_id(gateway_data.instance_id)
        if existing:
            # Update existing gateway
            existing.name = gateway_data.name
            existing.hostname = gateway_data.hostname
            existing.ip_address = gateway_data.ip_address
            existing.extra_metadata = gateway_data.metadata
            existing.status = GatewayStatus.ACTIVE
            existing.last_seen = datetime.utcnow()
            if registration_token_id:
                existing.registration_token_id = registration_token_id
            return self.repository.update(existing)

        # Create new gateway
        gateway = Gateway(
            name=gateway_data.name,
            instance_id=gateway_data.instance_id,
            org_id=org_id,
            status=GatewayStatus.REGISTERED,
            hostname=gateway_data.hostname,
            ip_address=gateway_data.ip_address,
            extra_metadata=gateway_data.metadata,
            last_seen=datetime.utcnow(),
            registration_token_id=registration_token_id,
        )
        return self.repository.create(gateway)

    def get_gateway(self, gateway_id: UUID, org_id: UUID) -> Optional[Gateway]:
        """Get a gateway by ID"""
        return self.repository.get(gateway_id, org_id)

    def get_gateways(self, org_id: UUID) -> List[Gateway]:
        """Get all gateways for an organization"""
        return self.repository.get_by_org(org_id)

    def get_active_gateways(self, org_id: UUID) -> List[Gateway]:
        """Get all active gateways"""
        return self.repository.get_active_gateways(org_id)

    def update_gateway(self, gateway_id: UUID, org_id: UUID, update_data: GatewayUpdate) -> Optional[Gateway]:
        """Update a gateway"""
        gateway = self.repository.get(gateway_id, org_id)
        if not gateway:
            return None

        if update_data.name is not None:
            gateway.name = update_data.name
        if update_data.status is not None:
            gateway.status = update_data.status
        if update_data.hostname is not None:
            gateway.hostname = update_data.hostname
        if update_data.ip_address is not None:
            gateway.ip_address = update_data.ip_address
        if update_data.metadata is not None:
            gateway.extra_metadata = update_data.metadata
        if update_data.current_config_version is not None:
            gateway.current_config_version = update_data.current_config_version

        return self.repository.update(gateway)

    def update_heartbeat(self, instance_id: str) -> Optional[Gateway]:
        """Update gateway heartbeat (last_seen)"""
        gateway = self.repository.get_by_instance_id(instance_id)
        if gateway:
            gateway.status = GatewayStatus.ACTIVE
            return self.repository.update_last_seen(gateway.id)
        return None

    def delete_gateway(self, gateway_id: UUID, org_id: UUID) -> bool:
        """Delete a gateway"""
        return self.repository.delete(gateway_id, org_id)

    def get_agent_health(self, gateway_id: UUID, org_id: UUID) -> Dict[str, Any]:
        """Calculate and return agent health status"""
        gateway = self.repository.get(gateway_id, org_id)
        if not gateway:
            return None

        now = datetime.utcnow()
        last_seen = gateway.last_seen
        seconds_since_last_seen = None
        uptime_seconds = None
        health_score = 0
        status_str = "offline"

        if gateway.status in [GatewayStatus.INACTIVE, GatewayStatus.ERROR]:
            status_str = "offline"
            health_score = 0
        elif last_seen:
            delta = now - last_seen.replace(tzinfo=None) if last_seen.tzinfo else now - last_seen
            seconds_since_last_seen = int(delta.total_seconds())
            
            if seconds_since_last_seen <= 60:
                status_str = "healthy"
                health_score = 100
            elif seconds_since_last_seen <= 300:
                status_str = "warning"
                health_score = 50
            else:
                status_str = "unhealthy"
                health_score = 20

            # Calculate uptime if gateway has been seen
            if gateway.created_at:
                uptime_delta = now - gateway.created_at.replace(tzinfo=None) if gateway.created_at.tzinfo else now - gateway.created_at
                uptime_seconds = int(uptime_delta.total_seconds())
        else:
            status_str = "unhealthy"
            health_score = 10

        return {
            "status": status_str,
            "last_seen": last_seen,
            "seconds_since_last_seen": seconds_since_last_seen,
            "uptime_seconds": uptime_seconds,
            "health_score": health_score,
        }

    def get_agent_version(self, gateway_id: UUID, org_id: UUID) -> Dict[str, Any]:
        """Extract and return version information from metadata"""
        gateway = self.repository.get(gateway_id, org_id)
        if not gateway:
            return None

        metadata = gateway.extra_metadata or {}
        
        return {
            "agent_version": metadata.get("version"),
            "otel_version": metadata.get("otel_version"),
            "capabilities": metadata.get("capabilities", []),
            "metadata": metadata,
        }

    def get_agent_config(self, gateway_id: UUID, org_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current deployed config for agent"""
        gateway = self.repository.get(gateway_id, org_id)
        if not gateway:
            return None

        from app.services.opamp_service import OpAMPService
        opamp_service = OpAMPService(self.db)
        config = opamp_service.get_config_for_gateway(gateway.instance_id)
        
        if config:
            return {
                "config_yaml": config.get("config_yaml", ""),
                "config_version": config.get("version"),
                "deployment_id": config.get("deployment_id"),
                "last_updated": gateway.updated_at,
            }
        
        # If no active deployment, return the base collector configuration
        # This allows users to see what config the gateway is currently using
        base_config = """receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-collector'
          scrape_interval: 10s
          static_configs:
            - targets: ['localhost:8888']

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    limit_mib: 512
    check_interval: 1s

exporters:
  otlp:
    endpoint: localhost:4317
    tls:
      insecure: true
  otlp/observability-backend:
    endpoint: vector-observability-backend:4317
    tls:
      insecure: true
  debug:
    verbosity: normal

service:
  pipelines:
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, batch]
      exporters: [otlp/observability-backend, debug]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/observability-backend, debug]
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/observability-backend, debug]
  
  extensions: []
  
  telemetry:
    logs:
      level: info
    metrics:
      level: detailed
"""
        
        return {
            "config_yaml": base_config,
            "config_version": gateway.current_config_version or 0,
            "deployment_id": None,
            "last_updated": gateway.updated_at or gateway.created_at,
        }

    def get_agent_metrics(self, gateway_id: UUID, org_id: UUID) -> Dict[str, Any]:
        """Get agent performance metrics"""
        gateway = self.repository.get(gateway_id, org_id)
        if not gateway:
            return None

        metadata = gateway.extra_metadata or {}
        metrics = metadata.get("metrics", {})
        
        return {
            "logs_processed": metrics.get("logs_processed"),
            "errors": metrics.get("errors"),
            "latency_ms": metrics.get("latency_ms"),
            "last_updated": gateway.last_seen,
        }

    def update_opamp_status(
        self, 
        instance_id: str, 
        connection_status: OpAMPConnectionStatus,
        transport_type: Optional[str] = None
    ) -> Optional[Gateway]:
        """Update OpAMP connection status"""
        gateway = self.repository.get_by_instance_id(instance_id)
        if gateway:
            gateway.opamp_connection_status = connection_status
            if transport_type:
                gateway.opamp_transport_type = transport_type
            return self.repository.update(gateway)
        return None

    def update_opamp_remote_config_status(
        self,
        instance_id: str,
        remote_config_status: OpAMPRemoteConfigStatus
    ) -> Optional[Gateway]:
        """Update OpAMP remote config status"""
        gateway = self.repository.get_by_instance_id(instance_id)
        if gateway:
            gateway.opamp_remote_config_status = remote_config_status
            return self.repository.update(gateway)
        return None

    def update_opamp_sequence_num(
        self,
        instance_id: str,
        sequence_num: int
    ) -> Optional[Gateway]:
        """Update last OpAMP sequence number"""
        gateway = self.repository.get_by_instance_id(instance_id)
        if gateway:
            gateway.opamp_last_sequence_num = sequence_num
            return self.repository.update(gateway)
        return None

    def update_opamp_capabilities(
        self,
        instance_id: str,
        agent_capabilities: Optional[int] = None,
        server_capabilities: Optional[int] = None
    ) -> Optional[Gateway]:
        """Store agent and server capabilities"""
        gateway = self.repository.get_by_instance_id(instance_id)
        if gateway:
            if agent_capabilities is not None:
                gateway.opamp_agent_capabilities = agent_capabilities
            if server_capabilities is not None:
                gateway.opamp_server_capabilities = server_capabilities
            return self.repository.update(gateway)
        return None

    def update_opamp_config_hashes(
        self,
        instance_id: str,
        effective_config_hash: Optional[str] = None,
        remote_config_hash: Optional[str] = None
    ) -> Optional[Gateway]:
        """Update OpAMP config hashes"""
        gateway = self.repository.get_by_instance_id(instance_id)
        if gateway:
            if effective_config_hash is not None:
                gateway.opamp_effective_config_hash = effective_config_hash
            if remote_config_hash is not None:
                gateway.opamp_remote_config_hash = remote_config_hash
            return self.repository.update(gateway)
        return None

    def mark_registration_failed(
        self,
        instance_id: str,
        failure_reason: str
    ) -> Optional[Gateway]:
        """Mark registration as failed"""
        gateway = self.repository.get_by_instance_id(instance_id)
        if gateway:
            gateway.opamp_registration_failed_at = datetime.utcnow()
            gateway.opamp_registration_failure_reason = failure_reason
            gateway.opamp_connection_status = OpAMPConnectionStatus.FAILED
            return self.repository.update(gateway)
        return None

    def clear_registration_failure(
        self,
        instance_id: str
    ) -> Optional[Gateway]:
        """Clear registration failure status"""
        gateway = self.repository.get_by_instance_id(instance_id)
        if gateway:
            gateway.opamp_registration_failed_at = None
            gateway.opamp_registration_failure_reason = None
            if gateway.opamp_connection_status == OpAMPConnectionStatus.FAILED:
                gateway.opamp_connection_status = OpAMPConnectionStatus.NEVER_CONNECTED
            return self.repository.update(gateway)
        return None

    def get_opamp_status(self, gateway_id: UUID, org_id: UUID) -> Optional[Dict[str, Any]]:
        """Get comprehensive OpAMP status information"""
        gateway = self.repository.get(gateway_id, org_id)
        if not gateway:
            return None

        from app.services.opamp_capabilities import (
            AgentCapabilities, ServerCapabilities, format_capabilities_display
        )

        # Decode capabilities
        agent_capabilities_decoded = []
        server_capabilities_decoded = []
        agent_capabilities_display = None
        server_capabilities_display = None

        if gateway.opamp_agent_capabilities is not None:
            agent_capabilities_decoded = AgentCapabilities.decode_capabilities(
                gateway.opamp_agent_capabilities
            )
            agent_capabilities_display = format_capabilities_display(
                gateway.opamp_agent_capabilities,
                agent_capabilities_decoded
            )

        if gateway.opamp_server_capabilities is not None:
            server_capabilities_decoded = ServerCapabilities.decode_capabilities(
                gateway.opamp_server_capabilities
            )
            server_capabilities_display = format_capabilities_display(
                gateway.opamp_server_capabilities,
                server_capabilities_decoded
            )

        # Handle enum fields - they're already strings from the database
        connection_status = gateway.opamp_connection_status
        if connection_status and hasattr(connection_status, 'value'):
            connection_status = connection_status.value
        
        remote_config_status = gateway.opamp_remote_config_status
        if remote_config_status and hasattr(remote_config_status, 'value'):
            remote_config_status = remote_config_status.value
        
        return {
            "opamp_connection_status": connection_status,
            "opamp_remote_config_status": remote_config_status,
            "opamp_last_sequence_num": gateway.opamp_last_sequence_num,
            "opamp_transport_type": gateway.opamp_transport_type,
            "opamp_agent_capabilities": gateway.opamp_agent_capabilities,
            "opamp_agent_capabilities_decoded": agent_capabilities_decoded,
            "opamp_agent_capabilities_display": agent_capabilities_display,
            "opamp_server_capabilities": gateway.opamp_server_capabilities,
            "opamp_server_capabilities_decoded": server_capabilities_decoded,
            "opamp_server_capabilities_display": server_capabilities_display,
            "opamp_effective_config_hash": gateway.opamp_effective_config_hash,
            "opamp_remote_config_hash": gateway.opamp_remote_config_hash,
            "opamp_registration_failed": gateway.opamp_registration_failed_at is not None,
            "opamp_registration_failed_at": gateway.opamp_registration_failed_at,
            "opamp_registration_failure_reason": gateway.opamp_registration_failure_reason,
        }

