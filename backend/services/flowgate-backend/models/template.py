"""Template models."""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class Template(BaseModel):
    """Template model for OTel config templates."""
    __tablename__ = "templates"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False)  # 'metric', 'log', 'trace', 'routing'
    is_active = Column(Boolean, default=True, nullable=False)
    current_version = Column(Integer, default=1, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="templates")
    versions = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")


class TemplateVersion(BaseModel):
    """Template version model for version history."""
    __tablename__ = "template_versions"
    
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=False)
    version = Column(Integer, nullable=False)
    config_yaml = Column(Text, nullable=False)  # OTel collector config YAML
    config_json = Column(JSON, nullable=True)  # Parsed config as JSON
    change_summary = Column(Text, nullable=True)
    is_deployed = Column(Boolean, default=False, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    template = relationship("Template", back_populates="versions")
    
    __table_args__ = (
        {"comment": "Version history for templates with rollback support"}
    )
