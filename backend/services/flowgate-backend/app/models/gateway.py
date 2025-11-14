"""Gateway model"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models.base import BaseModel


class GatewayStatus(str, enum.Enum):
    """Gateway status enumeration"""

    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class Gateway(Base, BaseModel):
    """Gateway model for registered OTel Collector instances"""

    __tablename__ = "gateways"

    name = Column(String(255), nullable=False)
    instance_id = Column(String(255), nullable=False, unique=True, index=True)  # OpAMP instance ID
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    status = Column(SQLEnum(GatewayStatus), default=GatewayStatus.REGISTERED, nullable=False)
    last_seen = Column(DateTime(timezone=True))
    current_config_version = Column(Integer)
    extra_metadata = Column(JSONB)  # Additional gateway metadata (version, capabilities, etc.)
    hostname = Column(String(255))
    ip_address = Column(String(45))  # IPv6 compatible
    opamp_token = Column(String(512), nullable=True)  # JWT token for OpAMP authentication
    registration_token_id = Column(UUID(as_uuid=True), ForeignKey("registration_tokens.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="gateways")
    deployments = relationship("Deployment", back_populates="gateway")
    registration_token = relationship("RegistrationToken", foreign_keys=[registration_token_id])

