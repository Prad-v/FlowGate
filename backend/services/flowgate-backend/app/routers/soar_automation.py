"""SOAR Automation Agent (SAA) API router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.database import get_db
from app.utils.auth import get_current_user_org_id
from app.models.soar_playbook import PlaybookTriggerType, PlaybookStatus
from app.services.soar_automation_service import SOARAutomationService

router = APIRouter(prefix="/soar-automation", tags=["SOAR Automation"])


class ExecutePlaybookRequest(BaseModel):
    playbook_id: UUID
    trigger_type: PlaybookTriggerType
    trigger_entity_id: Optional[str] = None
    trigger_entity_type: Optional[str] = None
    approved_by: Optional[str] = None


@router.post("/playbooks/execute")
async def execute_playbook(
    request: ExecutePlaybookRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Execute a SOAR playbook"""
    service = SOARAutomationService(db)
    try:
        execution = service.execute_playbook(
            org_id=org_id,
            playbook_id=request.playbook_id,
            trigger_type=request.trigger_type,
            trigger_entity_id=request.trigger_entity_id,
            trigger_entity_type=request.trigger_entity_type,
            approved_by=request.approved_by
        )
        return {"success": True, "execution_id": execution.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/playbooks")
async def list_playbooks(
    is_enabled: Optional[bool] = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """List SOAR playbooks"""
    service = SOARAutomationService(db)
    playbooks = service.get_playbooks(org_id=org_id, is_enabled=is_enabled)
    return playbooks


@router.get("/executions")
async def list_executions(
    playbook_id: Optional[UUID] = None,
    status: Optional[PlaybookStatus] = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """List playbook executions"""
    service = SOARAutomationService(db)
    executions = service.get_executions(
        org_id=org_id,
        playbook_id=playbook_id,
        status=status
    )
    return executions

