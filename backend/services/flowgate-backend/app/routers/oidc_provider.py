"""OIDC provider management router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.models.oidc_provider import OIDCProvider, OIDCProviderType
from app.services.oidc_service import OIDCService
from app.schemas.oidc_provider import (
    OIDCProviderCreate,
    OIDCProviderUpdate,
    OIDCProviderResponse,
)
from app.utils.auth import get_current_user, require_super_admin
from app.models.user import User

router = APIRouter(prefix="/oidc-providers", tags=["oidc-providers"])


@router.post("", response_model=OIDCProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_oidc_provider(
    provider_data: OIDCProviderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    Create a new OIDC provider
    
    Requires: Super admin access
    
    Direct integration providers: Okta, Azure AD, Google
    Proxy integration providers: OAuth proxy services
    """
    oidc_service = OIDCService(db)
    
    # Validate provider type
    try:
        provider_type = OIDCProviderType(provider_data.provider_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider type: {provider_data.provider_type}. Must be 'direct' or 'proxy'",
        )
    
    # Validate required fields based on provider type
    if provider_type == OIDCProviderType.DIRECT:
        if not provider_data.client_id or not provider_data.client_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_id and client_secret are required for direct integration",
            )
        if not provider_data.authorization_endpoint or not provider_data.token_endpoint:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="authorization_endpoint and token_endpoint are required for direct integration",
            )
    elif provider_type == OIDCProviderType.PROXY:
        if not provider_data.proxy_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="proxy_url is required for proxy integration",
            )
    
    # Encrypt client secret if provided
    client_secret_encrypted = None
    if provider_data.client_secret:
        client_secret_encrypted = oidc_service._encrypt_secret(provider_data.client_secret)
    
    # If this is set as default, unset other defaults
    if provider_data.is_default:
        db.query(OIDCProvider).filter(OIDCProvider.is_default == True).update({"is_default": False})
    
    # Create provider
    provider = OIDCProvider(
        name=provider_data.name,
        provider_type=provider_type,
        issuer_url=str(provider_data.issuer_url) if provider_data.issuer_url else None,
        client_id=provider_data.client_id,
        client_secret_encrypted=client_secret_encrypted,
        authorization_endpoint=str(provider_data.authorization_endpoint) if provider_data.authorization_endpoint else None,
        token_endpoint=str(provider_data.token_endpoint) if provider_data.token_endpoint else None,
        userinfo_endpoint=str(provider_data.userinfo_endpoint) if provider_data.userinfo_endpoint else None,
        proxy_url=str(provider_data.proxy_url) if provider_data.proxy_url else None,
        scopes=provider_data.scopes,
        org_id=provider_data.org_id,
        is_active=provider_data.is_active,
        is_default=provider_data.is_default,
    )
    
    db.add(provider)
    db.commit()
    db.refresh(provider)
    
    return OIDCProviderResponse.model_validate(provider)


@router.get("", response_model=List[OIDCProviderResponse])
async def list_oidc_providers(
    org_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List OIDC providers
    
    Returns system-wide providers and organization-specific providers.
    """
    query = db.query(OIDCProvider)
    
    if org_id:
        # Include system-wide (org_id is NULL) and org-specific providers
        query = query.filter(
            (OIDCProvider.org_id == org_id) | (OIDCProvider.org_id.is_(None))
        )
    else:
        # Only system-wide providers
        query = query.filter(OIDCProvider.org_id.is_(None))
    
    providers = query.all()
    return [OIDCProviderResponse.model_validate(p) for p in providers]


@router.get("/{provider_id}", response_model=OIDCProviderResponse)
async def get_oidc_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get OIDC provider details
    """
    provider = db.query(OIDCProvider).filter(OIDCProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OIDC provider not found",
        )
    
    return OIDCProviderResponse.model_validate(provider)


@router.put("/{provider_id}", response_model=OIDCProviderResponse)
async def update_oidc_provider(
    provider_id: UUID,
    provider_data: OIDCProviderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    Update OIDC provider
    
    Requires: Super admin access
    """
    provider = db.query(OIDCProvider).filter(OIDCProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OIDC provider not found",
        )
    
    oidc_service = OIDCService(db)
    
    # Update fields
    if provider_data.name is not None:
        provider.name = provider_data.name
    if provider_data.provider_type is not None:
        try:
            provider.provider_type = OIDCProviderType(provider_data.provider_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider type: {provider_data.provider_type}",
            )
    if provider_data.issuer_url is not None:
        provider.issuer_url = str(provider_data.issuer_url)
    if provider_data.client_id is not None:
        provider.client_id = provider_data.client_id
    if provider_data.client_secret is not None:
        provider.client_secret_encrypted = oidc_service._encrypt_secret(provider_data.client_secret)
    if provider_data.authorization_endpoint is not None:
        provider.authorization_endpoint = str(provider_data.authorization_endpoint)
    if provider_data.token_endpoint is not None:
        provider.token_endpoint = str(provider_data.token_endpoint)
    if provider_data.userinfo_endpoint is not None:
        provider.userinfo_endpoint = str(provider_data.userinfo_endpoint)
    if provider_data.proxy_url is not None:
        provider.proxy_url = str(provider_data.proxy_url)
    if provider_data.scopes is not None:
        provider.scopes = provider_data.scopes
    if provider_data.org_id is not None:
        provider.org_id = provider_data.org_id
    if provider_data.is_active is not None:
        provider.is_active = provider_data.is_active
    if provider_data.is_default is not None:
        if provider_data.is_default:
            # Unset other defaults
            db.query(OIDCProvider).filter(
                OIDCProvider.id != provider_id,
                OIDCProvider.is_default == True
            ).update({"is_default": False})
        provider.is_default = provider_data.is_default
    
    db.commit()
    db.refresh(provider)
    
    return OIDCProviderResponse.model_validate(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_oidc_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_super_admin()),
):
    """
    Delete OIDC provider
    
    Requires: Super admin access
    """
    provider = db.query(OIDCProvider).filter(OIDCProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OIDC provider not found",
        )
    
    db.delete(provider)
    db.commit()
    
    return None

