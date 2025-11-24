"""Tests for Correlation & RCA Agent (CRA) Service"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.threat_alert import ThreatAlert, ThreatSeverity, ThreatStatus
from app.models.tenant import Organization
from app.services.correlation_rca_service import CorrelationRCAService
from unittest.mock import Mock, patch


@pytest.fixture
def test_org(db: Session):
    """Create a test organization"""
    import time
    unique_id = str(uuid4())[:8]
    org = Organization(
        id=uuid4(),
        name=f"Test Org {unique_id}",
        slug=f"test-org-{unique_id}",
        is_active=True
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    yield org
    try:
        db.delete(org)
        db.commit()
    except Exception:
        db.rollback()


@pytest.fixture
def cra_service(db: Session):
    """Create CRA service instance"""
    with patch('app.services.correlation_rca_service.get_neo4j_client') as mock_neo4j:
        mock_client = Mock()
        mock_neo4j.return_value = mock_client
        
        service = CorrelationRCAService(db)
        return service


class TestCorrelationRCAService:
    """Test suite for Correlation & RCA Agent"""

    def test_correlate_incident(self, cra_service, test_org, db):
        """Test correlating multiple alerts into an incident"""
        # Create test alerts
        alert_ids = []
        for i in range(3):
            alert = ThreatAlert(
                organization_id=test_org.id,
                title=f"Test Alert {i}",
                severity=ThreatSeverity.MEDIUM,
                status=ThreatStatus.NEW,
                source_type="identity",
                confidence_score=0.7,
                detected_at=datetime.utcnow()
            )
            db.add(alert)
            db.flush()
            alert_ids.append(alert.id)
        db.commit()
        
        # Correlate them
        incident = cra_service.correlate_incident(
            org_id=test_org.id,
            alert_ids=alert_ids,
            time_window_minutes=60
        )
        
        assert incident.id is not None
        assert incident.organization_id == test_org.id
        assert len(incident.correlated_alerts) == 3
        assert incident.root_cause is not None

    def test_correlate_incident_severity(self, cra_service, test_org, db):
        """Test that incident severity matches highest alert severity"""
        # Create alerts with different severities
        alert_ids = []
        for severity in [ThreatSeverity.LOW, ThreatSeverity.HIGH]:
            alert = ThreatAlert(
                organization_id=test_org.id,
                title=f"Alert {severity.value}",
                severity=severity,
                status=ThreatStatus.NEW,
                source_type="identity",
                confidence_score=0.7,
                detected_at=datetime.utcnow()
            )
            db.add(alert)
            db.flush()
            alert_ids.append(alert.id)
        db.commit()
        
        incident = cra_service.correlate_incident(
            org_id=test_org.id,
            alert_ids=alert_ids
        )
        
        # Should have HIGH severity (highest from alerts)
        assert incident.severity == IncidentSeverity.HIGH

    def test_get_incidents(self, cra_service, test_org, db):
        """Test retrieving incidents"""
        # Create test incidents
        for i in range(3):
            incident = Incident(
                organization_id=test_org.id,
                title=f"Test Incident {i}",
                severity=IncidentSeverity.MEDIUM,
                status=IncidentStatus.NEW,
                detected_at=datetime.utcnow()
            )
            db.add(incident)
        db.commit()
        
        incidents = cra_service.get_incidents(org_id=test_org.id)
        assert len(incidents) >= 3

    def test_get_incidents_filtered(self, cra_service, test_org, db):
        """Test retrieving incidents with status filter"""
        # Create incidents with different statuses
        incident_new = Incident(
            organization_id=test_org.id,
            title="New Incident",
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.NEW,
            detected_at=datetime.utcnow()
        )
        incident_resolved = Incident(
            organization_id=test_org.id,
            title="Resolved Incident",
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.RESOLVED,
            detected_at=datetime.utcnow()
        )
        db.add(incident_new)
        db.add(incident_resolved)
        db.commit()
        
        # Filter by status
        new_incidents = cra_service.get_incidents(
            org_id=test_org.id,
            status=IncidentStatus.NEW
        )
        assert len(new_incidents) >= 1
        assert all(i.status == IncidentStatus.NEW for i in new_incidents)

