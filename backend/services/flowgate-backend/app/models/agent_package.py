"""Agent Package model for OpAMP package management"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models.base import BaseModel


class PackageStatus(str, enum.Enum):
    """Package status enumeration (per OpAMP spec)"""

    INSTALLED = "installed"
    INSTALLING = "installing"
    FAILED = "failed"
    UNINSTALLED = "uninstalled"


class PackageType(str, enum.Enum):
    """Package type enumeration (per OpAMP spec)"""

    TOP_LEVEL = "top_level"
    ADDON = "addon"


class AgentPackage(Base, BaseModel):
    """Model for agent packages installed via OpAMP"""

    __tablename__ = "agent_packages"

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
    package_name = Column(String(255), nullable=False)
    package_version = Column(String(100), nullable=True)
    package_type = Column(SQLEnum(PackageType, values_callable=lambda x: [e.value for e in x]), nullable=False, default=PackageType.TOP_LEVEL)
    package_hash = Column(String(256), nullable=True)  # Hash of package content
    status = Column(SQLEnum(PackageStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=PackageStatus.UNINSTALLED)
    installed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String(512), nullable=True)  # Error message if installation failed
    server_offered_hash = Column(String(256), nullable=True)  # Hash from server's PackagesAvailable
    agent_reported_hash = Column(String(256), nullable=True)  # Hash from agent's PackageStatuses
    
    # Package metadata
    download_url = Column(String(512), nullable=True)  # URL where package was downloaded from
    content_hash = Column(String(256), nullable=True)  # Content hash from DownloadableFile
    signature = Column(postgresql.BYTEA, nullable=True)  # Package signature for verification
    
    # Relationships
    gateway = relationship("Gateway", backref="packages")
    organization = relationship("Organization", backref="agent_packages")

