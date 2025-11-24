"""RBAC schemas"""

from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class RoleResponse(BaseModel):
    """Role response schema"""
    id: UUID
    name: str
    description: Optional[str]
    is_system_role: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """Permission response schema"""
    id: UUID
    name: str
    resource_type: str
    action: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RoleWithPermissionsResponse(RoleResponse):
    """Role with permissions response schema"""
    permissions: List[PermissionResponse] = []


class AssignRoleRequest(BaseModel):
    """Assign role request schema"""
    role_id: UUID
    org_id: Optional[UUID] = None  # None for global roles (super admin)


class UserRoleResponse(BaseModel):
    """User role response schema"""
    id: UUID
    user_id: UUID
    role_id: UUID
    org_id: Optional[UUID]
    role: RoleResponse
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserPermissionsResponse(BaseModel):
    """User permissions response schema"""
    user_id: UUID
    org_id: Optional[UUID]
    roles: List[RoleResponse]
    permissions: List[PermissionResponse]

