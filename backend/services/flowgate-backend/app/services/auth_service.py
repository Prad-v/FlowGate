"""Authentication service for local user authentication"""

import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for user authentication"""

    def __init__(self, db: Session):
        self.db = db

    def authenticate_local_user(self, username_or_email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username/email and password
        
        Args:
            username_or_email: Username or email address
            password: Plain text password
        
        Returns:
            User object if authentication successful, None otherwise
        """
        # Find user by username or email
        user = self.db.query(User).filter(
            or_(
                User.username == username_or_email,
                User.email == username_or_email
            )
        ).first()
        
        if not user:
            logger.warning(f"Authentication failed: User not found - {username_or_email}")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: User inactive - {username_or_email}")
            return None
        
        # Check if user has a password (not OIDC-only user)
        if not user.hashed_password:
            logger.warning(f"Authentication failed: User has no password (OIDC-only) - {username_or_email}")
            return None
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password - {username_or_email}")
            return None
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        self.db.commit()
        
        return user

    def create_access_token(self, user: User, org_id: Optional[UUID] = None) -> Tuple[str, str]:
        """
        Create access and refresh tokens for a user
        
        Args:
            user: User object
            org_id: Optional organization ID (defaults to user.org_id)
        
        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Use provided org_id or user's org_id
        token_org_id = org_id or user.org_id
        
        # Build token claims
        claims = {
            "sub": str(user.id),
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_superuser": user.is_superuser,
        }
        
        if token_org_id:
            claims["org_id"] = str(token_org_id)
        
        access_token = create_access_token(claims)
        refresh_token = create_refresh_token(claims)
        
        return access_token, refresh_token

    def require_password_change(self, user: User) -> bool:
        """
        Check if user must change password on first login
        
        Args:
            user: User object
        
        Returns:
            True if password change is required, False otherwise
        """
        return user.password_changed_at is None

    def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user: User object
            old_password: Current password
            new_password: New password
        
        Returns:
            True if password changed successfully, False otherwise
        """
        # Verify old password
        if user.hashed_password and not verify_password(old_password, user.hashed_password):
            return False
        
        # Hash and set new password
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        self.db.commit()
        
        return True

    def set_password(self, user: User, new_password: str) -> None:
        """
        Set password for user (e.g., on first login or password reset)
        
        Args:
            user: User object
            new_password: New password
        """
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        self.db.commit()

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

