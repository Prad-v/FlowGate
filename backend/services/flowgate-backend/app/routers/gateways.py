"""Gateway API router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
from app.schemas.opamp_config import AgentConfigHistoryEntry
from app.database import get_db
from app.services.gateway_service import GatewayService
from app.services.opamp_service import OpAMPService
from app.services.settings_service import SettingsService
from app.utils.auth import get_registration_token
from app.schemas.gateway import (
    GatewayCreate, GatewayUpdate, GatewayResponse, GatewayRegistrationResponse,
    AgentHealthResponse, AgentVersionResponse, AgentConfigResponse,
    AgentMetricsResponse, AgentStatusResponse
)
from app.config import settings

router = APIRouter(prefix="/gateways", tags=["gateways"])


@router.post("", response_model=GatewayRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_gateway(
    gateway_data: GatewayCreate,
    token_info: tuple = Depends(get_registration_token),  # Returns (org_id, token_id)
    db: Session = Depends(get_db),
):
    """
    Register a new gateway using a registration token
    
    Requires: Authorization: Bearer <registration_token> header
    """
    org_id, registration_token_id = token_info
    
    # Register the gateway
    service = GatewayService(db)
    gateway = service.register_gateway(gateway_data, org_id, registration_token_id)
    
    # Generate OpAMP token
    opamp_service = OpAMPService(db)
    opamp_token = opamp_service.generate_opamp_token(gateway.id, gateway.org_id)
    
    # Store OpAMP token in gateway
    gateway.opamp_token = opamp_token
    gateway = service.repository.update(gateway)
    
    # Build OpAMP endpoint URL
    opamp_endpoint = f"http://{settings.opamp_server_host}:{settings.opamp_server_port}/api/v1/opamp"
    
    # Get management mode from settings (default to supervisor)
    settings_service = SettingsService(db)
    management_mode = settings_service.get_gateway_management_mode(org_id)
    
    # Return registration response with OpAMP details
    # Convert gateway to dict, handling metadata properly
    response_dict = {
        "id": gateway.id,
        "name": gateway.name,
        "instance_id": gateway.instance_id,
        "org_id": gateway.org_id,
        "status": gateway.status,
        "last_seen": gateway.last_seen,
        "current_config_version": gateway.current_config_version,
        "metadata": gateway.extra_metadata if gateway.extra_metadata else {},
        "hostname": gateway.hostname,
        "ip_address": gateway.ip_address,
        "opamp_token": opamp_token,
        "opamp_endpoint": opamp_endpoint,
        "management_mode": management_mode,
        "created_at": gateway.created_at,
        "updated_at": gateway.updated_at,
    }
    
    return GatewayRegistrationResponse(**response_dict)


@router.post("/{gateway_id}/restart-registration", response_model=GatewayRegistrationResponse)
async def restart_registration(
    gateway_id: UUID,
    org_id: UUID,
    token_info: tuple = Depends(get_registration_token),  # Returns (org_id, token_id)
    db: Session = Depends(get_db),
):
    """
    Restart registration process for a gateway
    
    Allows restarting registration if it failed. Generates a new OPAMP_TOKEN
    and resets OpAMP connection status.
    
    Requires: Authorization: Bearer <registration_token> header
    """
    token_org_id, registration_token_id = token_info
    
    # Verify org_id matches
    if token_org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization ID does not match registration token"
        )
    
    service = GatewayService(db)
    gateway = service.get_gateway(gateway_id, org_id)
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    
    # Clear registration failure status
    service.clear_registration_failure(gateway.instance_id)
    
    # Generate new OpAMP token
    opamp_service = OpAMPService(db)
    opamp_token = opamp_service.generate_opamp_token(gateway.id, gateway.org_id)
    
    # Store new OpAMP token in gateway
    gateway.opamp_token = opamp_token
    gateway = service.repository.update(gateway)
    
    # Build OpAMP endpoint URL
    opamp_endpoint = f"http://{settings.opamp_server_host}:{settings.opamp_server_port}/api/v1/opamp"
    
    # Get management mode from settings (default to supervisor)
    settings_service = SettingsService(db)
    management_mode = settings_service.get_gateway_management_mode(org_id)
    
    # Return registration response with OpAMP details
    response_dict = {
        "id": gateway.id,
        "name": gateway.name,
        "instance_id": gateway.instance_id,
        "org_id": gateway.org_id,
        "status": gateway.status,
        "last_seen": gateway.last_seen,
        "current_config_version": gateway.current_config_version,
        "metadata": gateway.extra_metadata if gateway.extra_metadata else {},
        "hostname": gateway.hostname,
        "ip_address": gateway.ip_address,
        "opamp_token": opamp_token,
        "opamp_endpoint": opamp_endpoint,
        "management_mode": management_mode,
        "created_at": gateway.created_at,
        "updated_at": gateway.updated_at,
    }
    
    return GatewayRegistrationResponse(**response_dict)


@router.get("", response_model=List[GatewayResponse])
async def list_gateways(
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """List all gateways for an organization"""
    service = GatewayService(db)
    gateways = service.get_gateways(org_id)
    # Convert gateways to response format, handling extra_metadata -> metadata
    # Handle enum fields - they're already strings from the database
    result = []
    for gw in gateways:
        connection_status = gw.opamp_connection_status
        if connection_status and hasattr(connection_status, 'value'):
            connection_status = connection_status.value
        
        remote_config_status = gw.opamp_remote_config_status
        if remote_config_status and hasattr(remote_config_status, 'value'):
            remote_config_status = remote_config_status.value
        
        result.append(
            GatewayResponse(
                id=gw.id,
                name=gw.name,
                instance_id=gw.instance_id,
                org_id=gw.org_id,
                status=gw.status,
                last_seen=gw.last_seen,
                current_config_version=gw.current_config_version,
                metadata=gw.extra_metadata if gw.extra_metadata else None,
                hostname=gw.hostname,
                ip_address=gw.ip_address,
                opamp_token=gw.opamp_token,
                opamp_connection_status=connection_status,
                opamp_remote_config_status=remote_config_status,
                opamp_transport_type=gw.opamp_transport_type,
                management_mode=gw.management_mode,
                created_at=gw.created_at,
                updated_at=gw.updated_at,
            )
        )
    return result


@router.get("/active", response_model=List[GatewayResponse])
async def list_active_gateways(
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """List all active gateways"""
    service = GatewayService(db)
    gateways = service.get_active_gateways(org_id)
    return gateways


@router.get("/{gateway_id}", response_model=GatewayResponse)
async def get_gateway(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a gateway by ID"""
    service = GatewayService(db)
    gateway = service.get_gateway(gateway_id, org_id)
    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")
    return gateway


@router.put("/{gateway_id}", response_model=GatewayResponse)
async def update_gateway(
    gateway_id: UUID,
    org_id: UUID,
    update_data: GatewayUpdate,
    db: Session = Depends(get_db),
):
    """Update a gateway"""
    service = GatewayService(db)
    gateway = service.update_gateway(gateway_id, org_id, update_data)
    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")
    return gateway


@router.post("/heartbeat/{instance_id}", response_model=GatewayResponse)
async def update_heartbeat(
    instance_id: str,
    db: Session = Depends(get_db),
):
    """Update gateway heartbeat"""
    service = GatewayService(db)
    gateway = service.update_heartbeat(instance_id)
    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")
    return gateway


@router.delete("/{gateway_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gateway(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a gateway"""
    service = GatewayService(db)
    success = service.delete_gateway(gateway_id, org_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")


@router.get("/{gateway_id}/health", response_model=AgentHealthResponse)
async def get_agent_health(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get agent health status"""
    service = GatewayService(db)
    health = service.get_agent_health(gateway_id, org_id)
    if not health:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")
    return health


@router.get("/{gateway_id}/version", response_model=AgentVersionResponse)
async def get_agent_version(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get agent version information"""
    service = GatewayService(db)
    version = service.get_agent_version(gateway_id, org_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")
    return version


@router.get("/{gateway_id}/config", response_model=AgentConfigResponse)
async def get_agent_config(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get current agent configuration"""
    service = GatewayService(db)
    config = service.get_agent_config(gateway_id, org_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found or no active config"
        )
    return config


@router.get("/{gateway_id}/metrics", response_model=AgentMetricsResponse)
async def get_agent_metrics(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get agent performance metrics"""
    service = GatewayService(db)
    metrics = service.get_agent_metrics(gateway_id, org_id)
    if not metrics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")
    return metrics


@router.get("/{gateway_id}/config-history", response_model=List[AgentConfigHistoryEntry])
async def get_agent_config_history(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get config update history for an agent"""
    from app.services.opamp_config_service import OpAMPConfigService
    
    service = OpAMPConfigService(db)
    try:
        history = service.get_agent_config_history(gateway_id, org_id)
        return history
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{gateway_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get combined agent status (health, version, config, OpAMP status)"""
    service = GatewayService(db)
    gateway = service.get_gateway(gateway_id, org_id)
    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")
    
    health = service.get_agent_health(gateway_id, org_id)
    version = service.get_agent_version(gateway_id, org_id)
    config = service.get_agent_config(gateway_id, org_id)
    metrics = service.get_agent_metrics(gateway_id, org_id)
    opamp_status = service.get_opamp_status(gateway_id, org_id)
    
    response = {
        "gateway_id": gateway.id,
        "instance_id": gateway.instance_id,
        "name": gateway.name,
        "health": health,
        "version": version,
        "config": config,
        "metrics": metrics,
    }
    
    # Add OpAMP status fields if available
    if opamp_status:
        response.update(opamp_status)
    
    return response

