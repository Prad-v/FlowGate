"""Common schemas."""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class HealthResponse(BaseModel):
    """Health check response."""
    status: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class BaseResponse(BaseModel):
    """Base response model."""
    id: UUID
    org_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


