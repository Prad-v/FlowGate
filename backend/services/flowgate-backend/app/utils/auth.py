"""Authentication utilities"""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.registration_token_service import RegistrationTokenService
from app.services.opamp_service import OpAMPService
from app.database import get_db
from sqlalchemy.orm import Session

security = HTTPBearer()


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


def get_current_user_org_id() -> UUID:
    """
    Get current user's organization ID.
    
    For now, this returns a default org_id for development/testing.
    In production, this should extract org_id from the authenticated user's session.
    
    Returns:
        Organization UUID
    """
    # TODO: In production, get org_id from authenticated user session
    # For now, use a default org_id for development/testing
    from uuid import UUID
    # Default org_id - in production, get from user session
    return UUID('8057ca8e-4f71-4a19-b821-5937f129a0ec')

