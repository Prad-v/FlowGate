"""OpAMP Protocol Service - Handles OpAMP Protobuf messages

Implements OpAMP protocol message handling according to:
https://opentelemetry.io/docs/specs/opamp/
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.services.opamp_service import OpAMPService
from app.services.gateway_service import GatewayService
from app.services.opamp_config_service import OpAMPConfigService
from app.models.gateway import OpAMPRemoteConfigStatus, ManagementMode
from app.services.opamp_capabilities import (
    AgentCapabilities,
    ServerCapabilities,
    negotiate_capabilities
)
from app.services.opamp_supervisor_service import OpAMPSupervisorService
from app.protobufs import opamp_pb2
import logging

logger = logging.getLogger(__name__)


class OpAMPProtocolService:
    """Service for handling OpAMP protocol messages"""
    
    def __init__(self, db: Session):
        self.db = db
        self.opamp_service = OpAMPService(db)
        self.gateway_service = GatewayService(db)
        self.config_service = OpAMPConfigService(db)
        self.supervisor_service = OpAMPSupervisorService(db)
    
    def process_agent_to_server(
        self,
        instance_id: str,
        message: opamp_pb2.AgentToServer
    ) -> opamp_pb2.ServerToAgent:
        """
        Process AgentToServer message and return ServerToAgent response
        
        Args:
            instance_id: Gateway instance identifier
            message: Parsed AgentToServer message (dict representation)
        
        Returns:
            ServerToAgent message (dict representation)
        """
        # Get gateway
        gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
        if not gateway:
            raise ValueError(f"Gateway not found: {instance_id}")
        
        # Update heartbeat
        self.gateway_service.update_heartbeat(instance_id)
        
        # Extract and store OpAMP-specific data from message
        # Extract sequence number (uint64, always present in proto3, defaults to 0)
        # In proto3, scalar fields don't have presence, so we can't use HasField()
        # sequence_num will be 0 if not set, which is valid
        sequence_num = message.sequence_num
        if sequence_num > 0:  # Only update if non-zero (0 means not set or first message)
            self.gateway_service.update_opamp_sequence_num(instance_id, sequence_num)
        
        # Extract agent capabilities (uint64, always present, defaults to 0)
        agent_capabilities = message.capabilities
        
        # Store agent and server capabilities
        server_capabilities = ServerCapabilities.get_all_capabilities()
        self.gateway_service.update_opamp_capabilities(
            instance_id,
            agent_capabilities=agent_capabilities,
            server_capabilities=server_capabilities
        )
        
        # Extract remote config status and update audit log
        if message.HasField("remote_config_status"):
            remote_config_status = message.remote_config_status
            # Map OpAMP protobuf enum to our model enum
            status_mapping = {
                opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_UNSET: OpAMPRemoteConfigStatus.UNSET,
                opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLIED: OpAMPRemoteConfigStatus.APPLIED,
                opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLYING: OpAMPRemoteConfigStatus.APPLYING,
                opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_FAILED: OpAMPRemoteConfigStatus.FAILED,
            }
            opamp_status = status_mapping.get(
                remote_config_status.status,
                OpAMPRemoteConfigStatus.UNSET
            )
            self.gateway_service.update_opamp_remote_config_status(instance_id, opamp_status)
            
            # Store config hash if present and update audit log
            if remote_config_status.last_remote_config_hash:
                hash_bytes = remote_config_status.last_remote_config_hash
                try:
                    hash_str = hash_bytes.decode('utf-8') if isinstance(hash_bytes, bytes) else str(hash_bytes)
                    self.gateway_service.update_opamp_config_hashes(
                        instance_id,
                        effective_config_hash=None,  # Will be set from effective_config if present
                        remote_config_hash=hash_str
                    )
                    
                    # Get effective config hash if present
                    effective_hash = None
                    if message.HasField("effective_config") and message.effective_config.hash:
                        eff_hash_bytes = message.effective_config.hash
                        try:
                            effective_hash = eff_hash_bytes.decode('utf-8') if isinstance(eff_hash_bytes, bytes) else str(eff_hash_bytes)
                        except (ValueError, AttributeError):
                            pass
                    
                    # Update config status in audit log
                    status_str = opamp_status.value if opamp_status else 'UNSET'
                    error_msg = None
                    if remote_config_status.HasField("error_message"):
                        error_msg = remote_config_status.error_message
                    
                    self.config_service.update_config_status_from_agent(
                        instance_id=instance_id,
                        config_hash=hash_str,
                        status=status_str,
                        effective_config_hash=effective_hash,
                        error_message=error_msg
                    )
                except (ValueError, AttributeError):
                    pass
        
        # Extract effective config hash if present
        if message.HasField("effective_config"):
            effective_config = message.effective_config
            if effective_config.config_map:
                # Calculate hash from effective config (simplified - use hash field if present)
                # In practice, we'd compute a hash of the config content
                effective_hash = None
                if hasattr(effective_config, 'hash') and effective_config.hash:
                    effective_hash_bytes = effective_config.hash
                    try:
                        effective_hash = effective_hash_bytes.decode('utf-8') if isinstance(effective_hash_bytes, bytes) else str(effective_hash_bytes)
                    except (ValueError, AttributeError):
                        pass
                
                if effective_hash:
                    self.gateway_service.update_opamp_config_hashes(
                        instance_id,
                        effective_config_hash=effective_hash,
                        remote_config_hash=None  # Don't overwrite if already set
                    )
        
        # Detect if this is a supervisor-managed agent
        # Supervisor typically sends agent_description and health fields
        is_supervisor_managed = message.HasField("agent_description") or message.HasField("health")
        
        # Extract agent description for version info (if present)
        if message.HasField("agent_description"):
            agent_desc = message.agent_description
            # Update gateway metadata with version info
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                # Update management mode if supervisor-managed
                if is_supervisor_managed:
                    gateway.management_mode = ManagementMode.SUPERVISOR.value
                
                metadata = gateway.extra_metadata or {}
                if agent_desc.HasField("version"):
                    metadata["version"] = agent_desc.version
                if agent_desc.HasField("name"):
                    metadata["agent_name"] = agent_desc.name
                if agent_desc.HasField("identifying_attributes"):
                    # Store identifying attributes
                    attrs = {}
                    for attr in agent_desc.identifying_attributes:
                        if attr.HasField("key") and attr.HasField("value"):
                            attrs[attr.key] = attr.value.string_value if attr.value.HasField("string_value") else str(attr.value)
                    metadata["identifying_attributes"] = attrs
                gateway.extra_metadata = metadata
                self.gateway_service.repository.update(gateway)
        
        # Extract health information (if present)
        if message.HasField("health"):
            health = message.health
            # Update gateway metadata with health info
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                metadata = gateway.extra_metadata or {}
                health_info = metadata.get("health", {})
                if health.HasField("healthy"):
                    health_info["healthy"] = health.healthy
                if health.HasField("start_time_unix_nano"):
                    health_info["start_time_unix_nano"] = health.start_time_unix_nano
                if health.HasField("last_error"):
                    health_info["last_error"] = health.last_error
                metadata["health"] = health_info
                gateway.extra_metadata = metadata
                self.gateway_service.repository.update(gateway)
        
        # Store supervisor-specific status if supervisor-managed
        if is_supervisor_managed:
            supervisor_status = {}
            
            # Extract agent_description if present
            if message.HasField("agent_description"):
                agent_desc = message.agent_description
                supervisor_status["agent_description"] = {
                    "identifying_attributes": [
                        {"key": attr.key, "value": attr.value.string_value if attr.value.HasField("string_value") else str(attr.value)}
                        for attr in agent_desc.identifying_attributes
                    ] if agent_desc.identifying_attributes else [],
                    "non_identifying_attributes": [
                        {"key": attr.key, "value": attr.value.string_value if attr.value.HasField("string_value") else str(attr.value)}
                        for attr in agent_desc.non_identifying_attributes
                    ] if agent_desc.non_identifying_attributes else [],
                }
            
            # Extract health if present
            if message.HasField("health"):
                health = message.health
                supervisor_status["health"] = {
                    "healthy": health.healthy if health.HasField("healthy") else None,
                    "start_time_unix_nano": health.start_time_unix_nano if health.HasField("start_time_unix_nano") else None,
                    "last_error": health.last_error if health.HasField("last_error") else None,
                }
            
            # Update supervisor status
            if supervisor_status:
                self.supervisor_service.update_supervisor_status(
                    instance_id,
                    supervisor_status
                )
        
        # Build ServerToAgent Protobuf message
        server_message = opamp_pb2.ServerToAgent()
        
        # Set instance UID (must be 16 bytes per OpAMP spec - UUID v7 format)
        try:
            gateway_uuid = UUID(str(gateway.id))
            # UUID.bytes gives us 16 bytes
            server_message.instance_uid = gateway_uuid.bytes
        except (ValueError, AttributeError):
            # Fallback: convert string to 16 bytes
            gateway_id_str = str(gateway.id)
            # Pad or truncate to 16 bytes
            server_message.instance_uid = gateway_id_str.encode('utf-8')[:16].ljust(16, b'\x00')
        
        # Set server capabilities
        server_message.capabilities = server_capabilities
        
        # Handle remote config status if agent reports it (already processed above, but also update config version)
        if message.HasField("remote_config_status"):
            remote_config_status = message.remote_config_status
            # Agent is reporting status of last config we sent
            # Update gateway's config version if needed
            if remote_config_status.status == opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLIED:
                config_hash = remote_config_status.last_remote_config_hash
                # Try to extract version from hash if it's a string
                try:
                    hash_str = config_hash.decode('utf-8') if isinstance(config_hash, bytes) else str(config_hash)
                    if hash_str.startswith("v"):
                        version = int(hash_str[1:])
                        self.opamp_service.update_gateway_config_version(instance_id, version)
                except (ValueError, AttributeError):
                    pass
        
        # Check if we need to send new config
        # First check for pending OpAMP config deployments
        gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
        if gateway:
            from app.models.opamp_config_deployment import OpAMPConfigDeployment, OpAMPConfigDeploymentStatus
            from app.models.opamp_config_audit import OpAMPConfigAudit, OpAMPConfigAuditStatus
            
            # Check for pending deployment for this gateway
            pending_audit = self.db.query(OpAMPConfigAudit).join(OpAMPConfigDeployment).filter(
                and_(
                    OpAMPConfigAudit.gateway_id == gateway.id,
                    OpAMPConfigAudit.status == OpAMPConfigAuditStatus.PENDING,
                    OpAMPConfigDeployment.status.in_([
                        OpAMPConfigDeploymentStatus.PENDING,
                        OpAMPConfigDeploymentStatus.IN_PROGRESS
                    ])
                )
            ).order_by(OpAMPConfigAudit.created_at.desc()).first()
            
            if pending_audit:
                # Send config from pending deployment
                deployment = self.db.query(OpAMPConfigDeployment).filter(
                    OpAMPConfigDeployment.id == pending_audit.deployment_id
                ).first()
                
                if deployment:
                    remote_config = opamp_pb2.AgentRemoteConfig()
                    
                    # Create config map
                    config_map = opamp_pb2.AgentConfigMap()
                    config_file = opamp_pb2.AgentConfigFile()
                    config_file.body = deployment.config_yaml.encode('utf-8')
                    config_file.content_type = "text/yaml"
                    config_map.config_map[""].CopyFrom(config_file)
                    
                    remote_config.config.CopyFrom(config_map)
                    remote_config.config_hash = deployment.config_hash.encode('utf-8')
                    
                    server_message.remote_config.CopyFrom(remote_config)
                    
                    # Update audit entry status to APPLYING
                    pending_audit.status = OpAMPConfigAuditStatus.APPLYING
                    pending_audit.updated_at = datetime.utcnow()
                    self.db.commit()
                    
                    return server_message
        
        # Fallback to legacy config from deployments/templates
        current_config = self.opamp_service.get_config_for_gateway(instance_id)
        if current_config:
            # Check if agent needs this config
            agent_config_hash = None
            if message.HasField("effective_config"):
                # Agent has effective config, but we need to check if it matches
                pass
            
            config_version = current_config.get("version", 0)
            config_yaml = current_config.get("config_yaml", "")
            
            # Always send config for now (can be optimized later)
            remote_config = opamp_pb2.AgentRemoteConfig()
            
            # Create config map
            config_map = opamp_pb2.AgentConfigMap()
            config_file = opamp_pb2.AgentConfigFile()
            config_file.body = config_yaml.encode('utf-8')
            config_file.content_type = "text/yaml"
            # Use empty string as key for main config
            config_map.config_map[""].CopyFrom(config_file)
            
            remote_config.config.CopyFrom(config_map)
            remote_config.config_hash = f"v{config_version}".encode('utf-8')
            
            server_message.remote_config.CopyFrom(remote_config)
            
            # Store remote config hash
            self.gateway_service.update_opamp_config_hashes(
                instance_id,
                effective_config_hash=None,  # Don't overwrite
                remote_config_hash=f"v{config_version}"
            )
        
        return server_message
    
    def build_initial_server_message(
        self,
        instance_id: str
    ) -> opamp_pb2.ServerToAgent:
        """
        Build initial ServerToAgent message for agent connection
        
        Args:
            instance_id: Gateway instance identifier
        
        Returns:
            ServerToAgent Protobuf message
        """
        gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
        if not gateway:
            raise ValueError(f"Gateway not found: {instance_id}")
        
        server_capabilities = ServerCapabilities.get_all_capabilities()
        
        # Create ServerToAgent Protobuf message
        message = opamp_pb2.ServerToAgent()
        
        # Set instance UID (must be 16 bytes per OpAMP spec - UUID v7 format)
        try:
            gateway_uuid = UUID(str(gateway.id))
            # UUID.bytes gives us 16 bytes
            message.instance_uid = gateway_uuid.bytes
        except (ValueError, AttributeError):
            # Fallback: convert string to 16 bytes
            gateway_id_str = str(gateway.id)
            # Pad or truncate to 16 bytes
            message.instance_uid = gateway_id_str.encode('utf-8')[:16].ljust(16, b'\x00')
        
        # Set server capabilities
        message.capabilities = server_capabilities
        
        # Include initial config if available
        # First check for pending OpAMP config deployments
        gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
        if gateway:
            from app.models.opamp_config_deployment import OpAMPConfigDeployment, OpAMPConfigDeploymentStatus
            from app.models.opamp_config_audit import OpAMPConfigAudit, OpAMPConfigAuditStatus
            
            # Check for pending deployment for this gateway
            pending_audit = self.db.query(OpAMPConfigAudit).join(OpAMPConfigDeployment).filter(
                and_(
                    OpAMPConfigAudit.gateway_id == gateway.id,
                    OpAMPConfigAudit.status == OpAMPConfigAuditStatus.PENDING,
                    OpAMPConfigDeployment.status.in_([
                        OpAMPConfigDeploymentStatus.PENDING,
                        OpAMPConfigDeploymentStatus.IN_PROGRESS
                    ])
                )
            ).order_by(OpAMPConfigAudit.created_at.desc()).first()
            
            if pending_audit:
                # Send config from pending deployment
                deployment = self.db.query(OpAMPConfigDeployment).filter(
                    OpAMPConfigDeployment.id == pending_audit.deployment_id
                ).first()
                
                if deployment:
                    remote_config = opamp_pb2.AgentRemoteConfig()
                    
                    # Create config map
                    config_map = opamp_pb2.AgentConfigMap()
                    config_file = opamp_pb2.AgentConfigFile()
                    config_file.body = deployment.config_yaml.encode('utf-8')
                    config_file.content_type = "text/yaml"
                    config_map.config_map[""].CopyFrom(config_file)
                    
                    remote_config.config.CopyFrom(config_map)
                    remote_config.config_hash = deployment.config_hash.encode('utf-8')
                    
                    message.remote_config.CopyFrom(remote_config)
                    
                    # Update audit entry status to APPLYING
                    pending_audit.status = OpAMPConfigAuditStatus.APPLYING
                    pending_audit.updated_at = datetime.utcnow()
                    self.db.commit()
                    
                    return message
        
        # Fallback to legacy config from deployments/templates
        config = self.opamp_service.get_config_for_gateway(instance_id)
        if config:
            remote_config = opamp_pb2.AgentRemoteConfig()
            
            # Create config map
            config_map = opamp_pb2.AgentConfigMap()
            config_file = opamp_pb2.AgentConfigFile()
            config_file.body = config.get("config_yaml", "").encode('utf-8')
            config_file.content_type = "text/yaml"
            # Use empty string as key for main config
            config_map.config_map[""].CopyFrom(config_file)
            
            remote_config.config.CopyFrom(config_map)
            config_version = config.get('version', 0)
            remote_config.config_hash = f"v{config_version}".encode('utf-8')
            
            message.remote_config.CopyFrom(remote_config)
            
            # Store remote config hash
            self.gateway_service.update_opamp_config_hashes(
                instance_id,
                effective_config_hash=None,  # Don't overwrite
                remote_config_hash=f"v{config_version}"
            )
        
        return message
    
    def parse_agent_message(self, data: bytes) -> opamp_pb2.AgentToServer:
        """
        Parse AgentToServer message from protobuf bytes
        
        Args:
            data: Raw message data (protobuf bytes)
        
        Returns:
            Parsed AgentToServer Protobuf message
        """
        if not data:
            # Return empty message if no data
            return opamp_pb2.AgentToServer()
        
        # Parse Protobuf message
        try:
            agent_message = opamp_pb2.AgentToServer()
            agent_message.ParseFromString(data)
            return agent_message
        except Exception as e:
            # If parsing fails, return empty message
            # Log error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to parse AgentToServer message: {e}")
            return opamp_pb2.AgentToServer()
    
    def serialize_server_message(self, message: opamp_pb2.ServerToAgent) -> bytes:
        """
        Serialize ServerToAgent Protobuf message to bytes
        
        Args:
            message: ServerToAgent Protobuf message
        
        Returns:
            Serialized message as bytes (Protobuf wire format)
        """
        return message.SerializeToString()
    
    def create_error_response(
        self,
        error_type: int = opamp_pb2.ServerErrorResponseType_Unknown,
        error_message: str = "Unknown error"
    ) -> opamp_pb2.ServerToAgent:
        """
        Create a ServerToAgent error response message
        
        Args:
            error_type: ServerErrorResponseType enum value
            error_message: Human-readable error message
        
        Returns:
            ServerToAgent message with error_response set
        """
        error_response = opamp_pb2.ServerErrorResponse()
        error_response.type = error_type
        error_response.error_message = error_message
        
        server_message = opamp_pb2.ServerToAgent()
        server_message.error_response.CopyFrom(error_response)
        
        return server_message

