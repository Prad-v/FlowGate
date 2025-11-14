"""Template API router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.services.template_service import TemplateService
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateVersionResponse,
    TemplateVersionCreate,
)
from app.schemas.validation import ValidationRequest, ValidationResponse
from app.services.validation_service import ValidationService

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a new template"""
    service = TemplateService(db)
    try:
        template = service.create_template(template_data)
        return template
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    org_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all templates for an organization"""
    service = TemplateService(db)
    templates = service.get_templates(org_id, skip, limit)
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a template by ID"""
    service = TemplateService(db)
    template = service.get_template(template_id, org_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    org_id: UUID,
    update_data: TemplateUpdate,
    db: Session = Depends(get_db),
):
    """Update a template"""
    service = TemplateService(db)
    template = service.update_template(template_id, org_id, update_data)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a template"""
    service = TemplateService(db)
    success = service.delete_template(template_id, org_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")


@router.post("/{template_id}/versions", response_model=TemplateVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_template_version(
    template_id: UUID,
    org_id: UUID,
    version_data: TemplateVersionCreate,
    db: Session = Depends(get_db),
):
    """Create a new template version"""
    service = TemplateService(db)
    try:
        version = service.create_version(template_id, org_id, version_data)
        if not version:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return version
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{template_id}/versions", response_model=List[TemplateVersionResponse])
async def list_template_versions(
    template_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """List all versions of a template"""
    service = TemplateService(db)
    versions = service.get_versions(template_id, org_id)
    return versions


@router.get("/{template_id}/versions/{version}", response_model=TemplateVersionResponse)
async def get_template_version(
    template_id: UUID,
    version: int,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a specific template version"""
    service = TemplateService(db)
    template_version = service.get_version(template_id, version, org_id)
    if not template_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template version not found")
    return template_version


@router.post("/{template_id}/rollback/{version}", response_model=TemplateVersionResponse)
async def rollback_template(
    template_id: UUID,
    version: int,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Rollback template to a specific version"""
    service = TemplateService(db)
    template_version = service.rollback_to_version(template_id, version, org_id)
    if not template_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template or version not found")
    return template_version


@router.post("/{template_id}/validate", response_model=ValidationResponse)
async def validate_template(
    template_id: UUID,
    org_id: UUID,
    validation_request: ValidationRequest,
    db: Session = Depends(get_db),
):
    """Validate a template configuration"""
    template_service = TemplateService(db)
    template = template_service.get_template(template_id, org_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    validation_service = ValidationService()
    return validation_service.validate_config(validation_request)

