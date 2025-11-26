"""OpAMP Supervisor UI Router

Endpoints matching example server UI functionality for supervisor management.
"""

import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.services.opamp_supervisor_service import OpAMPSupervisorService
from app.services.gateway_service import GatewayService
from app.services.opamp_config_service import OpAMPConfigService
from app.services.opamp_protocol_service import OpAMPProtocolService
from app.services.websocket_manager import get_websocket_manager
from app.models.gateway import Gateway, ManagementMode
from app.models.config_request import ConfigRequest, ConfigRequestStatus
from app.utils.auth import get_current_user, get_current_user_org_id
from app.models.user import User
from app.protobufs import opamp_pb2
from app.services.opamp_capabilities import ServerCapabilities

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supervisor/ui", tags=["supervisor-ui"])


class ConfigPushRequest(BaseModel):
    """Request model for pushing config via supervisor UI"""
    config_yaml: str


@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_agents_for_ui(
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get agents list for UI with supervisor status."""
    gateway_service = GatewayService(db)
    gateways = gateway_service.get_gateways(org_id)
    
    # Include both extension and supervisor-managed agents
    # but mark supervisor status
    agents = []
    for gateway in gateways:
        agent_info = {
            "instance_id": gateway.instance_id,
            "gateway_id": str(gateway.id),
            "name": gateway.name,
            "management_mode": gateway.management_mode,
            "opamp_connection_status": gateway.opamp_connection_status,
            "last_seen": gateway.last_seen.isoformat() if gateway.last_seen else None,
        }
        
        # Add supervisor-specific info if supervisor-managed
        if gateway.management_mode == ManagementMode.SUPERVISOR.value:
            supervisor_service = OpAMPSupervisorService(db)
            supervisor_status = supervisor_service.get_supervisor_status(gateway.instance_id)
            if supervisor_status:
                agent_info["supervisor_status"] = supervisor_status.get("supervisor_status", {})
        
        agents.append(agent_info)
    
    return agents


@router.get("/agents/{instance_id}", response_model=Dict[str, Any])
async def get_agent_details_for_ui(
    instance_id: str,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get comprehensive agent details for UI including all OpAMP data."""
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    supervisor_service = OpAMPSupervisorService(db)
    gateway_service = GatewayService(db)
    config_service = OpAMPConfigService(db)
    
    # Extract agent description from metadata or supervisor status
    metadata = gateway.extra_metadata or {}
    agent_version = metadata.get("version", {})
    agent_name = metadata.get("agent_name")
    identifying_attributes = metadata.get("identifying_attributes", {})
    health_info = metadata.get("health", {})
    
    # Get OpAMP status information
    opamp_status = gateway_service.get_opamp_status(gateway.id, org_id) or {}
    
    # Get comprehensive agent info
    agent_details = {
        "instance_id": gateway.instance_id,
        "gateway_id": str(gateway.id),
        "name": gateway.name,
        "management_mode": gateway.management_mode,
        "hostname": gateway.hostname,
        "ip_address": gateway.ip_address,
        "last_seen": gateway.last_seen.isoformat() if gateway.last_seen else None,
        
        # Agent version information from agent_description
        "agent_version": agent_version,
        "agent_name": agent_name,
        "identifying_attributes": identifying_attributes,
        
        # Health information
        "health": health_info,
        
        # OpAMP connection information
        "opamp_connection_status": opamp_status.get("opamp_connection_status"),
        "opamp_remote_config_status": opamp_status.get("opamp_remote_config_status"),
        "opamp_transport_type": opamp_status.get("opamp_transport_type"),
        "opamp_last_sequence_num": opamp_status.get("opamp_last_sequence_num"),
        
        # Capabilities
        "opamp_agent_capabilities": opamp_status.get("opamp_agent_capabilities"),
        "opamp_agent_capabilities_decoded": opamp_status.get("opamp_agent_capabilities_decoded", []),
        "opamp_agent_capabilities_display": opamp_status.get("opamp_agent_capabilities_display"),
        "opamp_server_capabilities": opamp_status.get("opamp_server_capabilities"),
        "opamp_server_capabilities_decoded": opamp_status.get("opamp_server_capabilities_decoded", []),
        "opamp_server_capabilities_display": opamp_status.get("opamp_server_capabilities_display"),
        
        # Config hashes
        "opamp_effective_config_hash": opamp_status.get("opamp_effective_config_hash"),
        "opamp_remote_config_hash": opamp_status.get("opamp_remote_config_hash"),
        
        # Registration status
        "opamp_registration_failed": opamp_status.get("opamp_registration_failed", False),
        "opamp_registration_failed_at": opamp_status.get("opamp_registration_failed_at").isoformat() if opamp_status.get("opamp_registration_failed_at") is not None else None,
        "opamp_registration_failure_reason": opamp_status.get("opamp_registration_failure_reason"),
        
        # Connection metrics
        "connection_metrics": {
            "last_seen": gateway.last_seen.isoformat() if gateway.last_seen else None,
            "sequence_num": gateway.opamp_last_sequence_num,
            "transport_type": gateway.opamp_transport_type,
        },
    }
    
    # Extract and enhance agent_description from supervisor status or metadata
    agent_description_data = {}
    supervisor_status_data = gateway.supervisor_status or {}
    
    # Get agent_description from supervisor_status
    if supervisor_status_data.get("agent_description"):
        agent_description_data = supervisor_status_data.get("agent_description", {})
    elif metadata.get("agent_description"):
        agent_description_data = metadata.get("agent_description", {})
    
    # Parse identifying_attributes to extract key fields
    identifying_attrs = agent_description_data.get("identifying_attributes", [])
    non_identifying_attrs = agent_description_data.get("non_identifying_attributes", [])
    
    # Extract identifiers from identifying_attributes
    instance_uid = None
    agent_type = None
    agent_version_str = None
    agent_id = None
    
    for attr in identifying_attrs:
        if isinstance(attr, dict):
            key = attr.get("key", "")
            value = attr.get("value", "")
            if key == "service.instance.id" or key == "service.instance.uid":
                instance_uid = value
            elif key == "service.name" or key == "otelcol.type":
                agent_type = value
            elif key == "service.version" or key == "otelcol.version":
                agent_version_str = value
            elif key == "service.id" or key == "agent.id":
                agent_id = value
    
    # Extract OS/Runtime info from non_identifying_attributes
    operating_system = None
    architecture = None
    labels = {}
    extensions = []
    build_info = {}
    
    for attr in non_identifying_attrs:
        if isinstance(attr, dict):
            key = attr.get("key", "")
            value = attr.get("value", "")
            if key == "os.type" or key == "os.name":
                operating_system = value
            elif key == "os.arch" or key == "host.arch":
                architecture = value
            elif key.startswith("k8s.") or key.startswith("host.") or key.startswith("env."):
                labels[key] = value
            elif key == "otelcol.extensions":
                if isinstance(value, list):
                    extensions = value
                elif isinstance(value, str):
                    extensions = [ext.strip() for ext in value.split(",")]
            elif key in ["build.git.sha", "build.timestamp", "distro.name"]:
                build_info[key] = value
    
    # Build enhanced agent_description
    if agent_description_data or instance_uid or agent_type:
        agent_details["agent_description"] = {
            "identifiers": {
                "instance_uid": instance_uid or gateway.instance_id,
                "agent_type": agent_type or agent_details.get("agent_name"),
                "agent_version": agent_version_str or (agent_version.get("version") if isinstance(agent_version, dict) else None),
                "agent_id": agent_id or gateway.instance_id,
            },
            "os_runtime": {
                "operating_system": operating_system,
                "architecture": architecture,
                "labels": labels,
                "extensions": extensions,
            },
            "build_info": build_info if build_info else None,
            "identifying_attributes": identifying_attrs,
            "non_identifying_attributes": non_identifying_attrs,
        }
    
    # Enhance health information
    health_data = health_info
    if supervisor_status_data.get("health"):
        health_data = supervisor_status_data.get("health", {})
    
    if health_data:
        # Determine status_code from healthy field
        status_code = "unknown"
        if health_data.get("healthy") is True:
            status_code = "healthy"
        elif health_data.get("healthy") is False:
            status_code = "unhealthy"
        elif health_data.get("healthy") is None:
            status_code = "degraded"
        
        agent_details["health"] = {
            "healthy": health_data.get("healthy"),
            "status_code": status_code,
            "status_message": health_data.get("last_error"),
            "start_time_unix_nano": health_data.get("start_time_unix_nano"),
            "last_error": health_data.get("last_error"),
            "raw": health_data,
        }
    
    # Add supervisor-specific details if supervisor-managed
    if gateway.management_mode == ManagementMode.SUPERVISOR.value:
        supervisor_status = supervisor_service.get_supervisor_status(instance_id)
        agent_description = supervisor_service.get_agent_description(instance_id)
        
        if supervisor_status:
            agent_details["supervisor_status"] = supervisor_status.get("supervisor_status", {})
            
            # Extract available_components from supervisor_status
            available_components_data = supervisor_status.get("supervisor_status", {}).get("available_components")
            if available_components_data:
                agent_details["available_components"] = {
                    "components": available_components_data.get("components", []),
                    "hash": available_components_data.get("hash"),
                    "last_updated": available_components_data.get("last_updated")
                }
        
        if agent_description:
            desc = agent_description.get("agent_description", {})
            if desc and not agent_details.get("agent_description"):
                agent_details["agent_description"] = desc
    
    # Get effective config content
    # Priority: 1. Stored content from OpAMP message, 2. Match hash with deployment
    effective_config_hash = gateway.opamp_effective_config_hash
    effective_config_yaml = gateway.opamp_effective_config_content  # Direct from OpAMP message
    effective_config_version = None
    effective_config_deployment_name = None
    
    # If we have stored content from OpAMP, use it
    # Otherwise, try to find deployment by hash
    if not effective_config_yaml and effective_config_hash:
        from app.models.opamp_config_deployment import OpAMPConfigDeployment
        deployment = db.query(OpAMPConfigDeployment).filter(
            OpAMPConfigDeployment.config_hash == effective_config_hash
        ).first()
        
        if deployment:
            effective_config_yaml = deployment.config_yaml
            effective_config_version = deployment.config_version
            effective_config_deployment_name = deployment.name
    
    agent_details["effective_config"] = {
        "hash": effective_config_hash,
        "config_yaml": effective_config_yaml,  # Now includes content from OpAMP message
        "config_version": effective_config_version,
        "deployment_name": effective_config_deployment_name,
        "source": "opamp_message" if gateway.opamp_effective_config_content else ("deployment" if effective_config_yaml else None)
    }
    
    # Get current config (pending/active deployment)
    try:
        current_config = config_service.get_current_config_for_gateway(gateway.id, org_id)
        if current_config:
            agent_details["current_config"] = {
                "config_yaml": current_config.get("config_yaml", ""),
                "config_version": current_config.get("config_version"),
                "deployment_id": str(current_config.get("deployment_id")) if current_config.get("deployment_id") else None,
            }
        else:
            agent_details["current_config"] = None
    except Exception as e:
        # Config retrieval may fail, that's okay
        agent_details["current_config"] = None
        agent_details["config_error"] = str(e)
    
    # Get package statuses
    try:
        package_statuses = gateway_service.get_package_statuses(gateway.id, org_id)
        agent_details["package_statuses"] = package_statuses
    except Exception as e:
        logger.warning(f"Failed to retrieve package statuses: {e}")
        agent_details["package_statuses"] = []
    
    # Get connection settings hashes
    try:
        connection_settings_hashes = gateway_service.get_connection_settings_hashes(gateway.id, org_id)
        agent_details["connection_settings_hashes"] = connection_settings_hashes
    except Exception as e:
        logger.warning(f"Failed to retrieve connection settings hashes: {e}")
        agent_details["connection_settings_hashes"] = {
            "own_metrics": None,
            "own_logs": None,
            "own_traces": None,
        }
    
    # Add heartbeat timing information
    is_online = False
    if gateway.last_seen:
        last_seen_naive = gateway.last_seen.replace(tzinfo=None) if gateway.last_seen.tzinfo else gateway.last_seen
        now_naive = datetime.utcnow()
        is_online = (now_naive - last_seen_naive).total_seconds() < 300
    
    agent_details["heartbeat_timing"] = {
        "last_seen": gateway.last_seen.isoformat() if gateway.last_seen else None,
        "sequence_num": gateway.opamp_last_sequence_num,
        "is_online": is_online,
    }
    
    return agent_details


@router.post("/agents/{instance_id}/config", response_model=Dict[str, Any])
async def push_config_via_supervisor_ui(
    instance_id: str,
    config_request: ConfigPushRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Push config via supervisor UI (similar to example server UI)."""
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    # Validate config
    config_service = OpAMPConfigService(db)
    validation_result = config_service.validate_config_yaml(config_request.config_yaml)
    
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Configuration validation failed",
                "errors": [
                    {
                        "level": e.level,
                        "message": e.message,
                        "field": e.field,
                        "line": e.line
                    }
                    for e in validation_result.errors
                ],
                "warnings": [
                    {
                        "level": w.level,
                        "message": w.message,
                        "field": w.field,
                        "line": w.line
                    }
                    for w in validation_result.warnings
                ]
            }
        )
    
    # Create a deployment for this config push
    # Use a simple name for UI-initiated pushes
    deployment_name = f"UI Config Push - {instance_id}"
    
    try:
        deployment, audit_entries = config_service.create_config_deployment(
            name=deployment_name,
            config_yaml=config_request.config_yaml,
            org_id=org_id,
            rollout_strategy="immediate",
            target_tags=None,  # Push to all agents (or could filter by instance_id)
            ignore_failures=False,
            created_by=current_user.id
        )
        
        # Push config to agents
        push_result = config_service.push_config_to_agents(deployment.id, org_id)
        
        return {
            "message": "Configuration pushed successfully",
            "deployment_id": str(deployment.id),
            "config_version": deployment.config_version,
            "instance_id": instance_id,
            "push_result": push_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to push configuration: {str(e)}"
        )


@router.get("/agents/{instance_id}/effective-config")
async def get_effective_config(
    instance_id: str,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get effective config that agent is actually running.
    
    Returns the effective configuration reported by the agent via OpAMP.
    Priority: 1. Stored content from OpAMP message, 2. Match hash with deployment.
    
    WARNING: The effective_config reported by the OpAMP extension may be INCOMPLETE.
    Some components (e.g., debug exporters, telemetry service settings) may be missing.
    This is a known limitation in the OpAMP extension.
    Reference: https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/29117
    """
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    # Get effective config hash and content from gateway
    effective_config_hash = gateway.opamp_effective_config_hash
    effective_config_yaml = gateway.opamp_effective_config_content  # Direct from OpAMP message
    effective_config_version = None
    effective_config_deployment_name = None
    source = None
    
    # If we have stored content from OpAMP, use it
    if effective_config_yaml:
        source = "opamp_message"
    # Otherwise, try to find deployment by hash
    elif effective_config_hash:
        from app.models.opamp_config_deployment import OpAMPConfigDeployment
        deployment = db.query(OpAMPConfigDeployment).filter(
            OpAMPConfigDeployment.config_hash == effective_config_hash
        ).first()
        
        if deployment:
            effective_config_yaml = deployment.config_yaml
            effective_config_version = deployment.config_version
            effective_config_deployment_name = deployment.name
            source = "deployment"
    
    if not effective_config_hash:
        return {
            "instance_id": instance_id,
            "effective_config_hash": None,
            "config_yaml": None,
            "message": "No effective config hash reported by agent"
        }
    
    if effective_config_yaml:
        return {
            "instance_id": instance_id,
            "effective_config_hash": effective_config_hash,
            "config_version": effective_config_version,
            "config_yaml": effective_config_yaml,
            "deployment_name": effective_config_deployment_name,
            "source": source,
            "warning": "The effective_config reported by the OpAMP extension may be incomplete. Some components (e.g., debug exporters, telemetry service settings) may be missing. This is a known limitation. See https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/29117"
        }
    
    return {
        "instance_id": instance_id,
        "effective_config_hash": effective_config_hash,
        "config_yaml": None,
        "message": "Effective config hash found but content not available"
    }


@router.post("/agents/{instance_id}/request-effective-config")
async def request_effective_config(
    instance_id: str,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Request agent to report effective configuration via OpAMP.
    
    Creates a tracking ID and sends a ServerToAgent message with ReportFullState flag
    to request the agent to include effective_config in its next AgentToServer message.
    For WebSocket connections, the message is sent immediately.
    """
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    # Check if agent supports ReportsEffectiveConfig capability
    from app.services.opamp_capabilities import AgentCapabilities
    agent_capabilities = gateway.opamp_agent_capabilities or 0
    if not (agent_capabilities & AgentCapabilities.REPORTS_EFFECTIVE_CONFIG):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent does not support ReportsEffectiveConfig capability"
        )
    
    # Check OpAMP connection status
    if gateway.opamp_connection_status != "connected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not connected (status: {gateway.opamp_connection_status})"
        )
    
    # Create tracking ID
    tracking_id = str(uuid.uuid4())
    
    # Create ConfigRequest record with proper error handling
    try:
        config_request = ConfigRequest(
            tracking_id=tracking_id,
            instance_id=instance_id,
            org_id=org_id,
            status=ConfigRequestStatus.PENDING
        )
        db.add(config_request)
        db.commit()
        db.refresh(config_request)
        logger.info(f"Created config request {tracking_id} for instance {instance_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create config request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create config request: {str(e)}"
        )
    
    # Try to send immediate message if WebSocket connection exists
    ws_manager = get_websocket_manager()
    if ws_manager.is_connected(instance_id):
        try:
            protocol_service = OpAMPProtocolService(db)
            # Build a ServerToAgent message with ReportFullState flag
            server_message = protocol_service.build_initial_server_message(instance_id)
            # Force ReportFullState flag (OR with existing flags to preserve them)
            from app.protobufs import opamp_pb2
            server_message.flags = server_message.flags | opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportFullState
            
            # Serialize and send
            message_bytes = protocol_service.serialize_server_message(server_message)
            sent = await ws_manager.send_message(instance_id, server_message, message_bytes)
            
            if sent:
                logger.info(f"Sent immediate config request message to instance {instance_id} via WebSocket")
                return {
                    "tracking_id": tracking_id,
                    "instance_id": instance_id,
                    "status": "requested",
                    "message": "Effective config request sent immediately via WebSocket. The agent will report effective config in response.",
                    "transport": "websocket"
                }
        except Exception as e:
            logger.warning(f"Failed to send immediate WebSocket message: {e}", exc_info=True)
            # Continue with passive approach - config request is already created
    
    # For HTTP connections or if WebSocket send failed, mark as pending
    # The request will be processed on next agent message exchange
    return {
        "tracking_id": tracking_id,
        "instance_id": instance_id,
        "status": "requested",
        "message": "Effective config request will be sent on next OpAMP message exchange. The agent will report effective config in response.",
        "transport": gateway.opamp_transport_type or "http"
    }


@router.post("/agents/{instance_id}/request-available-components")
async def request_available_components(
    instance_id: str,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Request agent to report available components via OpAMP.
    
    Sends a ServerToAgent message with ReportAvailableComponents flag
    to request the agent to include available_components in its next AgentToServer message.
    For WebSocket connections, the message is sent immediately.
    """
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    # Check if agent supports ReportsAvailableComponents capability
    from app.services.opamp_capabilities import AgentCapabilities
    agent_capabilities = gateway.opamp_agent_capabilities or 0
    if not (agent_capabilities & AgentCapabilities.REPORTS_AVAILABLE_COMPONENTS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent does not support ReportsAvailableComponents capability"
        )
    
    # Check OpAMP connection status
    if gateway.opamp_connection_status != "connected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not connected (status: {gateway.opamp_connection_status})"
        )
    
    # Try to send immediately via WebSocket if connected
    from app.services.websocket_manager import get_websocket_manager
    from app.services.opamp_protocol_service import OpAMPProtocolService
    
    ws_manager = get_websocket_manager()
    if ws_manager.is_connected(instance_id):
        try:
            protocol_service = OpAMPProtocolService(db)
            # Build a ServerToAgent message with ReportAvailableComponents flag
            server_message = opamp_pb2.ServerToAgent()
            
            # Set instance UID
            try:
                gateway_uuid = UUID(str(gateway.id))
                server_message.instance_uid = gateway_uuid.bytes
            except (ValueError, AttributeError):
                gateway_id_str = str(gateway.id)
                server_message.instance_uid = gateway_id_str.encode('utf-8')[:16].ljust(16, b'\x00')
            
            # Set capabilities
            server_capabilities = ServerCapabilities.get_all_capabilities()
            server_message.capabilities = server_capabilities
            
            # Set ReportAvailableComponents flag
            server_message.flags = opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportAvailableComponents
            
            # Serialize and send
            message_bytes = protocol_service.serialize_server_message(server_message)
            success = await ws_manager.send_message(instance_id, server_message, message_bytes)
            
            logger.info(f"Sent immediate available components request to instance {instance_id} via WebSocket")
            return {
                "instance_id": instance_id,
                "status": "requested",
                "message": "Available components request sent immediately via WebSocket. The agent will report available components in response.",
                "transport": "websocket"
            }
        except Exception as e:
            logger.warning(f"Failed to send immediate WebSocket message: {e}", exc_info=True)
            # Continue with passive approach
    
    # For HTTP connections or if WebSocket send failed, mark gateway to request on next message
    # We'll set a flag in gateway metadata to request on next message exchange
    metadata = gateway.extra_metadata or {}
    metadata["request_available_components"] = True
    gateway.extra_metadata = metadata
    db.commit()
    
    return {
        "instance_id": instance_id,
        "status": "requested",
        "message": "Available components request will be sent on next OpAMP message exchange. The agent will report available components in response.",
        "transport": gateway.opamp_transport_type or "http"
    }


@router.get("/agents/{instance_id}/config-requests/{tracking_id}")
async def get_config_request_status(
    instance_id: str,
    tracking_id: str,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get config request status by tracking ID"""
    config_request = db.query(ConfigRequest).filter(
        ConfigRequest.tracking_id == tracking_id,
        ConfigRequest.instance_id == instance_id,
        ConfigRequest.org_id == org_id
    ).first()
    
    if not config_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Config request with tracking_id {tracking_id} not found"
        )
    
    response = {
        "tracking_id": config_request.tracking_id,
        "instance_id": config_request.instance_id,
        "status": config_request.status.value,
        "requested_at": config_request.created_at.isoformat() if config_request.created_at else None,
        "completed_at": config_request.completed_at.isoformat() if config_request.completed_at else None,
    }
    
    if config_request.status == ConfigRequestStatus.COMPLETED:
        response["effective_config"] = {
            "config_yaml": config_request.effective_config_content,
            "config_hash": config_request.effective_config_hash,
        }
    elif config_request.status == ConfigRequestStatus.FAILED:
        response["error_message"] = config_request.error_message
    
    return response


class ConfigCompareRequest(BaseModel):
    """Request model for config comparison"""
    standard_config_id: str | None = None  # System template ID
    standard_config_yaml: str | None = None  # Custom YAML to compare against


@router.post("/agents/{instance_id}/compare-config")
async def compare_agent_config(
    instance_id: str,
    compare_request: ConfigCompareRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Compare agent's effective config with standard config"""
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    # Get agent's effective config
    agent_config = gateway.opamp_effective_config_content
    if not agent_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent effective config not available. Please request config first."
        )
    
    # Get standard config
    standard_config = None
    if compare_request.standard_config_yaml:
        standard_config = compare_request.standard_config_yaml
    elif compare_request.standard_config_id:
        # Get system template by ID
        from app.models.system_template import SystemTemplate
        template = db.query(SystemTemplate).filter(
            SystemTemplate.id == compare_request.standard_config_id
        ).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System template with id {compare_request.standard_config_id} not found"
            )
        standard_config = template.config_yaml
    else:
        # Use default system template
        from app.services.system_template_service import SystemTemplateService
        template_service = SystemTemplateService(db)
        template = template_service.get_default_template()
        if not template:
            # Try to initialize
            try:
                template = template_service.initialize_default_template()
            except FileNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Default system template not found and could not be initialized"
                )
        standard_config = template.config_yaml
    
    # Calculate diff
    from app.services.config_diff_service import ConfigDiffService
    diff_result = ConfigDiffService.compare_configs(agent_config, standard_config)
    
    return {
        "instance_id": instance_id,
        "diff": diff_result["unified_diff"],
        "agent_config": diff_result["agent_config"],
        "standard_config": diff_result["standard_config"],
        "diff_stats": diff_result["stats"],
        "line_diff": diff_result["line_diff"]
    }

