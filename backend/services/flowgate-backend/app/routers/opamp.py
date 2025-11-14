"""OpAMP API router (simplified REST interface)"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.services.opamp_service import OpAMPService
from app.services.gateway_service import GatewayService
from app.utils.auth import get_opamp_token

router = APIRouter(prefix="/opamp", tags=["opamp"])


@router.get("/config/{instance_id}")
async def get_gateway_config(
    instance_id: str,
    token_info: dict = Depends(get_opamp_token),  # Validates OpAMP token
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get config for a gateway instance (OpAMP endpoint)
    
    Requires: Authorization: Bearer <opamp_token> header
    """
    # Verify instance_id matches token
    if token_info["instance_id"] != instance_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instance ID does not match token",
        )
    
    service = OpAMPService(db)
    config = service.get_config_for_gateway(instance_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active config found for this gateway",
        )
    return config


@router.post("/heartbeat/{instance_id}")
async def gateway_heartbeat(
    instance_id: str,
    config_version: int | None = None,
    token_info: dict = Depends(get_opamp_token),  # Validates OpAMP token
    db: Session = Depends(get_db),
):
    """
    Gateway heartbeat endpoint (OpAMP)
    
    Requires: Authorization: Bearer <opamp_token> header
    """
    # Verify instance_id matches token
    if token_info["instance_id"] != instance_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instance ID does not match token",
        )
    
    gateway_service = GatewayService(db)
    opamp_service = OpAMPService(db)

    # Update heartbeat
    gateway = gateway_service.update_heartbeat(instance_id)
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found",
        )

    # Update config version if provided
    if config_version is not None:
        opamp_service.update_gateway_config_version(instance_id, config_version)

    return {"status": "ok", "gateway_id": str(gateway.id)}

