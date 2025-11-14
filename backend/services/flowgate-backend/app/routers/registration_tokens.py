"""Registration token API router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.services.registration_token_service import RegistrationTokenService
from app.schemas.registration_token import (
    RegistrationTokenCreate,
    RegistrationTokenResponse,
    RegistrationTokenCreateResponse,
    RegistrationTokenListResponse,
)

router = APIRouter(prefix="/registration-tokens", tags=["registration-tokens"])


@router.post("", response_model=RegistrationTokenCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_registration_token(
    token_data: RegistrationTokenCreate,
    org_id: UUID,  # TODO: Extract from JWT token in production
    db: Session = Depends(get_db),
):
    """
    Generate a new registration token for an organization
    
    Note: In production, org_id should be extracted from authenticated user's JWT token
    """
    service = RegistrationTokenService(db)
    plain_token, token_model = service.generate_token(
        org_id=org_id,
        name=token_data.name,
        expires_in_days=token_data.expires_in_days,
        created_by=None,  # TODO: Extract from JWT token in production
    )
    
    return RegistrationTokenCreateResponse(
        token=plain_token,
        token_info=RegistrationTokenResponse.model_validate(token_model),
    )


@router.get("", response_model=RegistrationTokenListResponse)
async def list_registration_tokens(
    org_id: UUID,  # TODO: Extract from JWT token in production
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    """List all registration tokens for an organization"""
    service = RegistrationTokenService(db)
    tokens = service.list_tokens(org_id, include_inactive=include_inactive)
    
    return RegistrationTokenListResponse(
        tokens=[RegistrationTokenResponse.model_validate(token) for token in tokens],
        total=len(tokens),
    )


@router.get("/{token_id}", response_model=RegistrationTokenResponse)
async def get_registration_token(
    token_id: UUID,
    org_id: UUID,  # TODO: Extract from JWT token in production
    db: Session = Depends(get_db),
):
    """Get a specific registration token"""
    service = RegistrationTokenService(db)
    token = service.get_token(token_id, org_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration token not found",
        )
    return RegistrationTokenResponse.model_validate(token)


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_registration_token(
    token_id: UUID,
    org_id: UUID,  # TODO: Extract from JWT token in production
    db: Session = Depends(get_db),
):
    """Revoke (deactivate) a registration token"""
    service = RegistrationTokenService(db)
    success = service.revoke_token(token_id, org_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration token not found",
        )


@router.post("/{token_id}/revoke", status_code=status.HTTP_200_OK)
async def revoke_registration_token_post(
    token_id: UUID,
    org_id: UUID,  # TODO: Extract from JWT token in production
    db: Session = Depends(get_db),
):
    """Revoke (deactivate) a registration token (POST alternative)"""
    service = RegistrationTokenService(db)
    success = service.revoke_token(token_id, org_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration token not found",
        )
    return {"status": "revoked"}

