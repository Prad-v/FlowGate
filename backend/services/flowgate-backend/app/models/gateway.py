"""Gateway model"""

from sqlalchemy import Column, String, DateTime, Integer, BigInteger, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects import postgresql
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


class OpAMPConnectionStatus(str, enum.Enum):
    """OpAMP connection status enumeration"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    NEVER_CONNECTED = "never_connected"


class OpAMPRemoteConfigStatus(str, enum.Enum):
    """OpAMP remote config status enumeration (per OpAMP spec)"""

    UNSET = "UNSET"
    APPLIED = "APPLIED"
    APPLYING = "APPLYING"
    FAILED = "FAILED"


class Gateway(Base, BaseModel):
    """Gateway model for registered OTel Collector instances"""

    __tablename__ = "gateways"

    name = Column(String(255), nullable=False)
    instance_id = Column(String(255), nullable=False, unique=True, index=True)  # OpAMP instance ID
    org_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    status = Column(SQLEnum(GatewayStatus), default=GatewayStatus.REGISTERED, nullable=False)
    last_seen = Column(DateTime(timezone=True))
    current_config_version = Column(Integer)
    extra_metadata = Column(postgresql.JSONB)  # Additional gateway metadata (version, capabilities, etc.)
    hostname = Column(String(255))
    ip_address = Column(String(45))  # IPv6 compatible
    opamp_token = Column(String(512), nullable=True)  # JWT token for OpAMP authentication
    registration_token_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("registration_tokens.id"), nullable=True)
    
    # OpAMP status tracking fields
    opamp_connection_status = Column(
        postgresql.ENUM('connected', 'disconnected', 'failed', 'never_connected', name='opamp_connection_status', create_type=False),
        default='never_connected',
        nullable=True
    )
    opamp_remote_config_status = Column(
        postgresql.ENUM('UNSET', 'APPLIED', 'APPLYING', 'FAILED', name='opamp_remote_config_status', create_type=False),
        default='UNSET',
        nullable=True
    )
    opamp_last_sequence_num = Column(Integer, nullable=True)  # Last sequence number from agent
    opamp_transport_type = Column(String(20), nullable=True)  # websocket, http, none
    opamp_registration_failed_at = Column(DateTime(timezone=True), nullable=True)
    opamp_registration_failure_reason = Column(String(512), nullable=True)
    opamp_agent_capabilities = Column(BigInteger, nullable=True)  # Bit-field from agent
    opamp_server_capabilities = Column(BigInteger, nullable=True)  # Bit-field from server
    opamp_effective_config_hash = Column(String(256), nullable=True)  # Hash of effective config from agent
    opamp_remote_config_hash = Column(String(256), nullable=True)  # Hash of last remote config sent

    # Relationships
    organization = relationship("Organization", back_populates="gateways")
    deployments = relationship("Deployment", back_populates="gateway")
    registration_token = relationship("RegistrationToken", foreign_keys=[registration_token_id])

