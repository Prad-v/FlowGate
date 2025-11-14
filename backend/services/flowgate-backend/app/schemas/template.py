"""Template schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.template import TemplateType


class TemplateBase(BaseModel):
    """Base template schema"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: TemplateType


class TemplateCreate(TemplateBase):
    """Schema for creating a template"""

    org_id: UUID
    config_yaml: str = Field(..., description="OTel collector config in YAML format")


class TemplateUpdate(BaseModel):
    """Schema for updating a template"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    """Schema for template response"""

    id: UUID
    org_id: UUID
    is_active: bool
    current_version: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class TemplateVersionCreate(BaseModel):
    """Schema for creating a template version"""

    config_yaml: str = Field(..., description="OTel collector config in YAML format")
    description: Optional[str] = None


class TemplateVersionResponse(BaseModel):
    """Schema for template version response"""

    id: UUID
    template_id: UUID
    version: int
    config_yaml: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}

