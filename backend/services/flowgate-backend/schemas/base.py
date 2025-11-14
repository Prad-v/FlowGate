from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: datetime
    updated_at: datetime


class OrgSchema(TimestampSchema):
    """Schema with organization ID and timestamps."""
    
    id: UUID
    org_id: UUID

