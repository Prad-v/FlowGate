"""Settings API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any

from app.database import get_db
from app.services.settings_service import SettingsService
from app.schemas.settings import (
    SettingsResponse, SettingsUpdate,
    AISettingsUpdate, AISettingsResponse
)
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


@router.get("/ai", response_model=AISettingsResponse)
async def get_ai_settings(
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get AI provider configuration"""
    service = SettingsService(db)
    provider_config = service.get_ai_provider_config(org_id)
    return {"provider_config": provider_config}


@router.put("/ai", response_model=AISettingsResponse)
async def update_ai_settings(
    ai_settings_update: AISettingsUpdate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Update AI provider configuration"""
    service = SettingsService(db)
    
    try:
        # Convert Pydantic model to dict
        provider_config_dict = ai_settings_update.provider_config.model_dump()
        settings = service.update_ai_provider_config(org_id, provider_config_dict)
        return {"provider_config": settings.ai_provider_config}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/ai/test", response_model=Dict[str, Any])
async def test_ai_provider(
    ai_settings_update: AISettingsUpdate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Test AI provider connection"""
    service = SettingsService(db)
    
    # Convert Pydantic model to dict
    provider_config_dict = ai_settings_update.provider_config.model_dump()
    result = service.test_ai_provider_connection(org_id, provider_config_dict)
    return result


@router.post("/ai/models", response_model=Dict[str, Any])
async def get_available_models(
    ai_settings_update: AISettingsUpdate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get available models from AI provider"""
    service = SettingsService(db)
    
    # Convert Pydantic model to dict
    provider_config_dict = ai_settings_update.provider_config.model_dump()
    result = service.get_available_models(org_id, provider_config_dict)
    return result

