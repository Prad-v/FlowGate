"""Validation service for OTel configs."""
from typing import List, Optional, Dict, Any
from schemas.template import TemplateValidationRequest, TemplateValidationResponse
import yaml
import json


class ValidationService:
    """Service for validating OTel collector configurations."""
    
    def validate_config(
        self,
        request: TemplateValidationRequest
    ) -> TemplateValidationResponse:
        """Validate OTel collector configuration."""
        errors: List[str] = []
        warnings: List[str] = []
        preview_output: Optional[Dict[str, Any]] = None
        
        # Parse YAML
        try:
            config_dict = yaml.safe_load(request.config_yaml)
            if not config_dict:
                errors.append("Configuration is empty")
                return TemplateValidationResponse(
                    valid=False,
                    errors=errors,
                    warnings=warnings
                )
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax: {str(e)}")
            return TemplateValidationResponse(
                valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # Basic structure validation
        required_sections = ["receivers", "processors", "exporters", "service"]
        for section in required_sections:
            if section not in config_dict:
                warnings.append(f"Missing section: {section}")
        
        # Validate service.pipelines structure
        if "service" in config_dict:
            service = config_dict["service"]
            if "pipelines" not in service:
                warnings.append("No pipelines defined in service section")
            else:
                pipelines = service["pipelines"]
                for pipeline_name, pipeline_config in pipelines.items():
                    if not isinstance(pipeline_config, dict):
                        errors.append(f"Pipeline '{pipeline_name}' must be a dictionary")
                    else:
                        required_pipeline_keys = ["receivers", "processors", "exporters"]
                        for key in required_pipeline_keys:
                            if key not in pipeline_config:
                                warnings.append(f"Pipeline '{pipeline_name}' missing '{key}'")
        
        # If sample data provided, attempt to simulate transformation
        if request.sample_metrics or request.sample_logs:
            preview_output = self._simulate_transformation(
                config_dict,
                request.sample_metrics,
                request.sample_logs
            )
        
        valid = len(errors) == 0
        
        return TemplateValidationResponse(
            valid=valid,
            errors=errors,
            warnings=warnings,
            preview_output=preview_output
        )
    
    def _simulate_transformation(
        self,
        config: Dict[str, Any],
        sample_metrics: Optional[List[Dict[str, Any]]],
        sample_logs: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Simulate transformation on sample data (simplified)."""
        # This is a placeholder - in production, this would use actual OTel collector
        # or a sandbox environment
        preview = {
            "metrics_processed": len(sample_metrics) if sample_metrics else 0,
            "logs_processed": len(sample_logs) if sample_logs else 0,
            "note": "This is a simplified preview. Full validation requires OTel collector execution."
        }
        return preview


