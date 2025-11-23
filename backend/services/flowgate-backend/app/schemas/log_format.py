"""Log Format schemas"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List, Literal
from uuid import UUID
from datetime import datetime


class LogFormatTemplateResponse(BaseModel):
    """Schema for log format template response"""
    
    id: UUID
    format_name: str
    display_name: str
    format_type: Literal["source", "destination", "both"]
    description: Optional[str] = None
    sample_logs: Optional[str] = None
    parser_config: Optional[Dict[str, Any]] = None
    schema: Optional[Dict[str, Any]] = None
    is_system_template: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LogFormatTemplateListResponse(BaseModel):
    """Schema for list of log format templates"""
    
    templates: List[LogFormatTemplateResponse] = Field(..., description="List of format templates")
    total: int = Field(..., description="Total number of templates")


class LogTransformRequest(BaseModel):
    """Schema for log transformation request"""
    
    source_format: Optional[str] = Field(None, description="Source log format name (optional, for template-based parsing)")
    destination_format: Optional[str] = Field(None, description="Deprecated: Use target_json instead")
    sample_logs: str = Field(..., description="Sample log entries to transform")
    target_json: Optional[str] = Field(None, description="Target structured JSON format (optional - can be generated from ai_prompt)")
    ai_prompt: Optional[str] = Field(None, description="Natural language description of desired output structure (optional - used to generate target_json)")
    custom_source_parser: Optional[Dict[str, Any]] = Field(None, description="Custom source parser config")
    
    @model_validator(mode='after')
    def validate_target_or_prompt(self):
        """Ensure either target_json or ai_prompt is provided"""
        if not self.target_json and not self.ai_prompt:
            raise ValueError("Either target_json or ai_prompt must be provided")
        return self


class GenerateTargetJsonRequest(BaseModel):
    """Schema for generating target JSON from AI prompt"""
    
    source_format: Optional[str] = Field(None, description="Source log format name (optional)")
    sample_logs: str = Field(..., description="Sample log entries for context")
    ai_prompt: str = Field(..., description="Natural language description of desired output structure")


class GenerateTargetJsonResponse(BaseModel):
    """Schema for target JSON generation response"""
    
    success: bool = Field(..., description="Whether generation was successful")
    target_json: str = Field(..., description="Generated target JSON structure")
    errors: List[str] = Field(default_factory=list, description="Errors during generation")
    warnings: List[str] = Field(default_factory=list, description="Warnings during generation")


class LogTransformResponse(BaseModel):
    """Schema for log transformation response"""
    
    success: bool = Field(..., description="Whether transformation was successful")
    otel_config: str = Field(..., description="Generated OpenTelemetry transform processor config")
    warnings: List[str] = Field(default_factory=list, description="Warnings about the generated config")
    errors: List[str] = Field(default_factory=list, description="Errors in transformation")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations for improvement")


class FormatRecommendationRequest(BaseModel):
    """Schema for format recommendation request"""
    
    source_format: Optional[str] = Field(None, description="Source log format name")
    sample_logs: Optional[str] = Field(None, description="Sample log entries to analyze")
    use_case: Optional[str] = Field(None, description="Intended use case (e.g., 'monitoring', 'analytics', 'compliance')")


class FormatRecommendation(BaseModel):
    """Schema for a single format recommendation"""
    
    format_name: str = Field(..., description="Recommended format name")
    display_name: str = Field(..., description="Format display name")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    reasoning: str = Field(..., description="Reasoning for this recommendation")
    compatibility_score: Optional[float] = Field(None, description="Compatibility score with source format")


class FormatRecommendationResponse(BaseModel):
    """Schema for format recommendation response"""
    
    success: bool = Field(..., description="Whether recommendation was successful")
    recommendations: List[FormatRecommendation] = Field(..., description="List of recommended formats")
    message: Optional[str] = Field(None, description="Additional message or context")


class ConfigValidationRequest(BaseModel):
    """Schema for config validation request"""
    
    config: str = Field(..., description="OpenTelemetry config YAML to validate")
    sample_logs: Optional[str] = Field(None, description="Sample logs to test with")


class ConfigValidationResponse(BaseModel):
    """Schema for config validation response"""
    
    valid: bool = Field(..., description="Whether config is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class DryRunRequest(BaseModel):
    """Schema for dry run request"""
    
    config: str = Field(..., description="OpenTelemetry transform config")
    sample_logs: str = Field(..., description="Sample logs to transform")


class DryRunResponse(BaseModel):
    """Schema for dry run response"""
    
    success: bool = Field(..., description="Whether dry run was successful")
    transformed_logs: List[Dict[str, Any]] = Field(..., description="Transformed log entries")
    errors: List[str] = Field(default_factory=list, description="Errors during transformation")

