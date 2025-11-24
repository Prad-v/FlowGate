"""Tests for authentication endpoints"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.core.security import hash_password

client = TestClient(app)


@pytest.fixture
def test_user(db):
    """Create a test user"""
    from app.models.tenant import Organization
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Test Org Auth", slug="test-org-auth", is_active=True)
        db.add(org)
        db.commit()
        db.refresh(org)
    
    user = User(
        email="testauth@example.com",
        username="testuserauth",
        hashed_password=hash_password("testpass123"),
        full_name="Test User Auth",
        is_active=True,
        is_superuser=False,
        org_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


def test_login_success(db, test_user):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "testuserauth", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuserauth"


def test_login_invalid_credentials(db, test_user):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "testuserauth", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_get_current_user_with_token(db, test_user):
    """Test getting current user with valid token"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "testuserauth", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuserauth"
