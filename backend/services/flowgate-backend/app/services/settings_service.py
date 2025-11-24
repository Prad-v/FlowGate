"""Settings Service

Service for managing organization-level settings.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.settings import Settings
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


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
            
        Raises:
            ValueError: If organization doesn't exist (foreign key violation)
        """
        settings = self.db.query(Settings).filter(Settings.org_id == org_id).first()
        
        if not settings:
            # Create default settings with supervisor mode as default
            settings = Settings(
                org_id=org_id,
                gateway_management_mode="supervisor"
            )
            self.db.add(settings)
            try:
                self.db.commit()
                self.db.refresh(settings)
            except IntegrityError as e:
                self.db.rollback()
                # Check if it's a foreign key violation (org doesn't exist)
                error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
                if "foreign key" in error_str.lower() or "ForeignKeyViolation" in error_str:
                    raise ValueError(f"Organization {org_id} does not exist")
                raise
        
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

    def get_ai_provider_config(self, org_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get AI provider configuration for an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            AI provider configuration dict or None
        """
        settings = self.get_settings(org_id)
        return settings.ai_provider_config

    def update_ai_provider_config(self, org_id: UUID, provider_config: Dict[str, Any]) -> Settings:
        """
        Update AI provider configuration.
        
        Args:
            org_id: Organization UUID
            provider_config: AI provider configuration dict
            
        Returns:
            Updated Settings object
        """
        # Validate provider type
        provider_type = provider_config.get("provider_type")
        if provider_type not in ["litellm", "openai", "anthropic", "custom"]:
            raise ValueError(f"Invalid provider type: {provider_type}")
        
        # Validate required fields based on provider type
        if provider_type in ["litellm", "custom"]:
            if not provider_config.get("endpoint"):
                raise ValueError(f"Endpoint is required for {provider_type} provider")
        
        if not provider_config.get("api_key"):
            raise ValueError("API key is required")
        
        # Mask API key in stored config (show only last 4 chars)
        api_key = provider_config.get("api_key", "")
        if api_key and len(api_key) > 4:
            masked_key = "*" * (len(api_key) - 4) + api_key[-4:]
            provider_config["api_key_masked"] = masked_key
            # Store full key separately (in production, encrypt this)
            provider_config["api_key"] = api_key
        
        settings = self.get_settings(org_id)
        settings.ai_provider_config = provider_config
        settings.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(settings)
        
        return settings

    def test_ai_provider_connection(self, org_id: UUID, provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test AI provider connection.
        
        Args:
            org_id: Organization UUID
            provider_config: AI provider configuration to test
            
        Returns:
            Test result dict with success status and message
        """
        try:
            provider_type = provider_config.get("provider_type")
            api_key = provider_config.get("api_key")
            endpoint = provider_config.get("endpoint")
            
            if not api_key:
                return {"success": False, "message": "API key is required"}
            
            if provider_type in ["litellm", "custom"] and not endpoint:
                return {"success": False, "message": "Endpoint is required for this provider type"}
            
            # Import httpx for testing connections
            import httpx
            
            # Test connection based on provider type
            if provider_type == "litellm":
                # Test LiteLLM endpoint
                test_url = f"{endpoint.rstrip('/')}/health" if endpoint else None
                if not test_url:
                    return {"success": False, "message": "Invalid endpoint URL"}
                
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(test_url, headers={"Authorization": f"Bearer {api_key}"})
                    if response.status_code == 200:
                        return {"success": True, "message": "Connection successful"}
                    else:
                        return {"success": False, "message": f"Connection failed: {response.status_code}"}
            
            elif provider_type == "openai":
                # Test OpenAI API
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    if response.status_code == 200:
                        return {"success": True, "message": "Connection successful"}
                    else:
                        return {"success": False, "message": f"Connection failed: {response.status_code}"}
            
            elif provider_type == "anthropic":
                # Test Anthropic API
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01"
                        }
                    )
                    # Anthropic might return 400 for empty request, but that means auth works
                    if response.status_code in [200, 400]:
                        return {"success": True, "message": "Connection successful"}
                    else:
                        return {"success": False, "message": f"Connection failed: {response.status_code}"}
            
            elif provider_type == "custom":
                # Test custom endpoint
                test_url = f"{endpoint.rstrip('/')}/health" if endpoint else None
                if not test_url:
                    return {"success": False, "message": "Invalid endpoint URL"}
                
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(test_url, headers={"Authorization": f"Bearer {api_key}"})
                    if response.status_code == 200:
                        return {"success": True, "message": "Connection successful"}
                    else:
                        return {"success": False, "message": f"Connection failed: {response.status_code}"}
            
            return {"success": False, "message": f"Unknown provider type: {provider_type}"}
            
        except Exception as e:
            return {"success": False, "message": f"Connection test failed: {str(e)}"}

    def get_available_models(self, org_id: UUID, provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get available models from the AI provider.
        
        Args:
            org_id: Organization UUID
            provider_config: AI provider configuration
            
        Returns:
            Dict with success status and list of available models
        """
        try:
            provider_type = provider_config.get("provider_type")
            api_key = provider_config.get("api_key")
            endpoint = provider_config.get("endpoint")
            
            if not api_key:
                return {"success": False, "message": "API key is required", "models": []}
            
            import httpx
            
            models = []
            
            if provider_type == "litellm":
                # LiteLLM provides models endpoint
                if not endpoint:
                    return {"success": False, "message": "Endpoint is required for LiteLLM", "models": []}
                
                models_url = f"{endpoint.rstrip('/')}/v1/models"
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(
                        models_url,
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and "data" in data:
                            models = [model.get("id", "") for model in data["data"] if model.get("id")]
                        elif isinstance(data, list):
                            models = [model.get("id", "") for model in data if model.get("id")]
                        return {"success": True, "models": models, "message": f"Found {len(models)} models"}
                    else:
                        return {"success": False, "message": f"Failed to fetch models: {response.status_code}", "models": []}
            
            elif provider_type == "openai":
                # OpenAI models endpoint
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and "data" in data:
                            models = [model.get("id", "") for model in data["data"] if model.get("id")]
                        return {"success": True, "models": models, "message": f"Found {len(models)} models"}
                    else:
                        return {"success": False, "message": f"Failed to fetch models: {response.status_code}", "models": []}
            
            elif provider_type == "anthropic":
                # Anthropic doesn't have a models endpoint, return common models
                models = [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-sonnet-20240620",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307",
                ]
                return {"success": True, "models": models, "message": f"Found {len(models)} models"}
            
            elif provider_type == "custom":
                # Try to fetch from custom endpoint
                if not endpoint:
                    return {"success": False, "message": "Endpoint is required for custom provider", "models": []}
                
                models_url = f"{endpoint.rstrip('/')}/v1/models"
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(
                        models_url,
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and "data" in data:
                            models = [model.get("id", "") for model in data["data"] if model.get("id")]
                        elif isinstance(data, list):
                            models = [model.get("id", "") for model in data if model.get("id")]
                        return {"success": True, "models": models, "message": f"Found {len(models)} models"}
                    else:
                        return {"success": False, "message": f"Failed to fetch models: {response.status_code}", "models": []}
            
            return {"success": False, "message": f"Unknown provider type: {provider_type}", "models": []}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to fetch models: {str(e)}", "models": []}

