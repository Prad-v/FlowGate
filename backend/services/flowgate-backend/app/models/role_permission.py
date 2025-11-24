"""RolePermission association table for many-to-many relationship"""

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class RolePermission(Base):
    """Association table for role-permission many-to-many relationship"""

    __tablename__ = "role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

