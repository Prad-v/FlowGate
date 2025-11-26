"""User Management API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.tenant import Organization
from app.schemas.auth import UserResponse
from app.schemas.user_management import UserCreate, UserUpdate, UserOrganizationAssign
from app.services.auth_service import AuthService
from app.utils.auth import get_current_user, require_super_admin, get_current_user_org_id, require_permission
from app.services.rbac_service import RBACService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("users", "read")),
):
    """
    List users
    
    - Super admin: Returns all users across all orgs
    - Org admin: Returns only users in their organization
    """
    rbac_service = RBACService(db)
    
    if rbac_service.is_super_admin(current_user.id):
        # Super admin can see all users
        users = db.query(User).all()
    else:
        # Org admin can only see users in their org
        users = db.query(User).filter(User.org_id == org_id).all()
    
    return [UserResponse.model_validate(user) for user in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("users", "write")),
):
    """
    Create a new user
    
    - Super admin: Can create users in any org (via org_id in request)
    - Org admin: Can only create users in their org (org_id is forced)
    """
    auth_service = AuthService(db)
    rbac_service = RBACService(db)
    
    # Enforce org_id for non-super-admin users
    if not rbac_service.is_super_admin(current_user.id):
        user_data.org_id = org_id
    
    # Check if email or username already exists
    existing_user = auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    existing_user = auth_service.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists"
        )
    
    # Validate organization if provided
    if user_data.org_id:
        org = db.query(Organization).filter(Organization.id == user_data.org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
    
    # Org admins cannot create superusers
    if not rbac_service.is_super_admin(current_user.id):
        user_data.is_superuser = False
    
    # Create user
    user = auth_service.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name,
        org_id=user_data.org_id,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser,
    )
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("users", "write")),
):
    """
    Update user
    
    - Super admin: Can update any user
    - Org admin: Can only update users in their org
    """
    rbac_service = RBACService(db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate org access for non-super-admin
    if not rbac_service.is_super_admin(current_user.id):
        if user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this user"
            )
        # Org admins cannot change org_id or is_superuser
        if user_data.org_id is not None and user_data.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change user's organization"
            )
        if user_data.is_superuser is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change superuser status"
            )
    
    # Update fields
    if user_data.email is not None:
        # Check if email is already taken by another user
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = user_data.email
    
    if user_data.username is not None:
        # Check if username is already taken by another user
        existing = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already in use"
            )
        user.username = user_data.username
    
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.org_id is not None:
        # Validate organization
        if user_data.org_id:
            org = db.query(Organization).filter(Organization.id == user_data.org_id).first()
            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
        user.org_id = user_data.org_id
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    if user_data.is_superuser is not None:
        user.is_superuser = user_data.is_superuser
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/{user_id}/organizations", status_code=status.HTTP_200_OK)
async def assign_user_to_organization(
    user_id: UUID,
    assignment: UserOrganizationAssign,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    Assign user to organization (super admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    org = db.query(Organization).filter(Organization.id == assignment.org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Assign user to organization
    user.org_id = assignment.org_id
    db.commit()
    db.refresh(user)
    
    return {"message": "User assigned to organization successfully", "user": UserResponse.model_validate(user)}


@router.delete("/{user_id}/organizations/{org_id}", status_code=status.HTTP_200_OK)
async def remove_user_from_organization(
    user_id: UUID,
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    Remove user from organization (super admin only)
    Note: This sets org_id to None. Super admin users can have org_id = None.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not assigned to this organization"
        )
    
    # Remove user from organization
    user.org_id = None
    db.commit()
    db.refresh(user)
    
    return {"message": "User removed from organization successfully"}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("users", "read")),
):
    """
    Get user by ID
    
    - Super admin: Can get any user
    - Org admin: Can only get users in their org
    """
    rbac_service = RBACService(db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate org access for non-super-admin
    if not rbac_service.is_super_admin(current_user.id):
        if user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this user"
            )
    
    return UserResponse.model_validate(user)

