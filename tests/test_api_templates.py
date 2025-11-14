"""Tests for template API endpoints."""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, engine

# Create test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_create_template():
    """Test creating a template via API."""
    template_data = {
        "name": "Test Template",
        "description": "Test description",
        "template_type": "metric",
        "config_yaml": """
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
processors:
  batch:
exporters:
  logging:
service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]
""",
        "change_summary": "Initial version"
    }
    
    response = client.post("/api/v1/templates", json=template_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Template"
    assert data["template_type"] == "metric"


def test_list_templates():
    """Test listing templates via API."""
    response = client.get("/api/v1/templates")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_validate_template():
    """Test template validation via API."""
    validation_data = {
        "config_yaml": """
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
processors:
  batch:
exporters:
  logging:
service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]
"""
    }
    
    response = client.post("/api/v1/templates/validate", json=validation_data)
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data


