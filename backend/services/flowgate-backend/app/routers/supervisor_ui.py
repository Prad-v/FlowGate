"""OpAMP Supervisor UI Router

Endpoints matching example server UI functionality for supervisor management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.services.opamp_supervisor_service import OpAMPSupervisorService
from app.services.gateway_service import GatewayService
from app.services.opamp_config_service import OpAMPConfigService
from app.models.gateway import Gateway, ManagementMode
from app.utils.auth import get_current_user_org_id

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
    
    # Add supervisor-specific details if supervisor-managed
    if gateway.management_mode == ManagementMode.SUPERVISOR.value:
        supervisor_status = supervisor_service.get_supervisor_status(instance_id)
        agent_description = supervisor_service.get_agent_description(instance_id)
        
        if supervisor_status:
            agent_details["supervisor_status"] = supervisor_status.get("supervisor_status", {})
            # Extract agent_description from supervisor status if available
            supervisor_agent_desc = supervisor_status.get("supervisor_status", {}).get("agent_description", {})
            if supervisor_agent_desc:
                agent_details["agent_description"] = supervisor_agent_desc
                # Update version info from supervisor if available
                if not agent_details["agent_version"] and supervisor_agent_desc.get("identifying_attributes"):
                    attrs = supervisor_agent_desc.get("identifying_attributes", [])
                    for attr in attrs:
                        if isinstance(attr, dict) and attr.get("key") == "service.version":
                            agent_details["agent_version"] = {"version": attr.get("value")}
        
        if agent_description:
            desc = agent_description.get("agent_description", {})
            if desc:
                agent_details["agent_description"] = desc
                # Extract version from identifying attributes
                identifying_attrs = desc.get("identifying_attributes", [])
                for attr in identifying_attrs:
                    if isinstance(attr, dict):
                        key = attr.get("key", "")
                        value = attr.get("value", "")
                        if key == "service.version":
                            agent_details["agent_version"] = {"version": value}
                        elif key == "service.name":
                            agent_details["agent_name"] = value
    
    # Get effective config content by matching hash
    effective_config_hash = gateway.opamp_effective_config_hash
    effective_config_yaml = None
    effective_config_version = None
    effective_config_deployment_name = None
    
    if effective_config_hash:
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
        "config_yaml": effective_config_yaml,
        "config_version": effective_config_version,
        "deployment_name": effective_config_deployment_name,
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
    
    return agent_details


@router.post("/agents/{instance_id}/config", response_model=Dict[str, Any])
async def push_config_via_supervisor_ui(
    instance_id: str,
    config_request: ConfigPushRequest,
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
            created_by=None  # TODO: Get from auth context
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
    """Get effective config that agent is actually running."""
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    # Get effective config hash from gateway
    effective_config_hash = gateway.opamp_effective_config_hash
    
    if not effective_config_hash:
        return {
            "instance_id": instance_id,
            "effective_config_hash": None,
            "message": "No effective config hash reported by agent"
        }
    
    # Try to find the deployment with this hash
    from app.models.opamp_config_deployment import OpAMPConfigDeployment
    deployment = db.query(OpAMPConfigDeployment).filter(
        OpAMPConfigDeployment.config_hash == effective_config_hash
    ).first()
    
    if deployment:
        return {
            "instance_id": instance_id,
            "effective_config_hash": effective_config_hash,
            "config_version": deployment.config_version,
            "config_yaml": deployment.config_yaml,
            "deployment_name": deployment.name
        }
    
    return {
        "instance_id": instance_id,
        "effective_config_hash": effective_config_hash,
        "message": "Effective config hash found but deployment not found"
    }

