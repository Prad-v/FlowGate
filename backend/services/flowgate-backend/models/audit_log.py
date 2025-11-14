"""Audit log model."""
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class AuditLog(BaseModel):
    """Audit log for tracking changes."""
    __tablename__ = "audit_logs"
    
    action = Column(String(100), nullable=False)  # 'create', 'update', 'delete', 'deploy', 'rollback'
    resource_type = Column(String(50), nullable=False)  # 'template', 'deployment', 'gateway'
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    changes = Column(JSON, nullable=True)  # Before/after changes
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(Text, nullable=True)  # Additional details
