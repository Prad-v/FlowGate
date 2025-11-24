"""Threat Vector Agent (TVA) API router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.database import get_db
from app.utils.auth import get_current_user_org_id
from app.models.threat_alert import ThreatSeverity, ThreatStatus
from app.services.threat_vector_service import ThreatVectorService

router = APIRouter(prefix="/threat-vector", tags=["Threat Vector"])


class ThreatAlertResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    severity: str
    status: str
    mitre_technique_id: Optional[str]
    mitre_technique_name: Optional[str]
    mitre_tactic: Optional[str]
    source_type: str
    source_entity: Optional[str]
    confidence_score: float
    anomaly_score: Optional[float]
    detected_at: str

    class Config:
        from_attributes = True


@router.get("/alerts", response_model=List[ThreatAlertResponse])
async def list_threat_alerts(
    status: Optional[ThreatStatus] = None,
    severity: Optional[ThreatSeverity] = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """List threat alerts for the organization"""
    service = ThreatVectorService(db)
    alerts = service.get_threat_alerts(org_id=org_id, status=status, severity=severity)
    
    return [
        ThreatAlertResponse(
            id=alert.id,
            title=alert.title,
            description=alert.description,
            severity=alert.severity.value,
            status=alert.status.value,
            mitre_technique_id=alert.mitre_technique_id,
            mitre_technique_name=alert.mitre_technique_name,
            mitre_tactic=alert.mitre_tactic,
            source_type=alert.source_type,
            source_entity=alert.source_entity,
            confidence_score=alert.confidence_score,
            anomaly_score=alert.anomaly_score,
            detected_at=alert.detected_at.isoformat()
        )
        for alert in alerts
    ]


@router.get("/alerts/{alert_id}", response_model=ThreatAlertResponse)
async def get_threat_alert(
    alert_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get a specific threat alert"""
    from app.models.threat_alert import ThreatAlert
    alert = db.query(ThreatAlert).filter(
        ThreatAlert.id == alert_id,
        ThreatAlert.organization_id == org_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat alert not found")
    
    return ThreatAlertResponse(
        id=alert.id,
        title=alert.title,
        description=alert.description,
        severity=alert.severity.value,
        status=alert.status.value,
        mitre_technique_id=alert.mitre_technique_id,
        mitre_technique_name=alert.mitre_technique_name,
        mitre_tactic=alert.mitre_tactic,
        source_type=alert.source_type,
        source_entity=alert.source_entity,
        confidence_score=alert.confidence_score,
        anomaly_score=alert.anomaly_score,
        detected_at=alert.detected_at.isoformat()
    )

