"""Permission model for RBAC"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import BaseModel


class Permission(Base, BaseModel):
    """Permission model for fine-grained access control"""

    __tablename__ = "permissions"

    name = Column(String(100), nullable=False, unique=True, index=True)
    resource_type = Column(String(100), nullable=False)  # e.g., "templates", "gateways", "deployments"
    action = Column(String(50), nullable=False)  # e.g., "read", "write", "delete", "manage"

    # Relationships
    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions"
    )

