"""Organization Management API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.tenant import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse
)
from app.utils.auth import get_current_user, require_super_admin
from app.models.user import User
import re

router = APIRouter(prefix="/organizations", tags=["organizations"])


def validate_slug(slug: str) -> bool:
    """Validate slug format (lowercase, alphanumeric, hyphens, underscores)"""
    return bool(re.match(r'^[a-z0-9_-]+$', slug))


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    List all organizations (super admin only)
    """
    organizations = db.query(Organization).all()
    return [OrganizationResponse.model_validate(org) for org in organizations]


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    Create a new organization (super admin only)
    """
    # Validate slug format
    if not validate_slug(org_data.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug must contain only lowercase letters, numbers, hyphens, and underscores"
        )
    
    # Check if name or slug already exists
    existing = db.query(Organization).filter(
        (Organization.name == org_data.name) | (Organization.slug == org_data.slug)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name or slug already exists"
        )
    
    # Create organization
    organization = Organization(
        name=org_data.name,
        slug=org_data.slug,
        is_active=org_data.is_active,
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)
    
    return OrganizationResponse.model_validate(organization)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    Get organization by ID (super admin only)
    """
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return OrganizationResponse.model_validate(organization)


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    Update organization (super admin only)
    """
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields
    if org_data.name is not None:
        # Check if name is already taken by another organization
        existing = db.query(Organization).filter(
            Organization.name == org_data.name,
            Organization.id != org_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already in use"
            )
        organization.name = org_data.name
    
    if org_data.slug is not None:
        # Validate slug format
        if not validate_slug(org_data.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug must contain only lowercase letters, numbers, hyphens, and underscores"
            )
        # Check if slug is already taken by another organization
        existing = db.query(Organization).filter(
            Organization.slug == org_data.slug,
            Organization.id != org_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug already in use"
            )
        organization.slug = org_data.slug
    
    if org_data.is_active is not None:
        organization.is_active = org_data.is_active
    
    db.commit()
    db.refresh(organization)
    
    return OrganizationResponse.model_validate(organization)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    Delete organization (super admin only)
    """
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if organization has users
    user_count = db.query(User).filter(User.org_id == org_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete organization with {user_count} users. Please reassign or remove users first."
        )
    
    db.delete(organization)
    db.commit()
    
    return None

