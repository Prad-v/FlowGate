"""Tests for template service and API"""

import pytest
from uuid import uuid4
from app.services.template_service import TemplateService
from app.schemas.template import TemplateCreate, TemplateType


def test_create_template(db_session):
    """Test creating a template"""
    service = TemplateService(db_session)
    org_id = uuid4()
    
    template_data = TemplateCreate(
        name="Test Template",
        description="Test description",
        template_type=TemplateType.METRICS,
        org_id=org_id,
        config_yaml="receivers:\n  otlp:\n    protocols:\n      grpc:\n        endpoint: 0.0.0.0:4317",
    )
    
    template = service.create_template(template_data)
    assert template.name == "Test Template"
    assert template.current_version == 1
    assert template.org_id == org_id


def test_get_template(db_session):
    """Test getting a template"""
    service = TemplateService(db_session)
    org_id = uuid4()
    
    template_data = TemplateCreate(
        name="Test Template",
        description="Test description",
        template_type=TemplateType.METRICS,
        org_id=org_id,
        config_yaml="receivers:\n  otlp:",
    )
    
    created = service.create_template(template_data)
    retrieved = service.get_template(created.id, org_id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Test Template"


def test_create_template_version(db_session):
    """Test creating a template version"""
    service = TemplateService(db_session)
    org_id = uuid4()
    
    template_data = TemplateCreate(
        name="Test Template",
        description="Test description",
        template_type=TemplateType.METRICS,
        org_id=org_id,
        config_yaml="receivers:\n  otlp:",
    )
    
    template = service.create_template(template_data)
    
    from app.schemas.template import TemplateVersionCreate
    version_data = TemplateVersionCreate(
        config_yaml="receivers:\n  otlp:\n    protocols:\n      grpc:",
        description="Updated version",
    )
    
    version = service.create_version(template.id, org_id, version_data)
    assert version is not None
    assert version.version == 2
    assert template.current_version == 2

