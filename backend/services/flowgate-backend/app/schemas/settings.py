"""Settings schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class SettingsResponse(BaseModel):
    """Schema for settings response"""

    id: UUID
    org_id: UUID
    gateway_management_mode: str = Field(..., description="Gateway management mode: supervisor or extension")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    """Schema for updating settings"""

    gateway_management_mode: str = Field(..., description="Gateway management mode: supervisor or extension")

