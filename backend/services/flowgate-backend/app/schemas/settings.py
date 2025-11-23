"""Settings schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from uuid import UUID
from datetime import datetime


class AIProviderConfig(BaseModel):
    """Schema for AI provider configuration"""
    
    provider_type: Literal["litellm", "openai", "anthropic", "custom"] = Field(..., description="Type of LLM provider")
    provider_name: str = Field(..., description="Name/identifier for this provider configuration")
    api_key: Optional[str] = Field(None, description="API key (will be encrypted/masked)")
    endpoint: Optional[str] = Field(None, description="Endpoint URL (for litellm/custom providers)")
    model: Optional[str] = Field(None, description="Model name/identifier")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional provider-specific configuration")
    is_active: bool = Field(default=False, description="Whether this provider is currently active")


class SettingsResponse(BaseModel):
    """Schema for settings response"""

    id: UUID
    org_id: UUID
    gateway_management_mode: str = Field(..., description="Gateway management mode: supervisor or extension")
    ai_provider_config: Optional[Dict[str, Any]] = Field(None, description="AI provider configuration")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    """Schema for updating settings"""

    gateway_management_mode: Optional[str] = Field(None, description="Gateway management mode: supervisor or extension")


class AISettingsUpdate(BaseModel):
    """Schema for updating AI provider settings"""
    
    provider_config: AIProviderConfig = Field(..., description="AI provider configuration")


class AISettingsResponse(BaseModel):
    """Schema for AI settings response"""
    
    provider_config: Optional[AIProviderConfig] = Field(None, description="Current AI provider configuration")

