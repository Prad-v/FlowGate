"""Audit log model"""

from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
from app.database import Base
from app.models.base import BaseModel


class AuditAction(str, enum.Enum):
    """Audit action enumeration"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    DEPLOY = "deploy"
    ROLLBACK = "rollback"
    VALIDATE = "validate"


class AuditLog(Base, BaseModel):
    """Audit log model for change tracking"""

    __tablename__ = "audit_logs"

    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(SQLEnum(AuditAction), nullable=False)
    resource_type = Column(String(50), nullable=False)  # template, deployment, gateway, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    changes = Column(JSONB)  # Before/after changes
    description = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))

