"""System template model for default collector configurations"""

from sqlalchemy import Column, String, Text, Boolean
from app.database import Base
from app.models.base import BaseModel


class SystemTemplate(Base, BaseModel):
    """System template model for storing default collector config templates
    
    System templates are global (not org-scoped) and serve as baseline
    configurations for comparison with agent effective configs.
    """
    
    __tablename__ = "system_templates"
    
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    config_yaml = Column(Text, nullable=False)  # Raw YAML config content
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        {"comment": "System templates for default collector configurations"},
    )
    
    def __repr__(self):
        return f"<SystemTemplate(id={self.id}, name={self.name}, is_active={self.is_active})>"

