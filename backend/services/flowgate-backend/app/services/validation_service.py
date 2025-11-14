"""Validation service for OTel configs"""

from typing import Dict, Any, List
import yaml
import json
from app.schemas.validation import ValidationRequest, ValidationResponse


class ValidationService:
    """Service for validating OTel collector configurations"""

    def validate_config(self, request: ValidationRequest) -> ValidationResponse:
        """Validate OTel collector config"""
        errors: List[str] = []
        warnings: List[str] = []
        output_preview: Dict[str, Any] | None = None

        # Parse YAML
        try:
            config_dict = yaml.safe_load(request.config_yaml)
            if not config_dict:
                errors.append("Config is empty")
                return ValidationResponse(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                )
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax: {str(e)}")
            return ValidationResponse(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )

        # Basic structure validation
        required_sections = ["receivers", "processors", "exporters", "service"]
        for section in required_sections:
            if section not in config_dict:
                warnings.append(f"Missing optional section: {section}")

        # Validate service section (required)
        if "service" not in config_dict:
            errors.append("Missing required 'service' section")
        else:
            service = config_dict["service"]
            if "pipelines" not in service:
                errors.append("Missing 'pipelines' in service section")

        # If sample data provided, attempt dry-run
        if request.sample_data:
            try:
                # This is a placeholder - in production, would use actual OTel collector
                # to process sample data
                output_preview = {
                    "processed": True,
                    "sample_output": "Dry-run preview (placeholder)",
                }
            except Exception as e:
                warnings.append(f"Dry-run failed: {str(e)}")

        is_valid = len(errors) == 0

        return ValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            output_preview=output_preview,
            message="Validation completed" if is_valid else "Validation failed",
        )

