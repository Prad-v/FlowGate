"""Log Transformation Router

API endpoints for log format templates and AI-assisted log transformation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.utils.auth import get_current_user_org_id
from app.schemas.log_format import (
    LogFormatTemplateResponse,
    LogFormatTemplateListResponse,
    LogTransformRequest,
    LogTransformResponse,
    FormatRecommendation,
    FormatRecommendationRequest,
    FormatRecommendationResponse,
    ConfigValidationRequest,
    ConfigValidationResponse,
    DryRunRequest,
    DryRunResponse,
    GenerateTargetJsonRequest,
    GenerateTargetJsonResponse,
)
from app.services.log_transformation_service import LogTransformationService

router = APIRouter(prefix="/log-transformer", tags=["Log Transformation"])


@router.get("/formats", response_model=LogFormatTemplateListResponse)
async def list_formats(
    format_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all log format templates with optional filter"""
    service = LogTransformationService(db)
    templates = service.get_format_templates(format_type)
    
    template_responses = [
        LogFormatTemplateResponse(
            id=template.id,
            format_name=template.format_name,
            display_name=template.display_name,
            format_type=template.format_type.value,
            description=template.description,
            sample_logs=template.sample_logs,
            parser_config=template.parser_config,
            schema=template.schema,
            is_system_template=template.is_system_template,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
        for template in templates
    ]
    
    return LogFormatTemplateListResponse(templates=template_responses, total=len(template_responses))


@router.get("/formats/{format_name}", response_model=LogFormatTemplateResponse)
async def get_format(
    format_name: str,
    db: Session = Depends(get_db),
):
    """Get a single format template by name"""
    service = LogTransformationService(db)
    template = service.get_format_template(format_name)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Format template '{format_name}' not found"
        )
    
    # Handle enum conversion safely - SQLAlchemy returns the enum object
    try:
        format_type_value = template.format_type.value
    except (AttributeError, TypeError):
        format_type_value = str(template.format_type)
    
    return LogFormatTemplateResponse(
        id=template.id,
        format_name=template.format_name,
        display_name=template.display_name,
        format_type=format_type_value,
        description=template.description,
        sample_logs=template.sample_logs,
        parser_config=template.parser_config,
        schema=template.schema,
        is_system_template=template.is_system_template,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post("/generate-target", response_model=GenerateTargetJsonResponse)
async def generate_target_json(
    request: GenerateTargetJsonRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Generate target JSON structure from AI prompt"""
    service = LogTransformationService(db)
    
    result = service.generate_target_json(
        str(org_id),
        request.source_format,
        request.sample_logs,
        request.ai_prompt
    )
    
    return GenerateTargetJsonResponse(
        success=result["success"],
        target_json=result.get("target_json", ""),
        errors=result.get("errors", []),
        warnings=result.get("warnings", [])
    )


@router.post("/transform", response_model=LogTransformResponse)
async def transform_logs(
    request: LogTransformRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Transform logs and generate OTel config"""
    service = LogTransformationService(db)
    
    result = service.transform_logs(
        str(org_id),
        request.source_format,
        request.destination_format,
        request.sample_logs,
        request.target_json,
        request.ai_prompt,
        request.custom_source_parser
    )
    
    return LogTransformResponse(
        success=result["success"],
        otel_config=result["otel_config"],
        warnings=result["warnings"],
        errors=result["errors"],
        recommendations=result.get("recommendations", [])
    )


@router.post("/recommend", response_model=FormatRecommendationResponse)
async def get_recommendations(
    request: FormatRecommendationRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get AI recommendations for destination formats"""
    service = LogTransformationService(db)
    
    result = service.get_format_recommendations(
        str(org_id),
        request.source_format,
        request.sample_logs,
        request.use_case
    )
    
    # Convert recommendations to FormatRecommendation objects
    recommendations = [
        FormatRecommendation(**rec) for rec in result.get("recommendations", [])
    ]
    
    return FormatRecommendationResponse(
        success=result["success"],
        recommendations=recommendations,
        message=result.get("message")
    )


@router.post("/validate", response_model=ConfigValidationResponse)
async def validate_config(
    request: ConfigValidationRequest,
    db: Session = Depends(get_db),
):
    """Validate transformation config"""
    service = LogTransformationService(db)
    
    result = service._validate_transformation(request.config, request.sample_logs or "")
    
    return ConfigValidationResponse(
        valid=result["valid"],
        errors=result["errors"],
        warnings=result["warnings"]
    )


@router.post("/dry-run", response_model=DryRunResponse)
async def dry_run(
    request: DryRunRequest,
    db: Session = Depends(get_db),
):
    """Dry run transformation on sample logs"""
    service = LogTransformationService(db)
    
    try:
        transformed_logs, errors = service.dry_run_config(request.config, request.sample_logs)
        
        return DryRunResponse(
            success=len(errors) == 0,
            transformed_logs=transformed_logs,
            errors=errors
        )
    except Exception as e:
        return DryRunResponse(
            success=False,
            transformed_logs=[],
            errors=[str(e)]
        )

