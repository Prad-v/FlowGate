"""Gateway API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from services.gateway import GatewayService
from schemas.gateway import GatewayCreate, GatewayUpdate, GatewayResponse, GatewayHeartbeat

router = APIRouter(prefix="/gateways", tags=["gateways"])

# TODO: Add authentication middleware to extract org_id from JWT
DEFAULT_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=GatewayResponse, status_code=status.HTTP_201_CREATED)
async def register_gateway(
    gateway_data: GatewayCreate,
    db: Session = Depends(get_db)
):
    """Register a new gateway."""
    service = GatewayService(db)
    gateway = service.register_gateway(DEFAULT_ORG_ID, gateway_data)
    return gateway


@router.post("/{instance_id}/heartbeat", response_model=GatewayResponse)
async def update_heartbeat(
    instance_id: str,
    heartbeat: GatewayHeartbeat,
    db: Session = Depends(get_db)
):
    """Update gateway heartbeat."""
    service = GatewayService(db)
    gateway = service.update_heartbeat(instance_id, heartbeat, DEFAULT_ORG_ID)
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    return gateway


@router.get("", response_model=List[GatewayResponse])
async def list_gateways(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all gateways."""
    service = GatewayService(db)
    gateways = service.get_gateways(DEFAULT_ORG_ID, skip=skip, limit=limit)
    return gateways


@router.get("/{gateway_id}", response_model=GatewayResponse)
async def get_gateway(
    gateway_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a gateway by ID."""
    service = GatewayService(db)
    gateway = service.get_gateway(gateway_id, DEFAULT_ORG_ID)
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    return gateway


@router.put("/{gateway_id}", response_model=GatewayResponse)
async def update_gateway(
    gateway_id: UUID,
    gateway_data: GatewayUpdate,
    db: Session = Depends(get_db)
):
    """Update a gateway."""
    service = GatewayService(db)
    update_data = gateway_data.model_dump(exclude_unset=True)
    gateway = service.repo.update(gateway_id, DEFAULT_ORG_ID, **update_data)
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    return gateway


