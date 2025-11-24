"""Correlation & RCA Agent (CRA) Service

Handles cross-log correlation, attack timeline reconstruction, and root cause analysis.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import UUID
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.threat_alert import ThreatAlert, ThreatStatus
from app.core.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)


class CorrelationRCAService:
    """Correlation & RCA Agent service"""

    def __init__(self, db: Session):
        self.db = db
        self.neo4j_client = get_neo4j_client()

    def correlate_incident(
        self,
        org_id: UUID,
        alert_ids: List[UUID],
        time_window_minutes: int = 60
    ) -> Incident:
        """Correlate multiple alerts into an incident"""
        # Get alerts
        alerts = self.db.query(ThreatAlert).filter(
            ThreatAlert.id.in_(alert_ids),
            ThreatAlert.organization_id == org_id
        ).all()
        
        if not alerts:
            raise ValueError("No alerts found for correlation")
        
        # Determine severity (highest from alerts)
        # Severity order: low < medium < high < critical
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        max_severity = max((alert.severity for alert in alerts), key=lambda s: severity_order.get(s.value, 0))
        
        # Build timeline
        timeline = self._build_timeline(alerts, time_window_minutes)
        
        # Find root cause
        root_cause, root_cause_confidence = self._identify_root_cause(alerts, timeline)
        
        # Estimate blast radius
        blast_radius = self._estimate_blast_radius(alerts)
        
        # Create incident
        incident = Incident(
            organization_id=org_id,
            title=f"Security Incident: {len(alerts)} correlated alerts",
            description=f"Correlated {len(alerts)} threat alerts",
            severity=max_severity,
            status=IncidentStatus.NEW,
            detected_at=datetime.utcnow(),
            started_at=timeline[0]["timestamp"] if timeline else datetime.utcnow(),
            root_cause=root_cause,
            root_cause_confidence=root_cause_confidence,
            correlated_alerts=alert_ids,
            timeline=timeline,
            blast_radius=blast_radius
        )
        
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        
        # Update alerts to link to incident
        for alert in alerts:
            alert.incident_id = incident.id
            if alert.status == ThreatStatus.NEW:
                alert.status = ThreatStatus.INVESTIGATING
        
        self.db.commit()
        
        return incident

    def _build_timeline(
        self,
        alerts: List[ThreatAlert],
        time_window_minutes: int
    ) -> List[Dict[str, Any]]:
        """Build event timeline from alerts"""
        timeline = []
        
        for alert in sorted(alerts, key=lambda a: a.detected_at):
            timeline.append({
                "timestamp": alert.detected_at.isoformat(),
                "event_type": "threat_alert",
                "alert_id": str(alert.id),
                "title": alert.title,
                "severity": alert.severity.value,
                "source_type": alert.source_type,
                "mitre_technique": alert.mitre_technique_id
            })
        
        return timeline

    def _identify_root_cause(
        self,
        alerts: List[ThreatAlert],
        timeline: List[Dict[str, Any]]
    ) -> tuple[Optional[str], Optional[float]]:
        """Identify root cause from alerts and timeline"""
        if not alerts:
            return None, None
        
        # Simple heuristic: first alert is likely root cause
        first_alert = alerts[0]
        root_cause = f"Initial threat detected: {first_alert.title}"
        
        # Confidence based on number of correlated alerts
        confidence = min(0.9, 0.5 + (len(alerts) * 0.1))
        
        return root_cause, confidence

    def _estimate_blast_radius(
        self,
        alerts: List[ThreatAlert]
    ) -> Dict[str, Any]:
        """Estimate blast radius of incident"""
        affected_entities = set()
        affected_source_types = set()
        
        for alert in alerts:
            if alert.source_entity:
                affected_entities.add(alert.source_entity)
            affected_source_types.add(alert.source_type)
        
        return {
            "affected_entities": list(affected_entities),
            "affected_source_types": list(affected_source_types),
            "alert_count": len(alerts),
            "estimated_impact": "medium" if len(affected_entities) < 5 else "high"
        }

    def get_incidents(
        self,
        org_id: UUID,
        status: Optional[IncidentStatus] = None,
        limit: int = 100
    ) -> List[Incident]:
        """Get incidents for an organization"""
        query = self.db.query(Incident).filter(
            Incident.organization_id == org_id
        )
        
        if status:
            query = query.filter(Incident.status == status)
        
        return query.order_by(Incident.detected_at.desc()).limit(limit).all()

