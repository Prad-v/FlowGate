"""Correlation & RCA Agent (CRA) API router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.database import get_db
from app.utils.auth import get_current_user_org_id
from app.models.incident import IncidentStatus
from app.services.correlation_rca_service import CorrelationRCAService

router = APIRouter(prefix="/correlation-rca", tags=["Correlation & RCA"])


class CorrelateIncidentRequest(BaseModel):
    alert_ids: List[UUID] = Field(..., description="List of alert IDs to correlate")
    time_window_minutes: int = Field(60, description="Time window for correlation")


@router.post("/incidents/correlate")
async def correlate_incident(
    request: CorrelateIncidentRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Correlate multiple alerts into an incident"""
    service = CorrelationRCAService(db)
    try:
        incident = service.correlate_incident(
            org_id=org_id,
            alert_ids=request.alert_ids,
            time_window_minutes=request.time_window_minutes
        )
        return {"success": True, "incident_id": incident.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/incidents")
async def list_incidents(
    status: Optional[IncidentStatus] = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """List incidents for the organization"""
    service = CorrelationRCAService(db)
    incidents = service.get_incidents(org_id=org_id, status=status)
    return incidents

