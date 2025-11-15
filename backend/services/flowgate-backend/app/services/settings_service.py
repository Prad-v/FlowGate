"""Settings Service

Service for managing organization-level settings.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.settings import Settings
from datetime import datetime


class SettingsService:
    """Service for managing settings"""

    def __init__(self, db: Session):
        self.db = db

    def get_settings(self, org_id: UUID) -> Settings:
        """
        Get settings for an organization, creating default if not exists.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Settings object
        """
        settings = self.db.query(Settings).filter(Settings.org_id == org_id).first()
        
        if not settings:
            # Create default settings with supervisor mode as default
            settings = Settings(
                org_id=org_id,
                gateway_management_mode="supervisor"
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        
        return settings

    def update_gateway_management_mode(self, org_id: UUID, mode: str) -> Settings:
        """
        Update gateway management mode setting.
        
        Args:
            org_id: Organization UUID
            mode: "supervisor" or "extension"
            
        Returns:
            Updated Settings object
        """
        if mode not in ["supervisor", "extension"]:
            raise ValueError(f"Invalid management mode: {mode}. Must be 'supervisor' or 'extension'")
        
        settings = self.get_settings(org_id)
        settings.gateway_management_mode = mode
        settings.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(settings)
        
        return settings

    def get_gateway_management_mode(self, org_id: UUID) -> str:
        """
        Get gateway management mode for an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Management mode string ("supervisor" or "extension")
        """
        settings = self.get_settings(org_id)
        return settings.gateway_management_mode

