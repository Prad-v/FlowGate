"""SOAR Automation Agent (SAA) Service

Handles playbook execution and external integrations.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from app.models.soar_playbook import SOARPlaybook, PlaybookExecution, PlaybookStatus, PlaybookTriggerType

logger = logging.getLogger(__name__)


class SOARAutomationService:
    """SOAR Automation Agent service"""

    def __init__(self, db: Session):
        self.db = db

    def execute_playbook(
        self,
        org_id: UUID,
        playbook_id: UUID,
        trigger_type: PlaybookTriggerType,
        trigger_entity_id: Optional[str] = None,
        trigger_entity_type: Optional[str] = None,
        approved_by: Optional[str] = None
    ) -> PlaybookExecution:
        """Execute a SOAR playbook"""
        # Get playbook
        playbook = self.db.query(SOARPlaybook).filter(
            SOARPlaybook.id == playbook_id,
            SOARPlaybook.organization_id == org_id,
            SOARPlaybook.is_enabled == True
        ).first()
        
        if not playbook:
            raise ValueError(f"Playbook not found or disabled: {playbook_id}")
        
        # Check if approval required
        if playbook.requires_approval and not approved_by:
            raise ValueError("Playbook requires approval")
        
        # Create execution record
        execution = PlaybookExecution(
            organization_id=org_id,
            playbook_id=playbook_id,
            status=PlaybookStatus.PENDING,
            trigger_type=trigger_type,
            trigger_entity_id=trigger_entity_id,
            trigger_entity_type=trigger_entity_type,
            approved_by=approved_by,
            approved_at=datetime.utcnow() if approved_by else None
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        # Execute playbook (simplified - in production, use proper playbook engine)
        try:
            execution.status = PlaybookStatus.RUNNING
            execution.started_at = datetime.utcnow()
            self.db.commit()
            
            # Execute playbook steps (placeholder)
            execution_logs = [{"step": "playbook_started", "timestamp": datetime.utcnow().isoformat()}]
            actions_taken = []
            
            # In production, parse playbook_yaml and execute steps
            execution.execution_logs = execution_logs
            execution.actions_taken = actions_taken
            execution.status = PlaybookStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            
        except Exception as e:
            execution.status = PlaybookStatus.FAILED
            execution.errors = [str(e)]
            logger.error(f"Playbook execution failed: {e}")
        
        self.db.commit()
        self.db.refresh(execution)
        
        return execution

    def get_playbooks(
        self,
        org_id: UUID,
        is_enabled: Optional[bool] = None
    ) -> List[SOARPlaybook]:
        """Get SOAR playbooks for an organization"""
        query = self.db.query(SOARPlaybook).filter(
            SOARPlaybook.organization_id == org_id
        )
        
        if is_enabled is not None:
            query = query.filter(SOARPlaybook.is_enabled == is_enabled)
        
        return query.order_by(SOARPlaybook.created_at.desc()).all()

    def get_executions(
        self,
        org_id: UUID,
        playbook_id: Optional[UUID] = None,
        status: Optional[PlaybookStatus] = None,
        limit: int = 100
    ) -> List[PlaybookExecution]:
        """Get playbook executions"""
        query = self.db.query(PlaybookExecution).filter(
            PlaybookExecution.organization_id == org_id
        )
        
        if playbook_id:
            query = query.filter(PlaybookExecution.playbook_id == playbook_id)
        
        if status:
            query = query.filter(PlaybookExecution.status == status)
        
        return query.order_by(PlaybookExecution.created_at.desc()).limit(limit).all()

