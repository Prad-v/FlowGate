"""Canary Rollout Service

Service for managing canary-based config rollouts with percentage-based targeting.
"""

import random
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.gateway import Gateway
from app.services.agent_tag_service import AgentTagService


class CanaryRolloutService:
    """Service for canary rollout management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_tag_service = AgentTagService(db)
    
    def calculate_canary_targets(
        self,
        org_id: UUID,
        tags: Optional[List[str]] = None,
        percentage: int = 0
    ) -> Tuple[List[Gateway], List[Gateway]]:
        """
        Calculate which agents to target for canary rollout
        
        Args:
            org_id: Organization UUID
            tags: List of tag names to filter by (None = all agents)
            percentage: Percentage of agents to target (0-100)
            
        Returns:
            Tuple of (target_agents, remaining_agents)
        """
        # Get all eligible agents
        eligible_agents = self.agent_tag_service.get_agents_by_tags(org_id, tags, require_all=False)
        
        if not eligible_agents:
            return [], []
        
        # Calculate number of agents to target
        total_count = len(eligible_agents)
        target_count = max(1, int(total_count * percentage / 100))
        
        # Randomly select agents for canary
        # Use deterministic selection based on agent ID for consistency
        sorted_agents = sorted(eligible_agents, key=lambda g: str(g.id))
        random.seed(hash(str(org_id)))  # Deterministic seed for consistency
        target_agents = random.sample(sorted_agents, min(target_count, total_count))
        remaining_agents = [a for a in sorted_agents if a not in target_agents]
        
        return target_agents, remaining_agents
    
    def execute_canary_phase(
        self,
        org_id: UUID,
        tags: Optional[List[str]] = None,
        percentage: int = 10
    ) -> List[Gateway]:
        """
        Execute one phase of canary rollout
        
        Args:
            org_id: Organization UUID
            tags: List of tag names to filter by
            percentage: Percentage of agents to target in this phase
            
        Returns:
            List of Gateway objects selected for canary
        """
        target_agents, _ = self.calculate_canary_targets(org_id, tags, percentage)
        return target_agents
    
    def monitor_canary_health(
        self,
        gateway_ids: List[UUID],
        min_success_rate: float = 0.95
    ) -> Tuple[bool, float, int, int]:
        """
        Monitor success/failure rates for canary deployment
        
        Args:
            gateway_ids: List of gateway UUIDs in canary
            min_success_rate: Minimum success rate required (0.0-1.0)
            
        Returns:
            Tuple of (is_healthy, success_rate, success_count, total_count)
        """
        gateways = self.db.query(Gateway).filter(Gateway.id.in_(gateway_ids)).all()
        
        if not gateways:
            return False, 0.0, 0, 0
        
        total_count = len(gateways)
        success_count = 0
        
        for gateway in gateways:
            # Check if config was successfully applied
            if gateway.last_config_status == 'APPLIED':
                success_count += 1
        
        success_rate = success_count / total_count if total_count > 0 else 0.0
        is_healthy = success_rate >= min_success_rate
        
        return is_healthy, success_rate, success_count, total_count
    
    def promote_canary_to_full(
        self,
        org_id: UUID,
        canary_agents: List[Gateway],
        tags: Optional[List[str]] = None
    ) -> List[Gateway]:
        """
        Promote successful canary to full rollout
        
        Args:
            org_id: Organization UUID
            canary_agents: List of agents that were in canary
            tags: List of tag names to filter remaining agents
            
        Returns:
            List of remaining agents to target
        """
        # Get all eligible agents
        all_eligible = self.agent_tag_service.get_agents_by_tags(org_id, tags, require_all=False)
        
        # Get remaining agents (not in canary)
        canary_ids = {a.id for a in canary_agents}
        remaining_agents = [a for a in all_eligible if a.id not in canary_ids]
        
        return remaining_agents
    
    def rollback_canary(
        self,
        gateway_ids: List[UUID]
    ) -> int:
        """
        Rollback canary deployment
        
        Args:
            gateway_ids: List of gateway UUIDs to rollback
            
        Returns:
            Number of agents rolled back
        """
        # This would typically involve:
        # 1. Reverting to previous config version
        # 2. Updating deployment status
        # 3. Creating audit entries
        
        # For now, just return count
        # Actual rollback logic will be in OpAMP config service
        return len(gateway_ids)
    
    def get_rollout_progress(
        self,
        deployment_id: UUID,
        org_id: UUID
    ) -> dict:
        """
        Get progress of a rollout deployment
        
        Args:
            deployment_id: Deployment UUID
            org_id: Organization UUID
            
        Returns:
            Dict with progress metrics
        """
        from app.models.opamp_config_audit import OpAMPConfigAudit, OpAMPConfigAuditStatus
        
        # Get all audit entries for this deployment
        audit_entries = self.db.query(OpAMPConfigAudit).filter(
            OpAMPConfigAudit.deployment_id == deployment_id
        ).all()
        
        total = len(audit_entries)
        applied = sum(1 for e in audit_entries if e.status == OpAMPConfigAuditStatus.APPLIED)
        applying = sum(1 for e in audit_entries if e.status == OpAMPConfigAuditStatus.APPLYING)
        failed = sum(1 for e in audit_entries if e.status == OpAMPConfigAuditStatus.FAILED)
        pending = sum(1 for e in audit_entries if e.status == OpAMPConfigAuditStatus.PENDING)
        
        return {
            "total": total,
            "applied": applied,
            "applying": applying,
            "failed": failed,
            "pending": pending,
            "success_rate": applied / total if total > 0 else 0.0
        }

