"""Template models"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models.base import BaseModel


class TemplateType(str, enum.Enum):
    """Template type enumeration"""

    METRICS = "metrics"
    LOGS = "logs"
    TRACES = "traces"
    ROUTING = "routing"
    COMPOSITE = "composite"


class Template(Base, BaseModel):
    """Template model for OTel config templates"""

    __tablename__ = "templates"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(SQLEnum(TemplateType), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    current_version = Column(Integer, default=1, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="templates")
    versions = relationship("TemplateVersion", back_populates="template", order_by="TemplateVersion.version")


class TemplateVersion(Base, BaseModel):
    """Template version model for version history"""

    __tablename__ = "template_versions"

    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    config_yaml = Column(Text, nullable=False)  # Raw YAML config
    config_json = Column(JSONB)  # Parsed JSON representation
    description = Column(Text)  # Version description/changelog
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    template = relationship("Template", back_populates="versions")

    __table_args__ = (
        {"comment": "Version history for templates with rollback support"},
    )

