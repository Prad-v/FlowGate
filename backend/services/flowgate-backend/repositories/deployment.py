"""Deployment repository."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.deployment import Deployment
from repositories.base import BaseRepository


class DeploymentRepository(BaseRepository[Deployment]):
    """Repository for Deployment operations."""
    
    def __init__(self, db: Session):
        """Initialize deployment repository."""
        super().__init__(Deployment, db)
        self.db = db
    
    def get_by_template(
        self,
        template_id: UUID,
        org_id: Optional[UUID] = None
    ) -> List[Deployment]:
        """Get deployments for a template."""
        query = self.db.query(Deployment).filter(Deployment.template_id == template_id)
        if org_id:
            query = query.filter(Deployment.org_id == org_id)
        return query.order_by(Deployment.created_at.desc()).all()
    
    def get_by_gateway(
        self,
        gateway_id: UUID,
        org_id: Optional[UUID] = None
    ) -> List[Deployment]:
        """Get deployments for a gateway."""
        query = self.db.query(Deployment).filter(Deployment.gateway_id == gateway_id)
        if org_id:
            query = query.filter(Deployment.org_id == org_id)
        return query.order_by(Deployment.created_at.desc()).all()
    
    def get_active_deployments(
        self,
        org_id: Optional[UUID] = None
    ) -> List[Deployment]:
        """Get active deployments (pending or in_progress)."""
        query = self.db.query(Deployment).filter(
            Deployment.status.in_(["pending", "in_progress"])
        )
        if org_id:
            query = query.filter(Deployment.org_id == org_id)
        return query.all()


