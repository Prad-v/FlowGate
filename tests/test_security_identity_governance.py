"""Tests for Identity Governance Agent (IGA) Service"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.access_request import AccessRequest, AccessRequestStatus, AccessRequestType
# Note: Enum values are lowercase in database
from app.models.tenant import Organization
from app.services.identity_governance_service import IdentityGovernanceService
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
    # Cleanup
    try:
        db.delete(org)
        db.commit()
    except Exception:
        db.rollback()


@pytest.fixture
def iga_service(db: Session):
    """Create IGA service instance"""
    with patch('app.services.identity_governance_service.get_neo4j_client') as mock_neo4j:
        mock_client = Mock()
        mock_client.get_user_roles.return_value = [
            {"role_id": "role1", "role_name": "Developer", "privilege_level": 5}
        ]
        mock_client.get_resource_permissions.return_value = [
            {"role_id": "role1", "role_name": "Developer", "privilege_level": 5}
        ]
        mock_client.find_access_paths.return_value = [
            {"path": "mock_path", "depth": 2}
        ]
        mock_neo4j.return_value = mock_client
        
        service = IdentityGovernanceService(db)
        return service


class TestIdentityGovernanceService:
    """Test suite for Identity Governance Agent"""

    def test_evaluate_access_request_low_risk(self, iga_service, test_org, db):
        """Test access request evaluation with low risk"""
        evaluation = iga_service.evaluate_access_request(
            org_id=test_org.id,
            requester_id="user123",
            resource_id="resource456",
            resource_type="server",
            requested_duration_minutes=60
        )
        
        assert "risk_score" in evaluation
        assert "risk_factors" in evaluation
        assert "role_drift_detected" in evaluation
        assert isinstance(evaluation["risk_score"], float)
        assert 0.0 <= evaluation["risk_score"] <= 1.0

    def test_evaluate_access_request_high_risk(self, iga_service, test_org, db):
        """Test access request evaluation with high risk factors"""
        # Mock high privilege role
        iga_service.neo4j_client.get_user_roles.return_value = [
            {"role_id": "admin", "role_name": "Administrator", "privilege_level": 10}
        ]
        
        evaluation = iga_service.evaluate_access_request(
            org_id=test_org.id,
            requester_id="admin_user",
            resource_id="production_db",
            resource_type="database",
            requested_duration_minutes=1440  # 24 hours
        )
        
        assert evaluation["risk_score"] > 0.3  # Should be higher risk

    def test_create_access_request(self, iga_service, test_org, db):
        """Test creating an access request"""
        access_request = iga_service.create_access_request(
            org_id=test_org.id,
            requester_id="user123",
            resource_id="resource456",
            resource_type="server",
            request_type=AccessRequestType.JITA,  # Enum value is "jita" (lowercase)
            requested_duration_minutes=60,
            justification="Need access for maintenance"
        )
        
        assert access_request.id is not None
        assert access_request.organization_id == test_org.id
        assert access_request.requester_id == "user123"
        assert access_request.status == AccessRequestStatus.PENDING
        assert access_request.risk_score is not None

    def test_approve_access_request(self, iga_service, test_org, db):
        """Test approving an access request"""
        # Create request first
        access_request = iga_service.create_access_request(
            org_id=test_org.id,
            requester_id="user123",
            resource_id="resource456",
            resource_type="server",
            request_type=AccessRequestType.JITA
        )
        
        # Approve it
        approved = iga_service.approve_access_request(
            request_id=access_request.id,
            approver_id="approver1",
            approved_duration_minutes=30,
            rationale="Approved for maintenance"
        )
        
        assert approved.status == AccessRequestStatus.APPROVED
        assert approved.approver_id == "approver1"
        assert approved.access_token is not None

    def test_deny_access_request(self, iga_service, test_org, db):
        """Test denying an access request"""
        # Create request first
        access_request = iga_service.create_access_request(
            org_id=test_org.id,
            requester_id="user123",
            resource_id="resource456",
            resource_type="server",
            request_type=AccessRequestType.JITA
        )
        
        # Deny it
        denied = iga_service.deny_access_request(
            request_id=access_request.id,
            approver_id="approver1",
            rationale="Access denied - security policy"
        )
        
        assert denied.status == AccessRequestStatus.DENIED
        assert denied.approver_id == "approver1"

    def test_get_access_requests(self, iga_service, test_org, db):
        """Test retrieving access requests"""
        # Create multiple requests
        for i in range(3):
            iga_service.create_access_request(
                org_id=test_org.id,
                requester_id=f"user{i}",
                resource_id=f"resource{i}",
                resource_type="server",
                request_type=AccessRequestType.JITA
            )
        
        requests = iga_service.get_access_requests(org_id=test_org.id)
        assert len(requests) >= 3

    def test_role_drift_detection(self, iga_service, test_org, db):
        """Test role drift detection"""
        # Mock user with many roles (role drift)
        iga_service.neo4j_client.get_user_roles.return_value = [
            {"role_id": f"role{i}", "role_name": f"Role{i}", "privilege_level": i}
            for i in range(10)  # More than 5 roles
        ]
        
        evaluation = iga_service.evaluate_access_request(
            org_id=test_org.id,
            requester_id="user_with_many_roles",
            resource_id="resource1",
            resource_type="server"
        )
        
        assert evaluation["role_drift_detected"] is True

