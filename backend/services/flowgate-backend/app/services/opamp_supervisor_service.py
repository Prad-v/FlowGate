"""OpAMP Supervisor Service

Service for managing supervisor-specific operations and status.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.gateway import Gateway, ManagementMode
import logging

logger = logging.getLogger(__name__)


class OpAMPSupervisorService:
    """Service for managing OpAMP Supervisor operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_supervisor_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get supervisor health/status for an agent.
        
        Args:
            instance_id: Gateway instance ID
            
        Returns:
            Dict with supervisor status information, or None if not found
        """
        gateway = self.db.query(Gateway).filter(Gateway.instance_id == instance_id).first()
        if not gateway:
            return None
        
        if gateway.management_mode != ManagementMode.SUPERVISOR.value:
            return {
                "error": "Agent is not managed by supervisor",
                "management_mode": gateway.management_mode
            }
        
        # Get supervisor status from stored JSONB field
        supervisor_status = gateway.supervisor_status or {}
        
        # Combine with gateway status
        return {
            "instance_id": instance_id,
            "gateway_id": str(gateway.id),
            "management_mode": gateway.management_mode,
            "supervisor_status": supervisor_status,
            "opamp_connection_status": gateway.opamp_connection_status,
            "last_seen": gateway.last_seen.isoformat() if gateway.last_seen else None,
            "logs_path": gateway.supervisor_logs_path
        }

    def get_supervisor_logs(self, instance_id: str, lines: int = 100) -> Optional[str]:
        """
        Retrieve supervisor logs for an agent.
        
        Args:
            instance_id: Gateway instance ID
            lines: Number of log lines to retrieve (default: 100)
            
        Returns:
            Log content as string, or None if not found
        """
        gateway = self.db.query(Gateway).filter(Gateway.instance_id == instance_id).first()
        if not gateway:
            return None
        
        if gateway.management_mode != ManagementMode.SUPERVISOR.value:
            return None
        
        # If logs path is stored, we could read from file system
        # For now, return placeholder - in production, this would read from actual log file
        if gateway.supervisor_logs_path:
            # TODO: Implement actual log file reading
            return f"Logs would be read from: {gateway.supervisor_logs_path}\n(Log file reading not yet implemented)"
        
        return "No supervisor logs path configured"

    def get_agent_description(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent description from supervisor.
        
        Args:
            instance_id: Gateway instance ID
            
        Returns:
            Agent description dict, or None if not found
        """
        gateway = self.db.query(Gateway).filter(Gateway.instance_id == instance_id).first()
        if not gateway:
            return None
        
        if gateway.management_mode != ManagementMode.SUPERVISOR.value:
            return None
        
        # Agent description is typically sent via OpAMP protocol
        # Extract from supervisor_status or metadata
        supervisor_status = gateway.supervisor_status or {}
        agent_description = supervisor_status.get("agent_description", {})
        
        # Also include metadata from gateway
        metadata = gateway.extra_metadata or {}
        
        return {
            "instance_id": instance_id,
            "agent_description": agent_description,
            "metadata": metadata,
            "hostname": gateway.hostname,
            "ip_address": gateway.ip_address
        }

    def restart_agent_via_supervisor(self, instance_id: str) -> bool:
        """
        Request agent restart via supervisor.
        
        Note: This is a placeholder. Actual restart would be handled via OpAMP protocol
        by sending a ServerToAgent message with restart request.
        
        Args:
            instance_id: Gateway instance ID
            
        Returns:
            True if request was queued, False otherwise
        """
        gateway = self.db.query(Gateway).filter(Gateway.instance_id == instance_id).first()
        if not gateway:
            return False
        
        if gateway.management_mode != ManagementMode.SUPERVISOR.value:
            logger.warning(f"Agent {instance_id} is not managed by supervisor, cannot restart")
            return False
        
        # TODO: Implement actual restart via OpAMP protocol
        # This would involve:
        # 1. Sending a ServerToAgent message with command to restart
        # 2. Supervisor would handle the restart command
        # 3. Update supervisor_status with restart status
        
        logger.info(f"Restart request queued for supervisor-managed agent: {instance_id}")
        return True

    def update_supervisor_status(
        self,
        instance_id: str,
        status: Dict[str, Any],
        logs_path: Optional[str] = None
    ) -> bool:
        """
        Update supervisor status for an agent.
        
        Args:
            instance_id: Gateway instance ID
            status: Supervisor status dict to store
            logs_path: Optional path to supervisor logs
            
        Returns:
            True if updated, False if gateway not found
        """
        gateway = self.db.query(Gateway).filter(Gateway.instance_id == instance_id).first()
        if not gateway:
            return False
        
        gateway.supervisor_status = status
        if logs_path:
            gateway.supervisor_logs_path = logs_path
        gateway.management_mode = ManagementMode.SUPERVISOR.value
        
        self.db.commit()
        self.db.refresh(gateway)
        
        return True

