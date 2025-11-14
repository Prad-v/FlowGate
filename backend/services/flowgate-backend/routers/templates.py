"""Template API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from services.template import TemplateService
from services.validation import ValidationService
from schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateVersionResponse,
    TemplateValidationRequest,
    TemplateValidationResponse
)

router = APIRouter(prefix="/templates", tags=["templates"])


# TODO: Add authentication middleware to extract org_id from JWT
# For now, using a placeholder org_id
DEFAULT_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new template."""
    service = TemplateService(db)
    try:
        template = service.create_template(DEFAULT_ORG_ID, template_data)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all templates."""
    service = TemplateService(db)
    templates = service.get_templates(DEFAULT_ORG_ID, skip=skip, limit=limit)
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a template by ID."""
    service = TemplateService(db)
    template = service.get_template(template_id, DEFAULT_ORG_ID)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a template."""
    service = TemplateService(db)
    try:
        template = service.update_template(template_id, DEFAULT_ORG_ID, template_data)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a template."""
    service = TemplateService(db)
    success = service.delete_template(template_id, DEFAULT_ORG_ID)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )


@router.get("/{template_id}/versions", response_model=List[TemplateVersionResponse])
async def list_template_versions(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """List all versions of a template."""
    service = TemplateService(db)
    versions = service.get_template_versions(template_id, DEFAULT_ORG_ID)
    return versions


@router.get("/{template_id}/versions/{version}", response_model=TemplateVersionResponse)
async def get_template_version(
    template_id: UUID,
    version: int,
    db: Session = Depends(get_db)
):
    """Get a specific template version."""
    service = TemplateService(db)
    template_version = service.get_template_version(template_id, version, DEFAULT_ORG_ID)
    if not template_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )
    return template_version


@router.post("/validate", response_model=TemplateValidationResponse)
async def validate_template(
    request: TemplateValidationRequest,
    db: Session = Depends(get_db)
):
    """Validate a template configuration."""
    service = ValidationService()
    return service.validate_config(request)


