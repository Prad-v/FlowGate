"""UserRole model for many-to-many relationship between users and roles"""

from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import BaseModel


class UserRole(Base, BaseModel):
    """UserRole model linking users to roles within organizations"""

    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    # org_id is nullable: null means the role applies to all orgs (for super admin)

    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    organization = relationship("Organization", back_populates="user_roles")

    # Composite unique constraint: a user can only have a role once per org (or once globally if org_id is null)
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'org_id', name='uq_user_role_org'),
    )

