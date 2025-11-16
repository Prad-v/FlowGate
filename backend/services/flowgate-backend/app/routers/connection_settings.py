"""Connection Settings API router for OpAMP connection credential management"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.services.connection_settings_service import ConnectionSettingsService
from app.services.gateway_service import GatewayService
from app.schemas.connection_settings import (
    ConnectionSettingsCreate, ConnectionSettingsUpdate,
    ConnectionSettingsResponse, ConnectionSettingsStatusUpdate, CSRRequest
)
from app.utils.auth import get_current_user_org_id
from app.models.connection_settings import ConnectionSettingsType

router = APIRouter(prefix="/connection-settings", tags=["connection-settings"])


@router.post("/gateways/{gateway_id}", response_model=ConnectionSettingsResponse, status_code=status.HTTP_201_CREATED)
async def create_connection_setting(
    gateway_id: UUID,
    settings_data: ConnectionSettingsCreate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Create connection settings for a gateway"""
    # Verify gateway belongs to org
    gateway_service = GatewayService(db)
    gateway = gateway_service.repository.get_by_id(gateway_id)
    
    if not gateway or gateway.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    
    # Create connection settings
    connection_settings_service = ConnectionSettingsService(db)
    setting = connection_settings_service.create_connection_setting(
        gateway_id=gateway_id,
        org_id=org_id,
        settings_type=settings_data.settings_type,
        settings_data=settings_data.settings_data,
        settings_name=settings_data.settings_name,
        certificate_pem=settings_data.certificate_pem,
        private_key_pem=settings_data.private_key_pem,
        ca_cert_pem=settings_data.ca_cert_pem,
    )
    
    return setting


@router.get("/gateways/{gateway_id}", response_model=List[ConnectionSettingsResponse])
async def get_connection_settings_for_gateway(
    gateway_id: UUID,
    settings_type: ConnectionSettingsType | None = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get connection settings for a gateway"""
    # Verify gateway belongs to org
    gateway_service = GatewayService(db)
    gateway = gateway_service.repository.get_by_id(gateway_id)
    
    if not gateway or gateway.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    
    connection_settings_service = ConnectionSettingsService(db)
    settings = connection_settings_service.get_connection_settings_for_gateway(
        gateway_id, org_id, settings_type
    )
    
    return settings


@router.get("/{setting_id}", response_model=ConnectionSettingsResponse)
async def get_connection_setting(
    setting_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get a connection setting by ID"""
    connection_settings_service = ConnectionSettingsService(db)
    setting = connection_settings_service.get_connection_setting(setting_id, org_id)
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection setting not found"
        )
    
    return setting


@router.put("/{setting_id}", response_model=ConnectionSettingsResponse)
async def update_connection_setting(
    setting_id: UUID,
    settings_data: ConnectionSettingsUpdate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Update connection settings"""
    connection_settings_service = ConnectionSettingsService(db)
    setting = connection_settings_service.get_connection_setting(setting_id, org_id)
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection setting not found"
        )
    
    # Update settings fields
    if settings_data.settings_data is not None:
        setting.settings_data = settings_data.settings_data
    if settings_data.certificate_pem is not None:
        setting.certificate_pem = settings_data.certificate_pem
    if settings_data.private_key_pem is not None:
        setting.private_key_pem = settings_data.private_key_pem
    if settings_data.ca_cert_pem is not None:
        setting.ca_cert_pem = settings_data.ca_cert_pem
    
    # Recalculate settings hash
    setting.settings_hash = connection_settings_service._calculate_settings_hash(
        setting.settings_data or {},
        setting.certificate_pem
    )
    
    db.commit()
    db.refresh(setting)
    
    return setting


@router.post("/gateways/{gateway_id}/csr", response_model=ConnectionSettingsResponse, status_code=status.HTTP_201_CREATED)
async def handle_csr_request(
    gateway_id: UUID,
    csr_request: CSRRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Handle Certificate Signing Request from agent"""
    # Verify gateway belongs to org
    gateway_service = GatewayService(db)
    gateway = gateway_service.repository.get_by_id(gateway_id)
    
    if not gateway or gateway.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    
    connection_settings_service = ConnectionSettingsService(db)
    setting = connection_settings_service.handle_csr_request(
        gateway_id=gateway_id,
        org_id=org_id,
        csr_pem=csr_request.csr_pem
    )
    
    return setting


@router.delete("/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection_setting(
    setting_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Delete connection settings"""
    connection_settings_service = ConnectionSettingsService(db)
    setting = connection_settings_service.get_connection_setting(setting_id, org_id)
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection setting not found"
        )
    
    db.delete(setting)
    db.commit()
    
    return None

