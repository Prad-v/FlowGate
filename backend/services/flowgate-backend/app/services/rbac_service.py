"""RBAC service for role-based access control"""

import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole

logger = logging.getLogger(__name__)


class RBACService:
    """Service for role-based access control"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_roles(self, user_id: UUID, org_id: Optional[UUID] = None) -> List[Role]:
        """
        Get all roles for a user, optionally filtered by organization
        
        Args:
            user_id: User UUID
            org_id: Optional organization UUID (if None, returns roles for all orgs)
        
        Returns:
            List of Role objects
        """
        query = self.db.query(Role).join(UserRole).filter(UserRole.user_id == user_id)
        
        if org_id is not None:
            # Get roles for specific org or global roles (org_id is NULL)
            query = query.filter(
                or_(
                    UserRole.org_id == org_id,
                    UserRole.org_id.is_(None)  # Global roles (e.g., super admin)
                )
            )
        
        return query.all()

    def check_permission(
        self,
        user_id: UUID,
        org_id: Optional[UUID],
        resource_type: str,
        action: str
    ) -> bool:
        """
        Check if user has permission for a resource and action
        
        Args:
            user_id: User UUID
            org_id: Organization UUID (optional)
            resource_type: Resource type (e.g., "templates", "gateways")
            action: Action (e.g., "read", "write", "delete", "manage")
        
        Returns:
            True if user has permission, False otherwise
        """
        # Super admin has all permissions
        if self.is_super_admin(user_id):
            return True
        
        # Get user roles
        roles = self.get_user_roles(user_id, org_id)
        if not roles:
            return False
        
        # Get all permissions for user's roles
        role_ids = [role.id for role in roles]
        from app.models.role_permission import RolePermission
        
        permissions = self.db.query(Permission).join(
            RolePermission,
            Permission.id == RolePermission.permission_id
        ).filter(
            RolePermission.role_id.in_(role_ids)
        ).distinct().all()
        
        # Check for exact match or wildcard permission
        for perm in permissions:
            # Exact match
            if perm.resource_type == resource_type and perm.action == action:
                return True
            # Wildcard resource type
            if perm.resource_type == "*" and perm.action == action:
                return True
            # Wildcard action (manage grants all actions)
            if perm.resource_type == resource_type and perm.action == "manage":
                return True
            # Full wildcard
            if perm.resource_type == "*" and perm.action == "manage":
                return True
        
        return False

    def is_super_admin(self, user_id: UUID) -> bool:
        """
        Check if user is a super admin
        
        Args:
            user_id: User UUID
        
        Returns:
            True if user is super admin, False otherwise
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Check if user has super_admin role with org_id = NULL (global access)
        super_admin_role = self.db.query(Role).filter(Role.name == "super_admin").first()
        if not super_admin_role:
            return False
        
        user_role = self.db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == super_admin_role.id,
                UserRole.org_id.is_(None)  # Global super admin role
            )
        ).first()
        
        return user_role is not None

    def can_access_org(self, user_id: UUID, org_id: UUID) -> bool:
        """
        Check if user can access an organization
        
        Args:
            user_id: User UUID
            org_id: Organization UUID
        
        Returns:
            True if user can access org, False otherwise
        """
        # Super admin can access all orgs
        if self.is_super_admin(user_id):
            return True
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Check if user belongs to the org
        if user.org_id == org_id:
            return True
        
        # Check if user has a role in the org
        roles = self.get_user_roles(user_id, org_id)
        return len(roles) > 0

    def assign_role(self, user_id: UUID, role_id: UUID, org_id: Optional[UUID] = None) -> bool:
        """
        Assign a role to a user
        
        Args:
            user_id: User UUID
            role_id: Role UUID
            org_id: Optional organization UUID (None for global roles)
        
        Returns:
            True if role assigned successfully, False otherwise
        """
        # Check if assignment already exists
        existing = self.db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.org_id == org_id if org_id else UserRole.org_id.is_(None)
            )
        ).first()
        
        if existing:
            return True  # Already assigned
        
        # Create new assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            org_id=org_id
        )
        self.db.add(user_role)
        self.db.commit()
        
        return True

    def remove_role(self, user_id: UUID, role_id: UUID, org_id: Optional[UUID] = None) -> bool:
        """
        Remove a role from a user
        
        Args:
            user_id: User UUID
            role_id: Role UUID
            org_id: Optional organization UUID
        
        Returns:
            True if role removed successfully, False otherwise
        """
        user_role = self.db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.org_id == org_id if org_id else UserRole.org_id.is_(None)
            )
        ).first()
        
        if not user_role:
            return False
        
        self.db.delete(user_role)
        self.db.commit()
        
        return True

    def get_user_permissions(self, user_id: UUID, org_id: Optional[UUID] = None) -> List[Permission]:
        """
        Get all effective permissions for a user
        
        Args:
            user_id: User UUID
            org_id: Optional organization UUID
        
        Returns:
            List of Permission objects
        """
        # Super admin has all permissions
        if self.is_super_admin(user_id):
            return self.db.query(Permission).all()
        
        # Get user roles
        roles = self.get_user_roles(user_id, org_id)
        if not roles:
            return []
        
        # Get all permissions for user's roles
        role_ids = [role.id for role in roles]
        
        # Query permissions through role_permissions
        from app.models.role_permission import RolePermission
        
        permissions = self.db.query(Permission).join(
            RolePermission,
            Permission.id == RolePermission.permission_id
        ).filter(
            RolePermission.role_id.in_(role_ids)
        ).distinct().all()
        
        return permissions

