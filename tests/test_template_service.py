"""Tests for template service."""
import pytest
from uuid import uuid4
from services.template import TemplateService
from schemas.template import TemplateCreate


def test_create_template(db, test_org_id, sample_template_config):
    """Test template creation."""
    service = TemplateService(db)
    
    template_data = TemplateCreate(
        name="Test Template",
        description="Test description",
        template_type="metric",
        config_yaml=sample_template_config,
        change_summary="Initial version"
    )
    
    template = service.create_template(test_org_id, template_data)
    
    assert template.id is not None
    assert template.name == "Test Template"
    assert template.template_type == "metric"
    assert template.current_version == 1


def test_get_template(db, test_org_id, sample_template_config):
    """Test getting a template."""
    service = TemplateService(db)
    
    template_data = TemplateCreate(
        name="Test Template",
        template_type="metric",
        config_yaml=sample_template_config
    )
    
    template = service.create_template(test_org_id, template_data)
    retrieved = service.get_template(template.id, test_org_id)
    
    assert retrieved is not None
    assert retrieved.id == template.id
    assert retrieved.name == "Test Template"


def test_get_templates(db, test_org_id, sample_template_config):
    """Test listing templates."""
    service = TemplateService(db)
    
    # Create multiple templates
    for i in range(3):
        template_data = TemplateCreate(
            name=f"Template {i}",
            template_type="metric",
            config_yaml=sample_template_config
        )
        service.create_template(test_org_id, template_data)
    
    templates = service.get_templates(test_org_id)
    assert len(templates) == 3


def test_update_template(db, test_org_id, sample_template_config):
    """Test updating a template."""
    service = TemplateService(db)
    
    template_data = TemplateCreate(
        name="Test Template",
        template_type="metric",
        config_yaml=sample_template_config
    )
    
    template = service.create_template(test_org_id, template_data)
    
    from schemas.template import TemplateUpdate
    update_data = TemplateUpdate(name="Updated Template")
    updated = service.update_template(template.id, test_org_id, update_data)
    
    assert updated is not None
    assert updated.name == "Updated Template"


def test_delete_template(db, test_org_id, sample_template_config):
    """Test deleting a template."""
    service = TemplateService(db)
    
    template_data = TemplateCreate(
        name="Test Template",
        template_type="metric",
        config_yaml=sample_template_config
    )
    
    template = service.create_template(test_org_id, template_data)
    success = service.delete_template(template.id, test_org_id)
    
    assert success is True
    
    retrieved = service.get_template(template.id, test_org_id)
    assert retrieved is None


