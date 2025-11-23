"""Settings model for organization-level settings"""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import BaseModel


class Settings(Base, BaseModel):
    """Settings model for organization-level configuration"""

    __tablename__ = "settings"

    org_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, unique=True, index=True)
    
    # Gateway management mode setting
    gateway_management_mode = Column(String(20), default="supervisor", nullable=False)  # "supervisor" or "extension"
    
    # AI provider configuration (JSONB for flexibility)
    ai_provider_config = Column(postgresql.JSONB, nullable=True)  # Stores LLM provider configurations
    
    # Relationships
    organization = relationship("Organization", backref="settings")

