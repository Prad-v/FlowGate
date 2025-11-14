"""Registration token model"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import BaseModel


class RegistrationToken(Base, BaseModel):
    """Registration token model for secure gateway registration"""

    __tablename__ = "registration_tokens"

    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)  # Hashed token
    name = Column(String(255), nullable=True)  # Optional description
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="registration_tokens")
    user = relationship("User", foreign_keys=[created_by])

