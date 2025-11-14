"""Deployment service."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from models.deployment import Deployment
from models.template import Template
from repositories.deployment import DeploymentRepository
from repositories.gateway import GatewayRepository
from repositories.template import TemplateRepository
from schemas.deployment import DeploymentCreate, DeploymentUpdate, DeploymentResponse
from services.opamp import OpAMPService


class DeploymentService:
    """Service for deployment operations."""
    
    def __init__(self, db: Session):
        """Initialize deployment service."""
        self.db = db
        self.repo = DeploymentRepository(db)
        self.gateway_repo = GatewayRepository(db)
        self.template_repo = TemplateRepository(db)
        self.opamp_service = OpAMPService(db)
    
    def create_deployment(
        self,
        org_id: UUID,
        deployment_data: DeploymentCreate
    ) -> Deployment:
        """Create a new deployment."""
        # Validate template exists
        template = self.template_repo.get(deployment_data.template_id, org_id)
        if not template:
            raise ValueError("Template not found")
        
        # Validate template version exists
        version = self.template_repo.get_version(
            deployment_data.template_id,
            deployment_data.template_version,
            org_id
        )
        if not version:
            raise ValueError("Template version not found")
        
        # Validate gateway if specified
        if deployment_data.gateway_id:
            gateway = self.gateway_repo.get(deployment_data.gateway_id, org_id)
            if not gateway:
                raise ValueError("Gateway not found")
        
        # Create deployment
        deployment = Deployment(
            org_id=org_id,
            name=deployment_data.name,
            template_id=deployment_data.template_id,
            template_version=deployment_data.template_version,
            gateway_id=deployment_data.gateway_id,
            status="pending",
            rollout_strategy=deployment_data.rollout_strategy,
            canary_percentage=deployment_data.canary_percentage,
            metadata=deployment_data.metadata
        )
        deployment = self.repo.create(deployment)
        
        # Start rollout (async in production)
        self._start_rollout(deployment)
        
        return deployment
    
    def _start_rollout(self, deployment: Deployment):
        """Start the rollout process."""
        deployment.status = "in_progress"
        deployment.started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # Get template version config
            version = self.template_repo.get_version(
                deployment.template_id,
                deployment.template_version,
                deployment.org_id
            )
            
            if not version:
                raise ValueError("Template version not found")
            
            # Determine target gateways
            if deployment.gateway_id:
                gateways = [self.gateway_repo.get(deployment.gateway_id, deployment.org_id)]
            else:
                gateways = self.gateway_repo.get_online_gateways(deployment.org_id)
            
            # Push config via OpAMP
            for gateway in gateways:
                if gateway:
                    self.opamp_service.push_config(
                        gateway.instance_id,
                        version.config_yaml,
                        deployment.org_id
                    )
                    # Update gateway config version
                    gateway.config_version = deployment.template_version
                    self.db.commit()
            
            deployment.status = "completed"
            deployment.completed_at = datetime.utcnow()
        except Exception as e:
            deployment.status = "failed"
            deployment.error_message = str(e)
        finally:
            self.db.commit()
    
    def get_deployment(self, deployment_id: UUID, org_id: UUID) -> Optional[Deployment]:
        """Get a deployment by ID."""
        return self.repo.get(deployment_id, org_id)
    
    def get_deployments(
        self,
        org_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Deployment]:
        """Get all deployments for an organization."""
        return self.repo.get_multi(org_id=org_id, skip=skip, limit=limit)
    
    def rollback_deployment(
        self,
        deployment_id: UUID,
        org_id: UUID
    ) -> Optional[Deployment]:
        """Rollback a deployment."""
        deployment = self.repo.get(deployment_id, org_id)
        if not deployment:
            return None
        
        # Get previous version
        previous_version = deployment.template_version - 1
        if previous_version < 1:
            raise ValueError("No previous version to rollback to")
        
        # Create rollback deployment
        rollback = Deployment(
            org_id=org_id,
            name=f"Rollback: {deployment.name}",
            template_id=deployment.template_id,
            template_version=previous_version,
            gateway_id=deployment.gateway_id,
            status="pending",
            rollout_strategy="immediate",
            metadata={"rollback_from": str(deployment.id)}
        )
        rollback = self.repo.create(rollback)
        
        # Mark original as rolled back
        deployment.status = "rolled_back"
        self.db.commit()
        
        # Start rollback rollout
        self._start_rollout(rollback)
        
        return rollback


