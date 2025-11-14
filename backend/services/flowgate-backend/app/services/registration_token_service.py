"""Registration token service"""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repositories.registration_token_repository import RegistrationTokenRepository
from app.models.registration_token import RegistrationToken
from app.utils.security import hash_token, verify_token, generate_secure_token


class RegistrationTokenService:
    """Service for registration token operations"""

    def __init__(self, db: Session):
        self.repository = RegistrationTokenRepository(db)
        self.db = db

    def generate_token(
        self,
        org_id: UUID,
        name: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        created_by: Optional[UUID] = None,
    ) -> Tuple[str, RegistrationToken]:
        """
        Generate a new registration token
        
        Returns:
            Tuple of (plain_token, RegistrationToken model)
            The plain token should be returned to the user immediately as it won't be stored
        """
        # Generate a secure random token
        plain_token = generate_secure_token(48)  # 48 bytes = 64 chars in base64
        
        # Hash the token before storing
        hashed_token = hash_token(plain_token)
        
        # Calculate expiration if provided
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create the token record
        token = RegistrationToken(
            org_id=org_id,
            token=hashed_token,
            name=name,
            expires_at=expires_at,
            is_active=True,
            created_by=created_by,
        )
        
        token = self.repository.create(token)
        
        # Return both the plain token (for one-time display) and the model
        return plain_token, token

    def validate_token(self, plain_token: str) -> Optional[Tuple[UUID, UUID]]:
        """
        Validate a registration token and return (org_id, token_id) if valid
        
        Returns:
            Tuple of (org_id, token_id) if valid, None otherwise
        """
        # We need to check all tokens and verify against each hash
        # This is less efficient but necessary since we can't reverse the hash
        # In production, consider using a lookup table or indexed approach
        all_tokens = self.db.query(RegistrationToken).filter(
            RegistrationToken.is_active == True
        ).all()
        
        for token in all_tokens:
            if verify_token(plain_token, token.token):
                # Check expiration
                if token.expires_at:
                    # Make both datetimes timezone-aware for comparison
                    expires_at = token.expires_at
                    if expires_at.tzinfo is None:
                        # If expires_at is naive, assume UTC
                        from datetime import timezone
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    
                    now = datetime.utcnow()
                    if now.tzinfo is None:
                        from datetime import timezone
                        now = now.replace(tzinfo=timezone.utc)
                    
                    if expires_at < now:
                        return None
                
                # Check if active
                if not token.is_active:
                    return None
                
                return (token.org_id, token.id)
        
        return None

    def revoke_token(self, token_id: UUID, org_id: UUID) -> bool:
        """Revoke (deactivate) a registration token"""
        token = self.repository.get(token_id)
        if not token or token.org_id != org_id:
            return False
        
        token.is_active = False
        self.repository.update(token)
        return True

    def list_tokens(self, org_id: UUID, include_inactive: bool = False) -> List[RegistrationToken]:
        """List all registration tokens for an organization"""
        if include_inactive:
            return self.repository.get_by_org(org_id)
        else:
            return self.repository.get_active_by_org(org_id)

    def get_token(self, token_id: UUID, org_id: UUID) -> Optional[RegistrationToken]:
        """Get a specific token by ID (scoped to organization)"""
        token = self.repository.get(token_id)
        if token and token.org_id == org_id:
            return token
        return None

