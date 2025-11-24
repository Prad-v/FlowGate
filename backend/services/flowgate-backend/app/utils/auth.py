"""Authentication utilities"""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.registration_token_service import RegistrationTokenService
from app.services.opamp_service import OpAMPService
from app.services.auth_service import AuthService
from app.services.session_service import get_session_service
from app.services.rbac_service import RBACService
from app.core.security import verify_token
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.user import User

security = HTTPBearer(auto_error=False)  # Don't auto-raise on missing token
session_cookie_name = "flowgate_session"


def get_registration_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> tuple[UUID, UUID]:  # Returns (org_id, token_id)
    """
    Validate registration token from Authorization header
    
    Returns:
        Tuple of (org_id, token_id) if valid
    """
    token = credentials.credentials
    service = RegistrationTokenService(db)
    result = service.validate_token(token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired registration token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    org_id, token_id = result
    return org_id, token_id


def get_opamp_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """
    Validate OpAMP token from Authorization header
    
    Returns:
        Dict with gateway_id, org_id, instance_id if valid
    """
    token = credentials.credentials
    service = OpAMPService(db)
    result = service.validate_opamp_token(token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OpAMP token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session_id: Optional[str] = Cookie(None, alias=session_cookie_name),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token or session cookie
    
    Supports both:
    - JWT token in Authorization header (for API access)
    - Session cookie (for web UI)
    
    Returns:
        User object if authenticated
    
    Raises:
        HTTPException 401 if not authenticated
    """
    auth_service = AuthService(db)
    session_service = get_session_service()
    
    # Try JWT token first
    if credentials:
        token = credentials.credentials
        payload = verify_token(token)
        if payload:
            user_id = UUID(payload.get("user_id") or payload.get("sub"))
            user = auth_service.get_user_by_id(user_id)
            if user and user.is_active:
                return user
    
    # Try session cookie
    if session_id:
        session_data = session_service.get_session(session_id)
        if session_data:
            user_id = UUID(session_data.get("user_id"))
            user = auth_service.get_user_by_id(user_id)
            if user and user.is_active:
                # Refresh session
                session_service.refresh_session(session_id)
                return user
    
    # Not authenticated
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_org_id(
    current_user: User = Depends(get_current_user),
    org_id: Optional[UUID] = None,  # From query param for super admin
    db: Session = Depends(get_db),
) -> UUID:
    """
    Get current user's organization ID.
    
    For super admin, can accept org_id from query parameter.
    For regular users, uses their assigned org_id.
    
    Returns:
        Organization UUID
    """
    rbac_service = RBACService(db)
    
    # Super admin can access any org via query param
    if rbac_service.is_super_admin(current_user.id) and org_id:
        return org_id
    
    # Regular users use their assigned org
    if current_user.org_id:
        return current_user.org_id
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User has no organization assigned",
    )


def require_permission(resource_type: str, action: str):
    """
    Dependency factory to require a specific permission
    
    Usage:
        @router.get("/templates")
        async def list_templates(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_permission("templates", "read"))
        ):
            ...
    """
    def permission_check(
        current_user: User = Depends(get_current_user),
        org_id: UUID = Depends(get_current_user_org_id),
        db: Session = Depends(get_db),
    ) -> None:
        rbac_service = RBACService(db)
        if not rbac_service.check_permission(current_user.id, org_id, resource_type, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource_type}:{action}",
            )
    
    return permission_check


def require_role(role_name: str):
    """
    Dependency factory to require a specific role
    
    Usage:
        @router.post("/admin/settings")
        async def update_settings(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_role("org_admin"))
        ):
            ...
    """
    def role_check(
        current_user: User = Depends(get_current_user),
        org_id: UUID = Depends(get_current_user_org_id),
        db: Session = Depends(get_db),
    ) -> None:
        rbac_service = RBACService(db)
        roles = rbac_service.get_user_roles(current_user.id, org_id)
        role_names = [role.name for role in roles]
        
        if role_name not in role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role_name}",
            )
    
    return role_check


def require_super_admin():
    """
    Dependency to require super admin role
    
    Usage:
        @router.post("/system/settings")
        async def update_system_settings(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_super_admin())
        ):
            ...
    """
    def super_admin_check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        rbac_service = RBACService(db)
        if not rbac_service.is_super_admin(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required",
            )
    
    return super_admin_check


def require_org_access(target_org_id: UUID):
    """
    Dependency factory to require access to a specific organization
    
    Usage:
        @router.get("/orgs/{org_id}/data")
        async def get_org_data(
            org_id: UUID,
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_org_access(org_id))
        ):
            ...
    """
    def org_access_check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        rbac_service = RBACService(db)
        if not rbac_service.can_access_org(current_user.id, target_org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization",
            )
    
    return org_access_check

