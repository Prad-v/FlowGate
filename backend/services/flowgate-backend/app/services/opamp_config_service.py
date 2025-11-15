"""OpAMP Config Management Service

Service for managing OpAMP remote configuration deployments with global versioning,
canary rollouts, and audit tracking.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sqlalchemy.sql import text

from app.models.opamp_config_deployment import OpAMPConfigDeployment, OpAMPConfigDeploymentStatus
from app.models.opamp_config_audit import OpAMPConfigAudit, OpAMPConfigAuditStatus
from app.models.gateway import Gateway, OpAMPRemoteConfigStatus
from app.services.config_validator import ConfigValidator, ValidationResult
from app.services.agent_tag_service import AgentTagService
from app.services.canary_rollout_service import CanaryRolloutService
from app.services.gateway_service import GatewayService


class OpAMPConfigService:
    """Service for OpAMP config management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = ConfigValidator()
        self.agent_tag_service = AgentTagService(db)
        self.canary_service = CanaryRolloutService(db)
        self.gateway_service = GatewayService(db)
    
    def get_next_global_version(self) -> int:
        """Get next global config version from sequence"""
        result = self.db.execute(text("SELECT nextval('global_config_version_seq')"))
        return result.scalar()
    
    def validate_config_yaml(self, config_yaml: str) -> ValidationResult:
        """
        Validate YAML configuration
        
        Args:
            config_yaml: YAML configuration string
            
        Returns:
            ValidationResult with validation status and errors
        """
        return self.validator.validate(config_yaml)
    
    def create_config_deployment(
        self,
        name: str,
        config_yaml: str,
        org_id: UUID,
        rollout_strategy: str = "immediate",
        canary_percentage: Optional[int] = None,
        target_tags: Optional[List[str]] = None,
        ignore_failures: bool = False,
        template_id: Optional[UUID] = None,
        template_version: Optional[int] = None,
        created_by: Optional[UUID] = None
    ) -> Tuple[OpAMPConfigDeployment, ValidationResult]:
        """
        Create new config deployment with validation
        
        Args:
            name: Deployment name
            config_yaml: YAML configuration
            org_id: Organization UUID
            rollout_strategy: 'immediate', 'canary', or 'staged'
            canary_percentage: Percentage for canary (0-100)
            target_tags: List of tag names to target (None = all agents)
            ignore_failures: Skip validation failures
            template_id: Optional template ID
            template_version: Optional template version
            created_by: User UUID who created the deployment
            
        Returns:
            Tuple of (OpAMPConfigDeployment, ValidationResult)
        """
        # Validate config
        validation_result = self.validate_config_yaml(config_yaml)
        
        if not validation_result.is_valid and not ignore_failures:
            raise ValueError(f"Configuration validation failed: {', '.join(self.validator.get_validation_errors(validation_result))}")
        
        # Get next global version
        config_version = self.get_next_global_version()
        
        # Calculate config hash
        config_hash = self.validator.calculate_config_hash(config_yaml)
        
        # Create deployment
        deployment = OpAMPConfigDeployment(
            name=name,
            config_version=config_version,
            config_yaml=config_yaml,
            config_hash=config_hash,
            template_id=template_id,
            template_version=template_version,
            org_id=org_id,
            rollout_strategy=rollout_strategy,
            canary_percentage=canary_percentage,
            target_tags=target_tags,
            status=OpAMPConfigDeploymentStatus.PENDING,
            ignore_failures=ignore_failures,
            created_by=created_by
        )
        
        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)
        
        return deployment, validation_result
    
    def push_config_to_agents(
        self,
        deployment_id: UUID,
        org_id: UUID
    ) -> Dict[str, Any]:
        """
        Push config via OpAMP to selected agents
        
        Args:
            deployment_id: Deployment UUID
            org_id: Organization UUID
            
        Returns:
            Dict with push results
        """
        deployment = self.db.query(OpAMPConfigDeployment).filter(
            OpAMPConfigDeployment.id == deployment_id,
            OpAMPConfigDeployment.org_id == org_id
        ).first()
        
        if not deployment:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        # Update deployment status
        deployment.status = OpAMPConfigDeploymentStatus.IN_PROGRESS
        deployment.started_at = datetime.utcnow()
        self.db.commit()
        
        # Get target agents based on rollout strategy
        if deployment.rollout_strategy == "canary" and deployment.canary_percentage:
            target_agents, _ = self.canary_service.calculate_canary_targets(
                org_id,
                deployment.target_tags,
                deployment.canary_percentage
            )
        else:
            # Immediate rollout - get all eligible agents
            target_agents = self.agent_tag_service.get_agents_by_tags(
                org_id,
                deployment.target_tags,
                require_all=False
            )
        
        # Create audit entries for all target agents
        audit_entries = []
        for agent in target_agents:
            audit_entry = OpAMPConfigAudit(
                deployment_id=deployment_id,
                gateway_id=agent.id,
                config_version=deployment.config_version,
                config_hash=deployment.config_hash,
                status=OpAMPConfigAuditStatus.PENDING
            )
            self.db.add(audit_entry)
            audit_entries.append(audit_entry)
            
            # Update gateway to indicate pending config
            agent.last_config_deployment_id = deployment_id
            agent.last_config_version = deployment.config_version
            agent.last_config_status = OpAMPRemoteConfigStatus.UNSET
            agent.last_config_status_at = datetime.utcnow()
        
        self.db.commit()
        
        # Config will be sent via OpAMP protocol service when agents connect
        # The protocol service checks for pending deployments and sends config
        
        return {
            "deployment_id": str(deployment_id),
            "target_agents_count": len(target_agents),
            "config_version": deployment.config_version,
            "status": "pushed"
        }
    
    def execute_canary_rollout(
        self,
        deployment_id: UUID,
        org_id: UUID
    ) -> Dict[str, Any]:
        """
        Execute canary rollout
        
        Args:
            deployment_id: Deployment UUID
            org_id: Organization UUID
            
        Returns:
            Dict with canary rollout results
        """
        deployment = self.db.query(OpAMPConfigDeployment).filter(
            OpAMPConfigDeployment.id == deployment_id,
            OpAMPConfigDeployment.org_id == org_id
        ).first()
        
        if not deployment:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        if deployment.rollout_strategy != "canary":
            raise ValueError("Deployment is not a canary rollout")
        
        # Push to canary agents
        result = self.push_config_to_agents(deployment_id, org_id)
        
        return result
    
    def get_config_deployment_status(
        self,
        deployment_id: UUID,
        org_id: UUID
    ) -> Dict[str, Any]:
        """
        Get deployment status across all agents
        
        Args:
            deployment_id: Deployment UUID
            org_id: Organization UUID
            
        Returns:
            Dict with deployment status breakdown
        """
        deployment = self.db.query(OpAMPConfigDeployment).filter(
            OpAMPConfigDeployment.id == deployment_id,
            OpAMPConfigDeployment.org_id == org_id
        ).first()
        
        if not deployment:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        # Get progress from canary service
        progress = self.canary_service.get_rollout_progress(deployment_id, org_id)
        
        # Get agent breakdown
        audit_entries = self.db.query(OpAMPConfigAudit).filter(
            OpAMPConfigAudit.deployment_id == deployment_id
        ).all()
        
        agent_statuses = []
        for entry in audit_entries:
            gateway = self.db.query(Gateway).filter(Gateway.id == entry.gateway_id).first()
            if gateway:
                agent_statuses.append({
                    "gateway_id": str(entry.gateway_id),
                    "gateway_name": gateway.name,
                    "instance_id": gateway.instance_id,
                    "status": entry.status.value,
                    "status_reported_at": entry.status_reported_at.isoformat() if entry.status_reported_at else None,
                    "error_message": entry.error_message
                })
        
        return {
            "deployment_id": str(deployment_id),
            "deployment_name": deployment.name,
            "config_version": deployment.config_version,
            "status": deployment.status.value,
            "rollout_strategy": deployment.rollout_strategy,
            "canary_percentage": deployment.canary_percentage,
            "target_tags": deployment.target_tags,
            "progress": progress,
            "agent_statuses": agent_statuses,
            "started_at": deployment.started_at.isoformat() if deployment.started_at else None,
            "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None
        }
    
    def rollback_config_deployment(
        self,
        deployment_id: UUID,
        org_id: UUID
    ) -> OpAMPConfigDeployment:
        """
        Rollback a failed deployment
        
        Args:
            deployment_id: Deployment UUID
            org_id: Organization UUID
            
        Returns:
            Updated OpAMPConfigDeployment
        """
        deployment = self.db.query(OpAMPConfigDeployment).filter(
            OpAMPConfigDeployment.id == deployment_id,
            OpAMPConfigDeployment.org_id == org_id
        ).first()
        
        if not deployment:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        # Mark deployment as rolled back
        deployment.status = OpAMPConfigDeploymentStatus.ROLLED_BACK
        deployment.completed_at = datetime.utcnow()
        
        # Find previous deployment for each affected agent
        audit_entries = self.db.query(OpAMPConfigAudit).filter(
            OpAMPConfigAudit.deployment_id == deployment_id
        ).all()
        
        for entry in audit_entries:
            gateway = self.db.query(Gateway).filter(Gateway.id == entry.gateway_id).first()
            if gateway:
                # Find previous successful deployment
                previous_audit = self.db.query(OpAMPConfigAudit).filter(
                    and_(
                        OpAMPConfigAudit.gateway_id == gateway.id,
                        OpAMPConfigAudit.deployment_id != deployment_id,
                        OpAMPConfigAudit.status == OpAMPConfigAuditStatus.APPLIED
                    )
                ).order_by(OpAMPConfigAudit.created_at.desc()).first()
                
                if previous_audit:
                    # Revert to previous config
                    gateway.last_config_deployment_id = previous_audit.deployment_id
                    gateway.last_config_version = previous_audit.config_version
                    gateway.last_config_status = OpAMPRemoteConfigStatus.UNSET
                    gateway.last_config_status_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(deployment)
        
        return deployment
    
    def get_agent_config_history(
        self,
        gateway_id: UUID,
        org_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get config update history for an agent
        
        Args:
            gateway_id: Gateway UUID
            org_id: Organization UUID
            limit: Maximum number of entries to return
            
        Returns:
            List of config history entries
        """
        # Verify gateway belongs to org
        gateway = self.db.query(Gateway).filter(
            and_(
                Gateway.id == gateway_id,
                Gateway.org_id == org_id
            )
        ).first()
        
        if not gateway:
            raise ValueError(f"Gateway not found: {gateway_id}")
        
        # Get audit entries for this gateway
        audit_entries = self.db.query(OpAMPConfigAudit).filter(
            OpAMPConfigAudit.gateway_id == gateway_id
        ).order_by(OpAMPConfigAudit.created_at.desc()).limit(limit).all()
        
        history = []
        for entry in audit_entries:
            deployment = self.db.query(OpAMPConfigDeployment).filter(
                OpAMPConfigDeployment.id == entry.deployment_id
            ).first()
            
            history.append({
                "audit_id": str(entry.id),
                "deployment_id": str(entry.deployment_id),
                "deployment_name": deployment.name if deployment else None,
                "config_version": entry.config_version,
                "config_hash": entry.config_hash,
                "status": entry.status.value,
                "status_reported_at": entry.status_reported_at.isoformat() if entry.status_reported_at else None,
                "error_message": entry.error_message,
                "effective_config_hash": entry.effective_config_hash,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            })
        
        return history
    
    def get_deployment_audit_log(
        self,
        deployment_id: UUID,
        org_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get audit log for a deployment
        
        Args:
            deployment_id: Deployment UUID
            org_id: Organization UUID
            
        Returns:
            List of audit log entries
        """
        deployment = self.db.query(OpAMPConfigDeployment).filter(
            OpAMPConfigDeployment.id == deployment_id,
            OpAMPConfigDeployment.org_id == org_id
        ).first()
        
        if not deployment:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        audit_entries = self.db.query(OpAMPConfigAudit).filter(
            OpAMPConfigAudit.deployment_id == deployment_id
        ).order_by(OpAMPConfigAudit.created_at.desc()).all()
        
        audit_log = []
        for entry in audit_entries:
            gateway = self.db.query(Gateway).filter(Gateway.id == entry.gateway_id).first()
            
            audit_log.append({
                "audit_id": str(entry.id),
                "gateway_id": str(entry.gateway_id),
                "gateway_name": gateway.name if gateway else None,
                "instance_id": gateway.instance_id if gateway else None,
                "config_version": entry.config_version,
                "config_hash": entry.config_hash,
                "status": entry.status.value,
                "status_reported_at": entry.status_reported_at.isoformat() if entry.status_reported_at else None,
                "error_message": entry.error_message,
                "effective_config_hash": entry.effective_config_hash,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else None
            })
        
        return audit_log
    
    def update_config_status_from_agent(
        self,
        instance_id: str,
        config_hash: str,
        status: str,
        effective_config_hash: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update config status from agent report
        
        Args:
            instance_id: Gateway instance ID
            config_hash: Config hash from agent
            status: Status (APPLIED, APPLYING, FAILED)
            effective_config_hash: Effective config hash from agent
            error_message: Error message if failed
        """
        gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
        if not gateway:
            return
        
        # Find deployment by config hash
        deployment = self.db.query(OpAMPConfigDeployment).filter(
            OpAMPConfigDeployment.config_hash == config_hash
        ).first()
        
        if not deployment:
            return
        
        # Find or create audit entry
        audit_entry = self.db.query(OpAMPConfigAudit).filter(
            and_(
                OpAMPConfigAudit.deployment_id == deployment.id,
                OpAMPConfigAudit.gateway_id == gateway.id
            )
        ).first()
        
        if not audit_entry:
            audit_entry = OpAMPConfigAudit(
                deployment_id=deployment.id,
                gateway_id=gateway.id,
                config_version=deployment.config_version,
                config_hash=deployment.config_hash,
                status=OpAMPConfigAuditStatus.PENDING
            )
            self.db.add(audit_entry)
        
        # Map OpAMP status to audit status
        status_mapping = {
            'APPLIED': OpAMPConfigAuditStatus.APPLIED,
            'APPLYING': OpAMPConfigAuditStatus.APPLYING,
            'FAILED': OpAMPConfigAuditStatus.FAILED,
            'UNSET': OpAMPConfigAuditStatus.PENDING
        }
        
        audit_entry.status = status_mapping.get(status, OpAMPConfigAuditStatus.PENDING)
        audit_entry.status_reported_at = datetime.utcnow()
        audit_entry.error_message = error_message
        audit_entry.effective_config_hash = effective_config_hash
        
        # Update gateway
        try:
            if status in ['APPLIED', 'APPLYING', 'FAILED', 'UNSET']:
                gateway.last_config_status = OpAMPRemoteConfigStatus(status)
            else:
                gateway.last_config_status = None
        except (ValueError, AttributeError):
            gateway.last_config_status = None
        
        gateway.last_config_status_at = datetime.utcnow()
        gateway.last_config_version = deployment.config_version
        gateway.last_config_deployment_id = deployment.id
        
        self.db.commit()
    
    def get_current_config_for_gateway(self, gateway_id: UUID, org_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get current configuration for a specific gateway.
        
        Args:
            gateway_id: Gateway UUID
            org_id: Organization UUID
            
        Returns:
            Dict with current config info, or None if not found
        """
        gateway = self.db.query(Gateway).filter(
            Gateway.id == gateway_id,
            Gateway.org_id == org_id
        ).first()
        
        if not gateway:
            return None
        
        # If gateway has a last_config_deployment_id, get that deployment
        if gateway.last_config_deployment_id:
            deployment = self.db.query(OpAMPConfigDeployment).filter(
                OpAMPConfigDeployment.id == gateway.last_config_deployment_id
            ).first()
            
            if deployment:
                return {
                    "config_yaml": deployment.config_yaml,
                    "config_version": deployment.config_version,
                    "config_hash": deployment.config_hash,
                    "deployment_id": str(deployment.id),
                    "deployment_name": deployment.name
                }
        
        # If no deployment, return None
        return None

