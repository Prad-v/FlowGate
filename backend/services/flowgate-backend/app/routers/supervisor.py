"""OpAMP Supervisor Management Router

Endpoints for managing supervisor-managed agents.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from app.database import get_db
from app.services.opamp_supervisor_service import OpAMPSupervisorService
from app.services.gateway_service import GatewayService
from app.models.gateway import Gateway, ManagementMode
from app.utils.auth import get_current_user_org_id

router = APIRouter(prefix="/supervisor", tags=["supervisor"])


@router.get("/agents", response_model=List[Dict[str, Any]])
async def list_supervisor_agents(
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """List all supervisor-managed agents for an organization."""
    gateway_service = GatewayService(db)
    gateways = gateway_service.get_gateways(org_id)
    
    # Filter to only supervisor-managed agents
    supervisor_agents = [
        g for g in gateways 
        if g.management_mode == ManagementMode.SUPERVISOR.value
    ]
    
    return [
        {
            "instance_id": agent.instance_id,
            "gateway_id": str(agent.id),
            "name": agent.name,
            "management_mode": agent.management_mode,
            "opamp_connection_status": agent.opamp_connection_status,
            "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
            "supervisor_status": agent.supervisor_status,
        }
        for agent in supervisor_agents
    ]


@router.get("/agents/{instance_id}/status", response_model=Dict[str, Any])
async def get_supervisor_status(
    instance_id: str,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get supervisor status for a specific agent."""
    # Verify agent belongs to organization
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    supervisor_service = OpAMPSupervisorService(db)
    status_info = supervisor_service.get_supervisor_status(instance_id)
    
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supervisor status not available"
        )
    
    return status_info


@router.get("/agents/{instance_id}/logs")
async def get_supervisor_logs(
    instance_id: str,
    lines: int = 100,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get supervisor logs for a specific agent."""
    # Verify agent belongs to organization
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    supervisor_service = OpAMPSupervisorService(db)
    logs = supervisor_service.get_supervisor_logs(instance_id, lines)
    
    if logs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supervisor logs not available"
        )
    
    return {"instance_id": instance_id, "logs": logs}


@router.post("/agents/{instance_id}/restart", response_model=Dict[str, str])
async def restart_agent_via_supervisor(
    instance_id: str,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Restart an agent via supervisor."""
    # Verify agent belongs to organization
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    supervisor_service = OpAMPSupervisorService(db)
    success = supervisor_service.restart_agent_via_supervisor(instance_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to restart agent. Agent may not be supervisor-managed or not connected."
        )
    
    return {
        "message": "Restart request queued",
        "instance_id": instance_id
    }


@router.get("/agents/{instance_id}/description", response_model=Dict[str, Any])
async def get_agent_description(
    instance_id: str,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get agent description from supervisor."""
    # Verify agent belongs to organization
    gateway = db.query(Gateway).filter(
        Gateway.instance_id == instance_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with instance_id {instance_id} not found"
        )
    
    supervisor_service = OpAMPSupervisorService(db)
    description = supervisor_service.get_agent_description(instance_id)
    
    if description is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent description not available. Agent may not be supervisor-managed."
        )
    
    return description

