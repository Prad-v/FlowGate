"""OpAMP Protocol Router - Implements OpAMP protocol endpoints for collector compatibility"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.database import get_db
from app.services.opamp_service import OpAMPService
from app.services.gateway_service import GatewayService
from app.utils.auth import get_opamp_token
import json

router = APIRouter(prefix="/opamp/v1", tags=["opamp-protocol"])


@router.post("/opamp")
async def opamp_protocol(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    OpAMP protocol endpoint - handles OpAMP protocol messages
    
    The OpenTelemetry Collector OpAMP extension sends protocol buffer messages
    to this endpoint. We need to handle:
    - AgentConnect message (initial connection)
    - AgentToServer message (status updates, config requests)
    - Return ServerToAgent message (config updates, commands)
    
    For now, we'll implement a simplified REST-based approach that works with
    the collector's OpAMP extension expectations.
    """
    # Try to get OpAMP token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OpAMP token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate token
    opamp_service = OpAMPService(db)
    token_info = opamp_service.validate_opamp_token(token)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OpAMP token",
        )
    
    instance_id = token_info["instance_id"]
    
    # Get request body (OpAMP uses protobuf, but we'll handle JSON for now)
    try:
        body = await request.json()
    except:
        # If not JSON, might be protobuf - for now return basic response
        body = {}
    
    # Handle OpAMP protocol messages
    # For initial connection, return server capabilities and config if available
    gateway_service = GatewayService(db)
    gateway = gateway_service.repository.get_by_instance_id(instance_id)
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found",
        )
    
    # Update heartbeat
    gateway_service.update_heartbeat(instance_id)
    
    # Get config for gateway
    config = opamp_service.get_config_for_gateway(instance_id)
    
    # Build OpAMP response
    response_data = {
        "instance_uid": str(gateway.id),
        "capabilities": {
            "AcceptsRemoteConfig": True,
            "ReportsEffectiveConfig": True,
            "ReportsOwnTelemetry": True,
        },
    }
    
    # Include config if available
    if config:
        response_data["remote_config"] = {
            "config": {
                "yaml": config.get("config_yaml", ""),
            },
            "config_hash": f"v{config.get('version', 0)}",
        }
    
    return response_data


@router.get("/opamp")
async def opamp_get(
    request: Request,
    db: Session = Depends(get_db),
):
    """OpAMP GET endpoint for health/status checks"""
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OpAMP token required",
        )
    
    opamp_service = OpAMPService(db)
    token_info = opamp_service.validate_opamp_token(token)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OpAMP token",
        )
    
    return {"status": "ok", "instance_id": token_info["instance_id"]}

