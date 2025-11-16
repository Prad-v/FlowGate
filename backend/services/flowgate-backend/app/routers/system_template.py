"""System template API router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import UUID

from app.database import get_db
from app.services.system_template_service import SystemTemplateService
from app.utils.auth import get_current_user_org_id
from pydantic import BaseModel

router = APIRouter(prefix="/system-templates", tags=["system-templates"])


class SystemTemplateUpdate(BaseModel):
    """Schema for updating system template"""
    config_yaml: str
    description: str | None = None


class SystemTemplateResponse(BaseModel):
    """Schema for system template response"""
    id: str
    name: str
    description: str | None
    config_yaml: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/default", response_model=SystemTemplateResponse)
async def get_default_system_template(
    db: Session = Depends(get_db),
):
    """Get the default system template"""
    service = SystemTemplateService(db)
    template = service.get_default_template()
    
    if not template:
        # Initialize from file if not exists
        try:
            template = service.initialize_default_template()
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Default template not found and could not be initialized: {str(e)}"
            )
    
    return SystemTemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        config_yaml=template.config_yaml,
        is_active=template.is_active,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else "",
    )


@router.put("/default", response_model=SystemTemplateResponse)
async def update_default_system_template(
    update_data: SystemTemplateUpdate,
    db: Session = Depends(get_db),
    # TODO: Add admin authentication check
):
    """Update the default system template (admin only)"""
    service = SystemTemplateService(db)
    
    try:
        template = service.update_default_template(
            config_yaml=update_data.config_yaml,
            description=update_data.description
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update system template: {str(e)}"
        )
    
    return SystemTemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        config_yaml=template.config_yaml,
        is_active=template.is_active,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else "",
    )

