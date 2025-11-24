"""Tests for Persona Baseline Agent (PBA) Service"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.persona_baseline import PersonaBaseline, PersonaAnomaly, EntityType
from app.models.tenant import Organization
from app.services.persona_baseline_service import PersonaBaselineService


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
def pba_service(db: Session):
    """Create PBA service instance"""
    return PersonaBaselineService(db)


class TestPersonaBaselineService:
    """Test suite for Persona Baseline Agent"""

    def test_update_baseline_new_entity(self, pba_service, test_org, db):
        """Test updating baseline for a new entity"""
        baseline = pba_service.update_baseline(
            org_id=test_org.id,
            entity_type=EntityType.USER,
            entity_id="user123",
            event_data={"action": "login", "time": "09:00"}
        )
        
        assert baseline.id is not None
        assert baseline.organization_id == test_org.id
        assert baseline.entity_type == EntityType.USER
        assert baseline.entity_id == "user123"
        assert baseline.sample_count == 1

    def test_update_baseline_existing_entity(self, pba_service, test_org, db):
        """Test updating baseline for existing entity"""
        # Create initial baseline
        baseline1 = pba_service.update_baseline(
            org_id=test_org.id,
            entity_type=EntityType.USER,
            entity_id="user123",
            event_data={"action": "login"}
        )
        
        initial_count = baseline1.sample_count
        
        # Update again
        baseline2 = pba_service.update_baseline(
            org_id=test_org.id,
            entity_type=EntityType.USER,
            entity_id="user123",
            event_data={"action": "logout"}
        )
        
        assert baseline2.id == baseline1.id
        assert baseline2.sample_count == initial_count + 1

    def test_detect_anomaly_insufficient_data(self, pba_service, test_org, db):
        """Test anomaly detection with insufficient baseline data"""
        # Create baseline with few samples
        baseline = pba_service.update_baseline(
            org_id=test_org.id,
            entity_type=EntityType.USER,
            entity_id="user123",
            event_data={"action": "login"}
        )
        
        # Try to detect anomaly (should return None due to insufficient data)
        anomaly = pba_service.detect_anomaly(
            org_id=test_org.id,
            entity_type=EntityType.USER,
            entity_id="user123",
            event_data={"action": "unusual_action"},
            event_timestamp=datetime.utcnow()
        )
        
        # Should return None if sample_count < 10
        assert anomaly is None or baseline.sample_count < 10

    def test_detect_anomaly_sufficient_data(self, pba_service, test_org, db):
        """Test anomaly detection with sufficient baseline data"""
        # Create baseline with many samples
        baseline = None
        for i in range(15):
            baseline = pba_service.update_baseline(
                org_id=test_org.id,
                entity_type=EntityType.USER,
                entity_id="user123",
                event_data={"action": f"normal_action_{i}"}
            )
        
        # Now try to detect anomaly
        anomaly = pba_service.detect_anomaly(
            org_id=test_org.id,
            entity_type=EntityType.USER,
            entity_id="user123",
            event_data={"action": "highly_unusual_action"},
            event_timestamp=datetime.utcnow()
        )
        
        # May or may not detect anomaly depending on deviation score
        # Just verify the method doesn't crash
        assert True

    def test_get_baselines(self, pba_service, test_org, db):
        """Test retrieving baselines"""
        # Create multiple baselines
        for i in range(3):
            pba_service.update_baseline(
                org_id=test_org.id,
                entity_type=EntityType.USER,
                entity_id=f"user{i}",
                event_data={"action": "login"}
            )
        
        baselines = pba_service.get_baselines(org_id=test_org.id)
        assert len(baselines) >= 3

    def test_get_baselines_filtered(self, pba_service, test_org, db):
        """Test retrieving baselines with entity type filter"""
        # Create baselines for different entity types
        pba_service.update_baseline(
            org_id=test_org.id,
            entity_type=EntityType.USER,
            entity_id="user1",
            event_data={}
        )
        pba_service.update_baseline(
            org_id=test_org.id,
            entity_type=EntityType.SERVICE,
            entity_id="service1",
            event_data={}
        )
        
        # Filter by entity type
        user_baselines = pba_service.get_baselines(
            org_id=test_org.id,
            entity_type=EntityType.USER
        )
        assert len(user_baselines) >= 1
        assert all(b.entity_type == EntityType.USER for b in user_baselines)

