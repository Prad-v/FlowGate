"""RBAC router for role and permission management"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.services.rbac_service import RBACService
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.schemas.rbac import (
    RoleResponse,
    PermissionResponse,
    RoleWithPermissionsResponse,
    AssignRoleRequest,
    UserRoleResponse,
    UserPermissionsResponse,
)
from app.utils.auth import get_current_user, require_permission, require_super_admin, get_current_user_org_id
from app.models.user import User

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """
    List roles
    
    - Super admin: Returns all roles
    - Org admin: Returns org-scoped roles only
    
    Requires: rbac:read permission or super admin
    """
    rbac_service = RBACService(db)
    
    # Check permission
    if not rbac_service.is_super_admin(current_user.id):
        if not rbac_service.check_permission(current_user.id, org_id, "rbac", "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
    
    if rbac_service.is_super_admin(current_user.id):
        # Super admin sees all roles
        roles = db.query(Role).all()
    else:
        # Org admin sees org-scoped roles (non-system roles or roles assigned to their org)
        # Get roles that are either:
        # 1. System roles (is_system_role = true) - these are available to all orgs
        # 2. Roles assigned to users in this org
        from app.models.user_role import UserRole
        org_role_ids = db.query(UserRole.role_id).filter(
            UserRole.org_id == org_id
        ).distinct().all()
        org_role_ids = [r[0] for r in org_role_ids]
        
        # Get system roles and org-specific roles
        roles = db.query(Role).filter(
            (Role.is_system_role == True) | (Role.id.in_(org_role_ids))
        ).all()
    
    return [RoleResponse.model_validate(role) for role in roles]


@router.get("/roles/{role_id}", response_model=RoleWithPermissionsResponse)
async def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get role details with permissions
    
    Requires: rbac:read permission or super admin
    """
    rbac_service = RBACService(db)
    
    # Check permission
    if not rbac_service.is_super_admin(current_user.id):
        if not rbac_service.check_permission(current_user.id, current_user.org_id, "rbac", "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # Get permissions for this role
    from app.models.role_permission import RolePermission
    permissions = db.query(Permission).join(
        RolePermission,
        Permission.id == RolePermission.permission_id
    ).filter(RolePermission.role_id == role_id).all()
    
    role_data = RoleWithPermissionsResponse.model_validate(role)
    role_data.permissions = [PermissionResponse.model_validate(p) for p in permissions]
    
    return role_data


@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all permissions
    
    Requires: rbac:read permission or super admin
    """
    rbac_service = RBACService(db)
    
    # Check permission
    if not rbac_service.is_super_admin(current_user.id):
        if not rbac_service.check_permission(current_user.id, current_user.org_id, "rbac", "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
    
    permissions = db.query(Permission).all()
    return [PermissionResponse.model_validate(p) for p in permissions]


@router.get("/users/{user_id}/roles", response_model=List[UserRoleResponse])
async def get_user_roles(
    user_id: UUID,
    org_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get roles for a user
    
    Requires: users:read permission or super admin
    """
    rbac_service = RBACService(db)
    
    # Check permission
    if not rbac_service.is_super_admin(current_user.id):
        # Users can view their own roles, or need users:read permission
        if user_id != current_user.id:
            if not rbac_service.check_permission(current_user.id, current_user.org_id, "users", "read"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied",
                )
    
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    
    # Filter by org_id if provided
    if org_id is not None:
        user_roles = [ur for ur in user_roles if ur.org_id == org_id or ur.org_id is None]
    
    result = []
    for user_role in user_roles:
        role = db.query(Role).filter(Role.id == user_role.role_id).first()
        if role:
            role_data = RoleResponse.model_validate(role)
            user_role_data = UserRoleResponse.model_validate(user_role)
            user_role_data.role = role_data
            result.append(user_role_data)
    
    return result


@router.get("/users/{user_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: UUID,
    org_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get effective permissions for a user
    
    Requires: users:read permission or super admin
    """
    rbac_service = RBACService(db)
    
    # Check permission
    if not rbac_service.is_super_admin(current_user.id):
        # Users can view their own permissions, or need users:read permission
        if user_id != current_user.id:
            if not rbac_service.check_permission(current_user.id, current_user.org_id, "users", "read"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied",
                )
    
    # Use org_id from current user if not provided
    if org_id is None:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            org_id = user.org_id
    
    roles = rbac_service.get_user_roles(user_id, org_id)
    permissions = rbac_service.get_user_permissions(user_id, org_id)
    
    return UserPermissionsResponse(
        user_id=user_id,
        org_id=org_id,
        roles=[RoleResponse.model_validate(r) for r in roles],
        permissions=[PermissionResponse.model_validate(p) for p in permissions],
    )


@router.post("/users/{user_id}/roles", response_model=UserRoleResponse)
async def assign_role(
    user_id: UUID,
    role_data: AssignRoleRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("rbac", "write")),
):
    """
    Assign a role to a user
    
    - Super admin: Can assign roles to any user in any org
    - Org admin: Can only assign roles to users in their org
    
    Requires: rbac:write permission
    """
    rbac_service = RBACService(db)
    
    # Verify user exists and check org access
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Validate org access for non-super-admin
    if not rbac_service.is_super_admin(current_user.id):
        if user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign roles to users outside your organization",
            )
        # Org admin must assign roles with their org_id
        role_data.org_id = org_id
    
    # Verify role exists
    role = db.query(Role).filter(Role.id == role_data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # Assign role
    success = rbac_service.assign_role(user_id, role_data.role_id, role_data.org_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign role",
        )
    
    # Get the created user role
    user_role = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_data.role_id,
        UserRole.org_id == role_data.org_id if role_data.org_id else UserRole.org_id.is_(None)
    ).first()
    
    role_response = RoleResponse.model_validate(role)
    user_role_response = UserRoleResponse.model_validate(user_role)
    user_role_response.role = role_response
    
    return user_role_response


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    org_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    current_org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("rbac", "write")),
):
    """
    Remove a role from a user
    
    - Super admin: Can remove roles from any user in any org
    - Org admin: Can only remove roles from users in their org
    
    Requires: rbac:write permission
    """
    rbac_service = RBACService(db)
    
    # Verify user exists and check org access
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Validate org access for non-super-admin
    if not rbac_service.is_super_admin(current_user.id):
        if user.org_id != current_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove roles from users outside your organization",
            )
        # Org admin must use their org_id
        org_id = current_org_id
    
    # Verify the user role exists and belongs to the correct org
    user_role = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
        UserRole.org_id == org_id if org_id else UserRole.org_id.is_(None)
    ).first()
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role not found",
        )
    
    success = rbac_service.remove_role(user_id, role_id, org_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role not found",
        )
    
    return {"message": "Role removed successfully"}

