"""Persona Baseline Agent (PBA) API router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.utils.auth import get_current_user_org_id
from app.models.persona_baseline import EntityType
from app.services.persona_baseline_service import PersonaBaselineService

router = APIRouter(prefix="/persona-baseline", tags=["Persona Baseline"])


@router.get("/baselines")
async def list_baselines(
    entity_type: Optional[EntityType] = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """List persona baselines for the organization"""
    service = PersonaBaselineService(db)
    baselines = service.get_baselines(org_id=org_id, entity_type=entity_type)
    return baselines

