"""Config request model for tracking effective config retrieval requests"""

from sqlalchemy import Column, String, Text, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum
from app.database import Base
from app.models.base import BaseModel


class ConfigRequestStatus(str, enum.Enum):
    """Config request status enumeration"""
    
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ConfigRequest(Base, BaseModel):
    """Config request model for tracking effective config retrieval requests
    
    Tracks requests for agent effective configuration with unique tracking IDs.
    Used to provide status updates and retrieve configs by tracking ID.
    """
    
    __tablename__ = "config_requests"
    
    # Tracking ID (also stored as id, but this is the user-facing tracking ID)
    tracking_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID string format
    
    instance_id = Column(String(255), nullable=False, index=True)  # Gateway instance ID
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    status = Column(SQLEnum(ConfigRequestStatus), nullable=False, default=ConfigRequestStatus.PENDING, index=True)
    
    # Config data (populated when request is completed)
    effective_config_content = Column(Text, nullable=True)  # YAML content
    effective_config_hash = Column(String(255), nullable=True)  # Config hash
    
    # Error information (if request failed)
    error_message = Column(Text, nullable=True)
    
    # Timestamps (requested_at is created_at, completed_at is separate)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        {"comment": "Tracks effective config retrieval requests with tracking IDs"},
    )
    
    def __repr__(self):
        return f"<ConfigRequest(id={self.id}, tracking_id={self.tracking_id}, instance_id={self.instance_id}, status={self.status})>"

