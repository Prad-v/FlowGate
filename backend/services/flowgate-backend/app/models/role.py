"""Role model for RBAC"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.base import BaseModel


class Role(Base, BaseModel):
    """Role model for role-based access control"""

    __tablename__ = "roles"

    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(500))
    is_system_role = Column(Boolean, default=False, nullable=False)

    # Relationships
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles"
    )
    user_roles = relationship("UserRole", back_populates="role")

