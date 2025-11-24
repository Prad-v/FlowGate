"""Tests for Threat Vector Agent (TVA) Service"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.threat_alert import ThreatAlert, ThreatSeverity, ThreatStatus
from app.models.tenant import Organization
from app.services.threat_vector_service import ThreatVectorService
from unittest.mock import Mock, patch, AsyncMock


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
def tva_service(db: Session):
    """Create TVA service instance"""
    with patch('app.services.threat_vector_service.ThreatIntelService') as mock_intel:
        mock_intel_instance = Mock()
        mock_intel_instance.get_mitre_framework.return_value = {
            "tactics": ["Execution", "Persistence"],
            "techniques": {
                "T1055": {
                    "id": "T1055",
                    "name": "Process Injection",
                    "tactics": ["Defense Evasion"],
                    "description": "Adversaries may inject code into processes"
                }
            }
        }
        mock_intel.return_value = mock_intel_instance
        
        service = ThreatVectorService(db)
        return service


class TestThreatVectorService:
    """Test suite for Threat Vector Agent"""

    @pytest.mark.asyncio
    async def test_analyze_log_no_threat(self, tva_service, test_org):
        """Test log analysis with no threat detected"""
        alert = await tva_service.analyze_log(
            org_id=str(test_org.id),
            source_type="identity",
            log_data="Normal user login event",
            metadata={}
        )
        
        # Should return None for normal logs
        assert alert is None

    @pytest.mark.asyncio
    async def test_analyze_log_threat_detected(self, tva_service, test_org):
        """Test log analysis with threat detected"""
        alert = await tva_service.analyze_log(
            org_id=str(test_org.id),
            source_type="identity",
            log_data="Process injection detected: dll injection attempt",
            metadata={"entity_id": "user123"}
        )
        
        assert alert is not None
        assert alert.organization_id == test_org.id
        assert alert.severity in [ThreatSeverity.LOW, ThreatSeverity.MEDIUM, ThreatSeverity.HIGH, ThreatSeverity.CRITICAL]
        assert alert.status == ThreatStatus.NEW

    @pytest.mark.asyncio
    async def test_analyze_log_mitre_mapping(self, tva_service, test_org):
        """Test MITRE ATT&CK TTP mapping"""
        alert = await tva_service.analyze_log(
            org_id=str(test_org.id),
            source_type="endpoint",
            log_data="Process injection detected: dll injection attempt",
            metadata={}
        )
        
        if alert:
            # Should have MITRE technique if pattern matches
            assert alert.mitre_technique_id is not None or alert.anomaly_score > 0.7

    def test_get_threat_alerts(self, tva_service, test_org, db):
        """Test retrieving threat alerts"""
        # Create some test alerts
        for i in range(3):
            alert = ThreatAlert(
                organization_id=test_org.id,
                title=f"Test Threat {i}",
                description=f"Test threat description {i}",
                severity=ThreatSeverity.MEDIUM,
                status=ThreatStatus.NEW,
                source_type="identity",
                confidence_score=0.8,
                detected_at=datetime.utcnow()
            )
            db.add(alert)
        db.commit()
        
        alerts = tva_service.get_threat_alerts(org_id=test_org.id)
        assert len(alerts) >= 3

    def test_get_threat_alerts_filtered(self, tva_service, test_org, db):
        """Test retrieving threat alerts with filters"""
        # Create alerts with different severities
        alert_high = ThreatAlert(
            organization_id=test_org.id,
            title="High Severity Threat",
            severity=ThreatSeverity.HIGH,
            status=ThreatStatus.NEW,
            source_type="identity",
            confidence_score=0.9,
            detected_at=datetime.utcnow()
        )
        alert_low = ThreatAlert(
            organization_id=test_org.id,
            title="Low Severity Threat",
            severity=ThreatSeverity.LOW,
            status=ThreatStatus.NEW,
            source_type="identity",
            confidence_score=0.5,
            detected_at=datetime.utcnow()
        )
        db.add(alert_high)
        db.add(alert_low)
        db.commit()
        
        # Filter by severity
        high_alerts = tva_service.get_threat_alerts(
            org_id=test_org.id,
            severity=ThreatSeverity.HIGH
        )
        assert len(high_alerts) >= 1
        assert all(a.severity == ThreatSeverity.HIGH for a in high_alerts)

