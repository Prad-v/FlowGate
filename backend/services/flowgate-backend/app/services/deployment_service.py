"""Deployment service"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.template_repository import TemplateRepository
from app.repositories.gateway_repository import GatewayRepository
from app.models.deployment import Deployment, DeploymentStatus
from app.schemas.deployment import DeploymentCreate, DeploymentUpdate, DeploymentStatusUpdate


class DeploymentService:
    """Service for deployment operations"""

    def __init__(self, db: Session):
        self.deployment_repo = DeploymentRepository(db)
        self.template_repo = TemplateRepository(db)
        self.gateway_repo = GatewayRepository(db)
        self.db = db

    def create_deployment(self, deployment_data: DeploymentCreate) -> Deployment:
        """Create a new deployment"""
        # Validate template exists
        template = self.template_repo.get(deployment_data.template_id, deployment_data.org_id)
        if not template:
            raise ValueError("Template not found")

        # Validate template version exists
        version = self.template_repo.get_version(
            deployment_data.template_id,
            deployment_data.template_version,
            deployment_data.org_id,
        )
        if not version:
            raise ValueError("Template version not found")

        # If gateway_id specified, validate it exists
        if deployment_data.gateway_id:
            gateway = self.gateway_repo.get(deployment_data.gateway_id, deployment_data.org_id)
            if not gateway:
                raise ValueError("Gateway not found")

        # Create deployment
        deployment = Deployment(
            name=deployment_data.name,
            template_id=deployment_data.template_id,
            template_version=deployment_data.template_version,
            gateway_id=deployment_data.gateway_id,
            org_id=deployment_data.org_id,
            status=DeploymentStatus.PENDING,
            rollout_strategy=deployment_data.rollout_strategy,
            canary_percentage=deployment_data.canary_percentage,
            metadata=deployment_data.metadata,
        )
        return self.deployment_repo.create(deployment)

    def get_deployment(self, deployment_id: UUID, org_id: UUID) -> Optional[Deployment]:
        """Get a deployment by ID"""
        return self.deployment_repo.get(deployment_id, org_id)

    def get_deployments(self, org_id: UUID, skip: int = 0, limit: int = 100) -> List[Deployment]:
        """Get all deployments for an organization"""
        return self.deployment_repo.get_by_org(org_id, skip, limit)

    def update_deployment_status(
        self, deployment_id: UUID, org_id: UUID, status_update: DeploymentStatusUpdate
    ) -> Optional[Deployment]:
        """Update deployment status"""
        deployment = self.deployment_repo.get(deployment_id, org_id)
        if not deployment:
            return None

        deployment.status = status_update.status
        if status_update.error_message:
            deployment.error_message = status_update.error_message

        if status_update.status == DeploymentStatus.IN_PROGRESS and not deployment.started_at:
            deployment.started_at = datetime.utcnow()
        elif status_update.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]:
            deployment.completed_at = datetime.utcnow()

        return self.deployment_repo.update(deployment)

    def start_deployment(self, deployment_id: UUID, org_id: UUID) -> Optional[Deployment]:
        """Start a deployment"""
        return self.update_deployment_status(
            deployment_id,
            org_id,
            DeploymentStatusUpdate(status=DeploymentStatus.IN_PROGRESS),
        )

    def complete_deployment(self, deployment_id: UUID, org_id: UUID) -> Optional[Deployment]:
        """Mark deployment as completed"""
        return self.update_deployment_status(
            deployment_id,
            org_id,
            DeploymentStatusUpdate(status=DeploymentStatus.COMPLETED),
        )

    def fail_deployment(self, deployment_id: UUID, org_id: UUID, error_message: str) -> Optional[Deployment]:
        """Mark deployment as failed"""
        return self.update_deployment_status(
            deployment_id,
            org_id,
            DeploymentStatusUpdate(status=DeploymentStatus.FAILED, error_message=error_message),
        )

    def rollback_deployment(self, deployment_id: UUID, org_id: UUID) -> Optional[Deployment]:
        """Rollback a deployment"""
        return self.update_deployment_status(
            deployment_id,
            org_id,
            DeploymentStatusUpdate(status=DeploymentStatus.ROLLED_BACK),
        )

