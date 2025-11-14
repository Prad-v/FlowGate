"""Tests for validation service"""

import pytest
from app.services.validation_service import ValidationService
from app.schemas.validation import ValidationRequest


def test_validate_valid_config():
    """Test validating a valid OTel config"""
    service = ValidationService()
    
    request = ValidationRequest(
        config_yaml="""
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
processors:
  batch:
exporters:
  otlp:
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp]
"""
    )
    
    response = service.validate_config(request)
    assert response.is_valid is True
    assert len(response.errors) == 0


def test_validate_invalid_yaml():
    """Test validating invalid YAML"""
    service = ValidationService()
    
    request = ValidationRequest(
        config_yaml="invalid: yaml: [unclosed"
    )
    
    response = service.validate_config(request)
    assert response.is_valid is False
    assert len(response.errors) > 0


def test_validate_missing_service():
    """Test validating config missing service section"""
    service = ValidationService()
    
    request = ValidationRequest(
        config_yaml="""
receivers:
  otlp:
processors:
  batch:
exporters:
  otlp:
"""
    )
    
    response = service.validate_config(request)
    assert response.is_valid is False
    assert any("service" in error.lower() for error in response.errors)

