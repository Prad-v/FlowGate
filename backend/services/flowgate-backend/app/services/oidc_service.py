"""OIDC service for OAuth/OIDC authentication"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oidc.core import UserInfo
import httpx
from app.models.oidc_provider import OIDCProvider, OIDCProviderType
from app.models.user import User
from app.services.auth_service import AuthService
from cryptography.fernet import Fernet
from app.config import settings
import base64
import os

logger = logging.getLogger(__name__)


class OIDCService:
    """Service for OIDC/OAuth2 authentication"""

    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService(db)
        # Get encryption key from environment or generate one
        encryption_key = os.getenv("OIDC_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a key (in production, this should be set via environment variable)
            encryption_key = Fernet.generate_key().decode()
            logger.warning("OIDC_ENCRYPTION_KEY not set, using generated key (not secure for production)")
        self.cipher = Fernet(encryption_key.encode())

    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt OIDC client secret"""
        try:
            return self.cipher.decrypt(encrypted_secret.encode()).decode()
        except Exception as e:
            logger.error(f"Error decrypting secret: {e}")
            raise

    def _encrypt_secret(self, plain_secret: str) -> str:
        """Encrypt OIDC client secret"""
        return self.cipher.encrypt(plain_secret.encode()).decode()

    def get_authorization_url(
        self,
        provider_id: UUID,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> Optional[str]:
        """
        Get OIDC authorization URL for direct integration providers
        
        Args:
            provider_id: OIDC provider UUID
            redirect_uri: OAuth redirect URI
            state: Optional state parameter for CSRF protection
        
        Returns:
            Authorization URL or None if provider not found/invalid
        """
        provider = self.db.query(OIDCProvider).filter(
            OIDCProvider.id == provider_id,
            OIDCProvider.is_active == True
        ).first()
        
        if not provider or provider.provider_type != OIDCProviderType.DIRECT:
            return None
        
        if not provider.authorization_endpoint:
            return None
        
        # Build authorization URL
        params = {
            "client_id": provider.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": provider.scopes or "openid profile email",
        }
        
        if state:
            params["state"] = state
        
        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{provider.authorization_endpoint}?{query_string}"

    async def handle_oidc_callback(
        self,
        provider_id: UUID,
        code: str,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> Optional[User]:
        """
        Handle OIDC callback and create/update user
        
        Args:
            provider_id: OIDC provider UUID
            code: Authorization code from OIDC provider
            redirect_uri: OAuth redirect URI
            state: Optional state parameter
        
        Returns:
            User object if successful, None otherwise
        """
        provider = self.db.query(OIDCProvider).filter(
            OIDCProvider.id == provider_id,
            OIDCProvider.is_active == True
        ).first()
        
        if not provider:
            return None
        
        if provider.provider_type == OIDCProviderType.DIRECT:
            return await self._handle_direct_oidc(provider, code, redirect_uri)
        elif provider.provider_type == OIDCProviderType.PROXY:
            return await self._handle_proxy_oidc(provider, code, redirect_uri)
        
        return None

    async def _handle_direct_oidc(
        self,
        provider: OIDCProvider,
        code: str,
        redirect_uri: str
    ) -> Optional[User]:
        """Handle direct OIDC integration (Okta, Azure AD, Google)"""
        try:
            # Decrypt client secret
            client_secret = self._decrypt_secret(provider.client_secret_encrypted)
            
            # Exchange code for token
            async with httpx.AsyncClient() as client:
                token_data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": provider.client_id,
                    "client_secret": client_secret,
                }
                
                response = await client.post(
                    provider.token_endpoint,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                token_response = response.json()
            
            access_token = token_response.get("access_token")
            if not access_token:
                logger.error("No access token in OIDC response")
                return None
            
            # Get user info
            user_info = await self.get_user_info(provider.id, access_token)
            if not user_info:
                return None
            
            # Create or update user
            return await self._create_or_update_user(provider, user_info)
            
        except Exception as e:
            logger.error(f"Error handling direct OIDC: {e}")
            return None

    async def _handle_proxy_oidc(
        self,
        provider: OIDCProvider,
        code: str,
        redirect_uri: str
    ) -> Optional[User]:
        """Handle OAuth proxy integration"""
        try:
            # Forward to proxy for token exchange
            async with httpx.AsyncClient() as client:
                token_data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                }
                
                # Add client credentials if provided
                if provider.client_id:
                    token_data["client_id"] = provider.client_id
                if provider.client_secret_encrypted:
                    client_secret = self._decrypt_secret(provider.client_secret_encrypted)
                    token_data["client_secret"] = client_secret
                
                proxy_token_url = f"{provider.proxy_url.rstrip('/')}/token"
                response = await client.post(
                    proxy_token_url,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                token_response = response.json()
            
            access_token = token_response.get("access_token")
            if not access_token:
                logger.error("No access token in proxy response")
                return None
            
            # Get user info from proxy
            proxy_userinfo_url = f"{provider.proxy_url.rstrip('/')}/userinfo"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    proxy_userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                user_info = response.json()
            
            # Create or update user
            return await self._create_or_update_user(provider, user_info)
            
        except Exception as e:
            logger.error(f"Error handling proxy OIDC: {e}")
            return None

    async def get_user_info(self, provider_id: UUID, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user info from OIDC provider
        
        Args:
            provider_id: OIDC provider UUID
            access_token: OAuth access token
        
        Returns:
            User info dictionary or None
        """
        provider = self.db.query(OIDCProvider).filter(OIDCProvider.id == provider_id).first()
        if not provider:
            return None
        
        try:
            if provider.provider_type == OIDCProviderType.DIRECT:
                # Use userinfo endpoint
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        provider.userinfo_endpoint,
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    response.raise_for_status()
                    return response.json()
            else:
                # Proxy handles userinfo
                return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

    async def _create_or_update_user(
        self,
        provider: OIDCProvider,
        user_info: Dict[str, Any]
    ) -> Optional[User]:
        """Create or update user from OIDC user info"""
        try:
            # Extract user info
            oidc_subject = user_info.get("sub") or user_info.get("id")
            email = user_info.get("email")
            name = user_info.get("name") or user_info.get("display_name") or user_info.get("preferred_username")
            
            if not oidc_subject:
                logger.error("No subject (sub) in OIDC user info")
                return None
            
            if not email:
                logger.error("No email in OIDC user info")
                return None
            
            # Find existing user by OIDC subject or email
            user = self.db.query(User).filter(
                (User.oidc_subject == oidc_subject) & (User.oidc_provider_id == provider.id)
            ).first()
            
            if not user:
                # Check if user exists by email
                user = self.db.query(User).filter(User.email == email).first()
            
            if user:
                # Update existing user
                user.oidc_provider_id = provider.id
                user.oidc_subject = oidc_subject
                if name and not user.full_name:
                    user.full_name = name
                user.last_login_at = datetime.utcnow()
            else:
                # Create new user
                username = email.split("@")[0]  # Use email prefix as username
                # Ensure username is unique
                base_username = username
                counter = 1
                while self.db.query(User).filter(User.username == username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User(
                    email=email,
                    username=username,
                    full_name=name,
                    hashed_password=None,  # OIDC-only user
                    is_active=True,
                    is_superuser=False,
                    org_id=provider.org_id,
                    oidc_provider_id=provider.id,
                    oidc_subject=oidc_subject,
                    password_changed_at=None,  # OIDC users don't need password
                )
                self.db.add(user)
            
            self.db.commit()
            self.db.refresh(user)
            return user
            
        except Exception as e:
            logger.error(f"Error creating/updating user from OIDC: {e}")
            self.db.rollback()
            return None

