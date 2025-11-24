"""Tests for SOAR Automation Agent (SAA) Service"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.soar_playbook import SOARPlaybook, PlaybookExecution, PlaybookStatus, PlaybookTriggerType
from app.models.tenant import Organization
from app.services.soar_automation_service import SOARAutomationService


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
def saa_service(db: Session):
    """Create SAA service instance"""
    return SOARAutomationService(db)


@pytest.fixture
def test_playbook(test_org, db):
    """Create a test playbook"""
    import time
    unique_id = str(uuid4())[:8]
    playbook = SOARPlaybook(
        organization_id=test_org.id,
        name=f"Test Playbook {unique_id}",
        description="Test playbook for testing",
        version="1.0.0",
        playbook_yaml="""
        steps:
          - name: step1
            action: log
          - name: step2
            action: notify
        """,
        trigger_type=PlaybookTriggerType.THREAT_ALERT,
        is_enabled=True,
        requires_approval=False
    )
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    yield playbook
    try:
        db.delete(playbook)
        db.commit()
    except Exception:
        db.rollback()


class TestSOARAutomationService:
    """Test suite for SOAR Automation Agent"""

    def test_execute_playbook(self, saa_service, test_org, test_playbook, db):
        """Test executing a playbook"""
        execution = saa_service.execute_playbook(
            org_id=test_org.id,
            playbook_id=test_playbook.id,
            trigger_type=PlaybookTriggerType.THREAT_ALERT,
            trigger_entity_id="alert123"
        )
        
        assert execution.id is not None
        assert execution.playbook_id == test_playbook.id
        assert execution.status in [PlaybookStatus.COMPLETED, PlaybookStatus.FAILED, PlaybookStatus.RUNNING]

    def test_execute_playbook_requires_approval(self, saa_service, test_org, db):
        """Test executing a playbook that requires approval"""
        # Create playbook requiring approval
        unique_id = str(uuid4())[:8]
        playbook = SOARPlaybook(
            organization_id=test_org.id,
            name=f"Approval Required Playbook {unique_id}",
            playbook_yaml="steps: []",
            trigger_type=PlaybookTriggerType.THREAT_ALERT,
            is_enabled=True,
            requires_approval=True
        )
        db.add(playbook)
        db.commit()
        db.refresh(playbook)
        
        # Try to execute without approval (should fail)
        with pytest.raises(ValueError, match="requires approval"):
            saa_service.execute_playbook(
                org_id=test_org.id,
                playbook_id=playbook.id,
                trigger_type=PlaybookTriggerType.THREAT_ALERT
            )
        
        # Execute with approval (should succeed)
        execution = saa_service.execute_playbook(
            org_id=test_org.id,
            playbook_id=playbook.id,
            trigger_type=PlaybookTriggerType.THREAT_ALERT,
            approved_by="approver1"
        )
        
        assert execution.approved_by == "approver1"
        assert execution.approved_at is not None

    def test_get_playbooks(self, saa_service, test_org, db):
        """Test retrieving playbooks"""
        # Create multiple playbooks
        unique_id = str(uuid4())[:8]
        for i in range(3):
            playbook = SOARPlaybook(
                organization_id=test_org.id,
                name=f"Playbook {i} {unique_id}",
                playbook_yaml="steps: []",
                trigger_type=PlaybookTriggerType.THREAT_ALERT,
                is_enabled=True
            )
            db.add(playbook)
        db.commit()
        
        playbooks = saa_service.get_playbooks(org_id=test_org.id)
        assert len(playbooks) >= 3

    def test_get_playbooks_filtered(self, saa_service, test_org, db):
        """Test retrieving playbooks with filter"""
        # Create enabled and disabled playbooks
        unique_id = str(uuid4())[:8]
        enabled = SOARPlaybook(
            organization_id=test_org.id,
            name=f"Enabled Playbook {unique_id}",
            playbook_yaml="steps: []",
            trigger_type=PlaybookTriggerType.THREAT_ALERT,
            is_enabled=True
        )
        disabled = SOARPlaybook(
            organization_id=test_org.id,
            name=f"Disabled Playbook {unique_id}",
            playbook_yaml="steps: []",
            trigger_type=PlaybookTriggerType.THREAT_ALERT,
            is_enabled=False
        )
        db.add(enabled)
        db.add(disabled)
        db.commit()
        
        # Filter enabled only
        enabled_playbooks = saa_service.get_playbooks(
            org_id=test_org.id,
            is_enabled=True
        )
        assert len(enabled_playbooks) >= 1
        assert all(p.is_enabled for p in enabled_playbooks)

    def test_get_executions(self, saa_service, test_org, test_playbook, db):
        """Test retrieving playbook executions"""
        # Create multiple executions
        for i in range(3):
            execution = PlaybookExecution(
                organization_id=test_org.id,
                playbook_id=test_playbook.id,
                status=PlaybookStatus.COMPLETED,
                trigger_type=PlaybookTriggerType.THREAT_ALERT
            )
            db.add(execution)
        db.commit()
        
        executions = saa_service.get_executions(org_id=test_org.id)
        assert len(executions) >= 3

    def test_get_executions_filtered(self, saa_service, test_org, test_playbook, db):
        """Test retrieving executions with filters"""
        # Create executions with different statuses
        completed = PlaybookExecution(
            organization_id=test_org.id,
            playbook_id=test_playbook.id,
            status=PlaybookStatus.COMPLETED,
            trigger_type=PlaybookTriggerType.THREAT_ALERT
        )
        failed = PlaybookExecution(
            organization_id=test_org.id,
            playbook_id=test_playbook.id,
            status=PlaybookStatus.FAILED,
            trigger_type=PlaybookTriggerType.THREAT_ALERT
        )
        db.add(completed)
        db.add(failed)
        db.commit()
        
        # Filter by status
        completed_executions = saa_service.get_executions(
            org_id=test_org.id,
            status=PlaybookStatus.COMPLETED
        )
        assert len(completed_executions) >= 1
        assert all(e.status == PlaybookStatus.COMPLETED for e in completed_executions)

