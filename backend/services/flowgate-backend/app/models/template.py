"""Template models"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum, Boolean, UniqueConstraint, Index, text
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
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    current_version = Column(Integer, default=1, nullable=False)
    is_system_template = Column(Boolean, default=False, nullable=False, index=True)
    default_version_id = Column(UUID(as_uuid=True), ForeignKey("template_versions.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="templates")
    versions = relationship("TemplateVersion", back_populates="template", order_by="TemplateVersion.version", foreign_keys="[TemplateVersion.template_id]")
    default_version = relationship("TemplateVersion", foreign_keys=[default_version_id], remote_side="TemplateVersion.id", uselist=False, post_update=True, viewonly=True)

    __table_args__ = (
        # Unique constraint: (name, org_id) for org-scoped templates where org_id is not null
        UniqueConstraint('name', 'org_id', name='uq_template_name_org_id'),
        # Index for system template name lookups (partial index)
        Index('idx_template_system_name', 'name', postgresql_where=text('is_system_template = true')),
        {"comment": "Template model with version control and system template support"},
    )


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
    template = relationship("Template", back_populates="versions", foreign_keys=[template_id])

    __table_args__ = (
        # Unique constraint: (template_id, version) to ensure version immutability
        UniqueConstraint('template_id', 'version', name='uq_template_version'),
        # Index for efficient lookups
        Index('idx_template_version_lookup', 'template_id', 'version'),
        {"comment": "Version history for templates with rollback support"},
    )

