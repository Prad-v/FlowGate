"""Template API router"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import yaml
from app.database import get_db
from app.services.template_service import TemplateService
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateVersionResponse,
    TemplateVersionCreate,
    SetDefaultVersionRequest,
    CreateFromGatewayRequest,
)
from app.schemas.validation import ValidationRequest, ValidationResponse
from app.services.validation_service import ValidationService
from app.utils.auth import get_current_user_org_id

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
    org_id: UUID = Depends(get_current_user_org_id),
    skip: int = 0,
    limit: int = 100,
    is_system_template: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """List all templates for an organization or system templates
    
    Args:
        org_id: Organization ID (from auth)
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_system_template: Filter by system template flag (None = both org and system)
    """
    service = TemplateService(db)
    templates = service.get_templates(org_id, skip, limit, is_system_template)
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
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
    update_data: TemplateUpdate,
    org_id: UUID = Depends(get_current_user_org_id),
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
    org_id: UUID = Depends(get_current_user_org_id),
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
    version_data: TemplateVersionCreate,
    org_id: UUID = Depends(get_current_user_org_id),
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
    org_id: UUID = Depends(get_current_user_org_id),
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
    org_id: UUID = Depends(get_current_user_org_id),
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
    org_id: UUID = Depends(get_current_user_org_id),
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
    org_id: UUID = Depends(get_current_user_org_id),
    validation_request: ValidationRequest = None,
    db: Session = Depends(get_db),
):
    """Validate a template configuration"""
    template_service = TemplateService(db)
    template = template_service.get_template(template_id, org_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    validation_service = ValidationService()
    return validation_service.validate_config(validation_request)


@router.put("/{template_id}/default-version", response_model=TemplateResponse)
async def set_default_version(
    template_id: UUID,
    request: SetDefaultVersionRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Set a specific version as the default version for a template"""
    service = TemplateService(db)
    try:
        template = service.set_default_version(template_id, request.version, org_id)
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


@router.post("/from-gateway", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template_from_gateway(
    request: CreateFromGatewayRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Create a new template from a gateway's effective configuration"""
    service = TemplateService(db)
    
    # Load config from gateway
    config_yaml = service.load_config_from_gateway(request.gateway_id, org_id)
    if not config_yaml:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No effective configuration available for the specified gateway"
        )
    
    # Create template
    template_data = TemplateCreate(
        name=request.name,
        description=request.description,
        template_type=request.template_type,
        org_id=None if request.is_system_template else org_id,
        config_yaml=config_yaml,
        is_system_template=request.is_system_template,
    )
    
    try:
        template = service.create_template(template_data)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/upload", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def upload_template(
    file: UploadFile = File(..., description="YAML file to upload"),
    name: str = Form(..., description="Template name"),
    description: Optional[str] = Form(None, description="Template description"),
    template_type: str = Form("composite", description="Template type"),
    is_system_template: bool = Form(False, description="Whether this is a system template"),
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Upload a template from a YAML file"""
    # Validate file extension
    if not (file.filename.endswith('.yaml') or file.filename.endswith('.yml')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a YAML file (.yaml or .yml)"
        )
    
    # Read file content
    try:
        content = await file.read()
        config_yaml = content.decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )
    
    # Validate YAML syntax
    try:
        yaml.safe_load(config_yaml)
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid YAML syntax: {str(e)}"
        )
    
    # Validate template type
    from app.models.template import TemplateType
    try:
        template_type_enum = TemplateType(template_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template type: {template_type}"
        )
    
    # Create template
    service = TemplateService(db)
    template_data = TemplateCreate(
        name=name,
        description=description,
        template_type=template_type_enum,
        org_id=None if is_system_template else org_id,
        config_yaml=config_yaml,
        is_system_template=is_system_template,
    )
    
    try:
        template = service.create_template(template_data)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

