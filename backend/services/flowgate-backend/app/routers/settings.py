"""Settings API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict

from app.database import get_db
from app.services.settings_service import SettingsService
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.utils.auth import get_current_user_org_id

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get settings for the current organization"""
    service = SettingsService(db)
    settings = service.get_settings(org_id)
    return settings


@router.put("", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Update settings for the current organization"""
    service = SettingsService(db)
    
    try:
        settings = service.update_gateway_management_mode(
            org_id,
            settings_update.gateway_management_mode
        )
        return settings
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/gateway-management-mode", response_model=Dict[str, str])
async def get_gateway_management_mode(
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get gateway management mode setting"""
    service = SettingsService(db)
    mode = service.get_gateway_management_mode(org_id)
    return {"gateway_management_mode": mode}

