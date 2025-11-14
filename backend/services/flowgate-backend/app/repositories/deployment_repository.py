"""Deployment repository"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.deployment import Deployment, DeploymentStatus
from app.repositories.base_repository import BaseRepository


class DeploymentRepository(BaseRepository[Deployment]):
    """Repository for Deployment operations"""

    def __init__(self, db: Session):
        super().__init__(Deployment, db)

    def get_by_template(self, template_id: UUID, org_id: UUID) -> List[Deployment]:
        """Get all deployments for a template"""
        return (
            self.db.query(Deployment)
            .filter(
                Deployment.template_id == template_id,
                Deployment.org_id == org_id,
            )
            .order_by(Deployment.created_at.desc())
            .all()
        )

    def get_by_gateway(self, gateway_id: UUID, org_id: UUID) -> List[Deployment]:
        """Get all deployments for a gateway"""
        return (
            self.db.query(Deployment)
            .filter(
                Deployment.gateway_id == gateway_id,
                Deployment.org_id == org_id,
            )
            .order_by(Deployment.created_at.desc())
            .all()
        )

    def get_active_deployments(self, org_id: UUID) -> List[Deployment]:
        """Get all active (in-progress) deployments"""
        return (
            self.db.query(Deployment)
            .filter(
                Deployment.org_id == org_id,
                Deployment.status == DeploymentStatus.IN_PROGRESS,
            )
            .all()
        )

