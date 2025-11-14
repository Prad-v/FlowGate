"""Template schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TemplateCreate(BaseModel):
    """Template creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: str = Field(..., pattern="^(metric|log|trace|routing)$")
    config_yaml: str = Field(..., min_length=1)
    change_summary: Optional[str] = None


class TemplateUpdate(BaseModel):
    """Template update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    config_yaml: Optional[str] = Field(None, min_length=1)
    change_summary: Optional[str] = None


class TemplateVersionResponse(BaseModel):
    """Template version response."""
    id: UUID
    template_id: UUID
    version: int
    change_summary: Optional[str]
    is_deployed: bool
    created_at: datetime
    created_by: Optional[UUID]
    
    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    """Template response."""
    id: UUID
    org_id: UUID
    name: str
    description: Optional[str]
    template_type: str
    is_active: bool
    current_version: int
    created_at: datetime
    updated_at: datetime
    versions: Optional[List[TemplateVersionResponse]] = None
    
    class Config:
        from_attributes = True


class TemplateValidationRequest(BaseModel):
    """Template validation request."""
    config_yaml: str = Field(..., min_length=1)
    sample_metrics: Optional[List[dict]] = None
    sample_logs: Optional[List[str]] = None


class TemplateValidationResponse(BaseModel):
    """Template validation response."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    preview_output: Optional[dict] = None
