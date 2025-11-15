"""YAML Configuration Validator for OpenTelemetry Collector

Validates YAML syntax and OTel collector configuration structure.
"""

import yaml
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Validation error with location and message"""
    level: str  # 'error' or 'warning'
    message: str
    field: Optional[str] = None
    line: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    parsed_config: Optional[Dict[str, Any]] = None


class ConfigValidator:
    """Validator for OpenTelemetry Collector YAML configurations"""
    
    REQUIRED_SECTIONS = ['receivers', 'processors', 'exporters', 'service']
    REQUIRED_SERVICE_FIELDS = ['pipelines']
    
    # Allowed components based on builder-config.yaml
    # These are the components available in the FlowGate collector binary
    ALLOWED_RECEIVERS = {'otlp', 'prometheus'}
    ALLOWED_PROCESSORS = {'batch', 'memorylimiter'}
    ALLOWED_EXPORTERS = {'otlp', 'otlphttp', 'debug'}
    ALLOWED_EXTENSIONS = {'opamp'}
    
    def validate_yaml_syntax(self, config_yaml: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate YAML syntax
        
        Returns:
            (is_valid, parsed_config, error_message)
        """
        try:
            parsed = yaml.safe_load(config_yaml)
            if parsed is None:
                return False, None, "YAML file is empty"
            if not isinstance(parsed, dict):
                return False, None, "YAML root must be a dictionary"
            return True, parsed, None
        except yaml.YAMLError as e:
            return False, None, f"YAML syntax error: {str(e)}"
    
    def validate_otel_structure(self, config: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate OpenTelemetry Collector configuration structure
        
        Args:
            config: Parsed YAML configuration dictionary
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required top-level sections
        for section in self.REQUIRED_SECTIONS:
            if section not in config:
                errors.append(ValidationError(
                    level='error',
                    message=f"Missing required section: {section}",
                    field=section
                ))
            elif not isinstance(config[section], dict):
                errors.append(ValidationError(
                    level='error',
                    message=f"Section '{section}' must be a dictionary",
                    field=section
                ))
        
        # Validate service section structure
        if 'service' in config:
            service = config['service']
            if not isinstance(service, dict):
                errors.append(ValidationError(
                    level='error',
                    message="Service section must be a dictionary",
                    field='service'
                ))
            else:
                # Check for pipelines
                if 'pipelines' not in service:
                    errors.append(ValidationError(
                        level='error',
                        message="Service section must contain 'pipelines'",
                        field='service.pipelines'
                    ))
                elif not isinstance(service['pipelines'], dict):
                    errors.append(ValidationError(
                        level='error',
                        message="Service pipelines must be a dictionary",
                        field='service.pipelines'
                    ))
                else:
                    # Validate pipeline structure
                    errors.extend(self._validate_pipelines(service['pipelines'], config))
        
        # Validate component references
        errors.extend(self._validate_component_references(config))
        
        return errors
    
    def _validate_pipelines(self, pipelines: Dict[str, Any], config: Dict[str, Any]) -> List[ValidationError]:
        """Validate pipeline definitions"""
        errors = []
        
        for pipeline_name, pipeline_config in pipelines.items():
            if not isinstance(pipeline_config, dict):
                errors.append(ValidationError(
                    level='error',
                    message=f"Pipeline '{pipeline_name}' must be a dictionary",
                    field=f'service.pipelines.{pipeline_name}'
                ))
                continue
            
            # Check for required pipeline fields
            required_fields = ['receivers', 'processors', 'exporters']
            for field in required_fields:
                if field not in pipeline_config:
                    errors.append(ValidationError(
                        level='error',
                        message=f"Pipeline '{pipeline_name}' missing required field: {field}",
                        field=f'service.pipelines.{pipeline_name}.{field}'
                    ))
                elif not isinstance(pipeline_config[field], list):
                    errors.append(ValidationError(
                        level='error',
                        message=f"Pipeline '{pipeline_name}' field '{field}' must be a list",
                        field=f'service.pipelines.{pipeline_name}.{field}'
                    ))
                elif len(pipeline_config[field]) == 0:
                    errors.append(ValidationError(
                        level='warning',
                        message=f"Pipeline '{pipeline_name}' has empty '{field}' list",
                        field=f'service.pipelines.{pipeline_name}.{field}'
                    ))
        
        return errors
    
    def _validate_component_references(self, config: Dict[str, Any]) -> List[ValidationError]:
        """Validate that all referenced components exist"""
        errors = []
        
        # Collect all defined components
        defined_components = {
            'receivers': set(config.get('receivers', {}).keys()),
            'processors': set(config.get('processors', {}).keys()),
            'exporters': set(config.get('exporters', {}).keys()),
        }
        
        # Check pipeline references
        if 'service' in config and 'pipelines' in config['service']:
            pipelines = config['service']['pipelines']
            for pipeline_name, pipeline_config in pipelines.items():
                if not isinstance(pipeline_config, dict):
                    continue
                
                # Check receiver references
                for receiver in pipeline_config.get('receivers', []):
                    if receiver not in defined_components['receivers']:
                        errors.append(ValidationError(
                            level='error',
                            message=f"Pipeline '{pipeline_name}' references undefined receiver: {receiver}",
                            field=f'service.pipelines.{pipeline_name}.receivers'
                        ))
                
                # Check processor references
                for processor in pipeline_config.get('processors', []):
                    if processor not in defined_components['processors']:
                        errors.append(ValidationError(
                            level='error',
                            message=f"Pipeline '{pipeline_name}' references undefined processor: {processor}",
                            field=f'service.pipelines.{pipeline_name}.processors'
                        ))
                
                # Check exporter references
                for exporter in pipeline_config.get('exporters', []):
                    if exporter not in defined_components['exporters']:
                        errors.append(ValidationError(
                            level='error',
                            message=f"Pipeline '{pipeline_name}' references undefined exporter: {exporter}",
                            field=f'service.pipelines.{pipeline_name}.exporters'
                        ))
        
        return errors
    
    def validate_config_completeness(self, config: Dict[str, Any]) -> List[ValidationError]:
        """Check for common configuration issues"""
        warnings = []
        
        # Warn if no receivers are defined
        if 'receivers' in config and len(config['receivers']) == 0:
            warnings.append(ValidationError(
                level='warning',
                message="No receivers defined. Collector will not receive any data.",
                field='receivers'
            ))
        
        # Warn if no exporters are defined
        if 'exporters' in config and len(config['exporters']) == 0:
            warnings.append(ValidationError(
                level='warning',
                message="No exporters defined. Collector will not export any data.",
                field='exporters'
            ))
        
        return warnings
    
    def _get_component_type(self, component_name: str, component_config: Dict[str, Any]) -> str:
        """
        Extract the actual component type from component config.
        
        In OTel configs, component type can be:
        1. The name itself (e.g., 'otlp: {}')
        2. A key in the config dict (e.g., 'my_otlp: { otlp: {...} }')
        3. Part of an alias (e.g., 'otlp/backend: {}')
        """
        # Handle aliases (e.g., 'otlp/backend' -> 'otlp')
        base_name = component_name.split('/')[0]
        
        # Check if the config dict has a key that matches a known component type
        # This handles cases like: 'my_otlp: { otlp: {...} }'
        if isinstance(component_config, dict):
            for key in component_config.keys():
                if key in (self.ALLOWED_RECEIVERS | self.ALLOWED_PROCESSORS | 
                          self.ALLOWED_EXPORTERS | self.ALLOWED_EXTENSIONS):
                    return key
        
        # Default to the base name (most common case)
        return base_name
    
    def _validate_allowed_components(self, config: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate that only allowed components are used in the config.
        This ensures compatibility with the FlowGate collector binary.
        """
        errors = []
        
        # Validate receivers
        receivers = config.get('receivers', {})
        for receiver_name, receiver_config in receivers.items():
            if isinstance(receiver_config, dict):
                receiver_type = self._get_component_type(receiver_name, receiver_config)
                if receiver_type not in self.ALLOWED_RECEIVERS:
                    errors.append(ValidationError(
                        level='error',
                        message=f"Receiver '{receiver_name}' uses unsupported component type '{receiver_type}'. "
                                f"Allowed receivers: {', '.join(sorted(self.ALLOWED_RECEIVERS))}",
                        field=f'receivers.{receiver_name}'
                    ))
        
        # Validate processors
        processors = config.get('processors', {})
        for processor_name, processor_config in processors.items():
            if isinstance(processor_config, dict):
                processor_type = self._get_component_type(processor_name, processor_config)
                if processor_type not in self.ALLOWED_PROCESSORS:
                    errors.append(ValidationError(
                        level='error',
                        message=f"Processor '{processor_name}' uses unsupported component type '{processor_type}'. "
                                f"Allowed processors: {', '.join(sorted(self.ALLOWED_PROCESSORS))}",
                        field=f'processors.{processor_name}'
                    ))
        
        # Validate exporters
        exporters = config.get('exporters', {})
        for exporter_name, exporter_config in exporters.items():
            if isinstance(exporter_config, dict):
                exporter_type = self._get_component_type(exporter_name, exporter_config)
                if exporter_type not in self.ALLOWED_EXPORTERS:
                    errors.append(ValidationError(
                        level='error',
                        message=f"Exporter '{exporter_name}' uses unsupported component type '{exporter_type}'. "
                                f"Allowed exporters: {', '.join(sorted(self.ALLOWED_EXPORTERS))}",
                        field=f'exporters.{exporter_name}'
                    ))
        
        # Validate extensions
        extensions = config.get('extensions', {})
        for extension_name, extension_config in extensions.items():
            if isinstance(extension_config, dict):
                extension_type = self._get_component_type(extension_name, extension_config)
                if extension_type not in self.ALLOWED_EXTENSIONS:
                    errors.append(ValidationError(
                        level='error',
                        message=f"Extension '{extension_name}' uses unsupported component type '{extension_type}'. "
                                f"Allowed extensions: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}",
                        field=f'extensions.{extension_name}'
                    ))
        
        return errors
    
    def validate(self, config_yaml: str) -> ValidationResult:
        """
        Validate YAML configuration
        
        Args:
            config_yaml: YAML configuration string
            
        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        warnings = []
        
        # Step 1: Validate YAML syntax
        is_valid, parsed_config, yaml_error = self.validate_yaml_syntax(config_yaml)
        if not is_valid:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(level='error', message=yaml_error)],
                warnings=[],
                parsed_config=None
            )
        
        # Step 2: Validate OTel structure
        structure_errors = self.validate_otel_structure(parsed_config)
        errors.extend([e for e in structure_errors if e.level == 'error'])
        warnings.extend([e for e in structure_errors if e.level == 'warning'])
        
        # Step 3: Validate component types (ensure only allowed components are used)
        component_errors = self._validate_allowed_components(parsed_config)
        errors.extend(component_errors)
        
        # Step 4: Check completeness
        completeness_warnings = self.validate_config_completeness(parsed_config)
        warnings.extend(completeness_warnings)
        
        return ValidationResult(
            is_valid=len([e for e in errors if e.level == 'error']) == 0,
            errors=errors,
            warnings=warnings,
            parsed_config=parsed_config
        )
    
    def calculate_config_hash(self, config_yaml: str) -> str:
        """
        Calculate hash of configuration for version tracking
        
        Args:
            config_yaml: YAML configuration string
            
        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(config_yaml.encode('utf-8')).hexdigest()
    
    def get_validation_errors(self, result: ValidationResult) -> List[str]:
        """
        Get formatted error messages from validation result
        
        Args:
            result: ValidationResult object
            
        Returns:
            List of formatted error messages
        """
        messages = []
        for error in result.errors:
            if error.field:
                messages.append(f"{error.field}: {error.message}")
            else:
                messages.append(error.message)
        return messages
    
    def get_validation_warnings(self, result: ValidationResult) -> List[str]:
        """
        Get formatted warning messages from validation result
        
        Args:
            result: ValidationResult object
            
        Returns:
            List of formatted warning messages
        """
        messages = []
        for warning in result.warnings:
            if warning.field:
                messages.append(f"{warning.field}: {warning.message}")
            else:
                messages.append(warning.message)
        return messages

