"""Tests for validation service."""
import pytest
from services.validation import ValidationService
from schemas.template import TemplateValidationRequest


def test_validate_valid_config():
    """Test validation of a valid config."""
    service = ValidationService()
    
    valid_config = """
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
    
    request = TemplateValidationRequest(config_yaml=valid_config)
    result = service.validate_config(request)
    
    assert result.valid is True
    assert len(result.errors) == 0


def test_validate_invalid_yaml():
    """Test validation of invalid YAML."""
    service = ValidationService()
    
    invalid_config = "invalid: yaml: ["
    
    request = TemplateValidationRequest(config_yaml=invalid_config)
    result = service.validate_config(request)
    
    assert result.valid is False
    assert len(result.errors) > 0


def test_validate_empty_config():
    """Test validation of empty config."""
    service = ValidationService()
    
    request = TemplateValidationRequest(config_yaml="")
    result = service.validate_config(request)
    
    assert result.valid is False
    assert len(result.errors) > 0


