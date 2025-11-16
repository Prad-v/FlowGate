"""Connection Settings model for OpAMP connection credential management"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models.base import BaseModel


class ConnectionSettingsType(str, enum.Enum):
    """Connection settings type enumeration"""

    OPAMP = "opamp"  # OpAMP connection settings
    OWN_METRICS = "own_metrics"  # Agent's own metrics destination
    OWN_TRACES = "own_traces"  # Agent's own traces destination
    OWN_LOGS = "own_logs"  # Agent's own logs destination
    OTHER = "other"  # Other connection settings


class ConnectionSettingsStatus(str, enum.Enum):
    """Connection settings status enumeration (per OpAMP spec)"""

    UNSET = "UNSET"
    APPLIED = "APPLIED"
    APPLYING = "APPLYING"
    FAILED = "FAILED"


class ConnectionSettings(Base, BaseModel):
    """Model for OpAMP connection settings (TLS, endpoints, etc.)"""

    __tablename__ = "connection_settings"

    gateway_id = Column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("gateways.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    org_id = Column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    settings_type = Column(SQLEnum(ConnectionSettingsType), nullable=False)
    settings_name = Column(String(255), nullable=True)  # For "other" connection settings
    settings_hash = Column(String(256), nullable=True)  # Hash of settings for verification
    status = Column(SQLEnum(ConnectionSettingsStatus), nullable=False, default=ConnectionSettingsStatus.UNSET)
    
    # Settings data stored as JSONB for flexibility
    settings_data = Column(postgresql.JSONB, nullable=True)  # Stores connection settings (endpoint, headers, TLS, proxy, etc.)
    
    # TLS certificate information (if applicable)
    certificate_pem = Column(postgresql.TEXT, nullable=True)  # PEM-encoded certificate
    private_key_pem = Column(postgresql.TEXT, nullable=True)  # PEM-encoded private key (encrypted)
    ca_cert_pem = Column(postgresql.TEXT, nullable=True)  # PEM-encoded CA certificate
    
    # Status tracking
    applied_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String(512), nullable=True)  # Error message if application failed
    
    # CSR (Certificate Signing Request) information
    csr_pem = Column(postgresql.TEXT, nullable=True)  # PEM-encoded CSR if agent requested certificate
    
    # Relationships
    gateway = relationship("Gateway", backref="connection_settings")
    organization = relationship("Organization", backref="connection_settings")

