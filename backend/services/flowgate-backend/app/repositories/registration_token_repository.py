"""Registration token repository"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.registration_token import RegistrationToken
from app.repositories.base_repository import BaseRepository


class RegistrationTokenRepository(BaseRepository[RegistrationToken]):
    """Repository for registration token operations"""

    def __init__(self, db: Session):
        super().__init__(RegistrationToken, db)

    def get_by_token_hash(self, token_hash: str) -> Optional[RegistrationToken]:
        """Get a registration token by its hash"""
        return self.db.query(RegistrationToken).filter(RegistrationToken.token == token_hash).first()

    def get_by_org(self, org_id: UUID) -> List[RegistrationToken]:
        """Get all registration tokens for an organization"""
        return self.db.query(RegistrationToken).filter(RegistrationToken.org_id == org_id).all()

    def get_active_by_org(self, org_id: UUID) -> List[RegistrationToken]:
        """Get all active registration tokens for an organization"""
        return (
            self.db.query(RegistrationToken)
            .filter(RegistrationToken.org_id == org_id)
            .filter(RegistrationToken.is_active == True)
            .all()
        )

