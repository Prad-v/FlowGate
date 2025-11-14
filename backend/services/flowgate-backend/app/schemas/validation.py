"""Validation schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ValidationRequest(BaseModel):
    """Schema for validation request"""

    config_yaml: str = Field(..., description="OTel collector config in YAML format")
    sample_data: Optional[Dict[str, Any]] = Field(
        None, description="Sample telemetry data for dry-run"
    )


class ValidationResponse(BaseModel):
    """Schema for validation response"""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    output_preview: Optional[Dict[str, Any]] = Field(
        None, description="Preview of transformed output"
    )
    message: Optional[str] = None

