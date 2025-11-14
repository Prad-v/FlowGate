"""OpAMP service for config distribution"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.repositories.template_repository import TemplateRepository
from app.repositories.gateway_repository import GatewayRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.models.gateway import Gateway
from app.config import settings


class OpAMPService:
    """Service for OpAMP config distribution"""

    def __init__(self, db: Session):
        self.template_repo = TemplateRepository(db)
        self.gateway_repo = GatewayRepository(db)
        self.deployment_repo = DeploymentRepository(db)
        self.db = db

    def generate_opamp_token(self, gateway_id: UUID, org_id: UUID, expires_in_days: int = 365) -> str:
        """
        Generate a JWT-based OpAMP access token for a gateway
        
        Args:
            gateway_id: UUID of the gateway
            org_id: UUID of the organization
            expires_in_days: Token expiration in days (default 365)
        
        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(days=expires_in_days)
        payload = {
            "sub": str(gateway_id),  # Subject (gateway ID)
            "org_id": str(org_id),
            "type": "opamp_token",
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        return token

    def validate_opamp_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an OpAMP token and return gateway information
        
        Returns:
            Dict with gateway_id, org_id, instance_id if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            
            # Verify token type
            if payload.get("type") != "opamp_token":
                return None
            
            gateway_id = UUID(payload.get("sub"))
            org_id = UUID(payload.get("org_id"))
            
            # Verify gateway exists and matches org
            gateway = self.gateway_repo.get(gateway_id, org_id)
            if not gateway:
                return None
            
            # Verify token matches stored token (if stored)
            if gateway.opamp_token and gateway.opamp_token != token:
                return None
            
            return {
                "gateway_id": gateway_id,
                "org_id": org_id,
                "instance_id": gateway.instance_id,
            }
        except (JWTError, ValueError, TypeError):
            return None

    def get_config_for_gateway(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get the current config for a gateway instance"""
        gateway = self.gateway_repo.get_by_instance_id(instance_id)
        if not gateway:
            return None

        # Get the active deployment for this gateway
        deployments = self.deployment_repo.get_by_gateway(gateway.id, gateway.org_id)
        active_deployment = None
        for deployment in deployments:
            if deployment.status.value in ["in_progress", "completed"]:
                active_deployment = deployment
                break

        if not active_deployment:
            return None

        # Get the template version
        template_version = self.template_repo.get_version(
            active_deployment.template_id,
            active_deployment.template_version,
            gateway.org_id,
        )

        if not template_version:
            return None

        # Return config bundle
        return {
            "config_yaml": template_version.config_yaml,
            "version": template_version.version,
            "deployment_id": str(active_deployment.id),
        }

    def update_gateway_config_version(self, instance_id: str, config_version: int) -> Optional[Gateway]:
        """Update gateway's current config version"""
        gateway = self.gateway_repo.get_by_instance_id(instance_id)
        if gateway:
            gateway.current_config_version = config_version
            return self.gateway_repo.update(gateway)
        return None

