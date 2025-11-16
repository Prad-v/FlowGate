"""System template service for managing default collector configurations"""

import os
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.system_template import SystemTemplate

logger = logging.getLogger(__name__)


class SystemTemplateService:
    """Service for system template operations"""
    
    DEFAULT_TEMPLATE_NAME = "Default Collector Config (Supervisor Mode)"
    DEFAULT_TEMPLATE_DESCRIPTION = "Default OpenTelemetry Collector configuration template for supervisor-managed agents"
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_default_template(self) -> Optional[SystemTemplate]:
        """Get the default system template"""
        return self.db.query(SystemTemplate).filter(
            SystemTemplate.name == self.DEFAULT_TEMPLATE_NAME,
            SystemTemplate.is_active == True
        ).first()
    
    def initialize_default_template(self, config_yaml: Optional[str] = None) -> SystemTemplate:
        """Initialize or update the default system template from YAML file or provided content
        
        Args:
            config_yaml: Optional YAML content. If not provided, reads from file.
        
        Returns:
            SystemTemplate instance
        """
        # Read config from file if not provided
        if config_yaml is None:
            config_yaml = self._read_default_config_file()
        
        # Check if template already exists
        existing = self.get_default_template()
        
        if existing:
            # Update existing template
            existing.config_yaml = config_yaml
            existing.is_active = True
            self.db.commit()
            self.db.refresh(existing)
            logger.info(f"Updated default system template: {existing.id}")
            return existing
        else:
            # Create new template
            template = SystemTemplate(
                name=self.DEFAULT_TEMPLATE_NAME,
                description=self.DEFAULT_TEMPLATE_DESCRIPTION,
                config_yaml=config_yaml,
                is_active=True
            )
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            logger.info(f"Created default system template: {template.id}")
            return template
    
    def _read_default_config_file(self) -> str:
        """Read the default config file from gateway directory
        
        Returns:
            Config YAML content as string
        """
        # Try multiple possible paths (for different deployment scenarios)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            # Path 1: From backend/services/flowgate-backend to project root/gateway
            os.path.normpath(os.path.join(current_dir, '..', '..', '..', '..', '..', 'gateway', 'otel-collector-config-supervisor-gateway-2.yaml')),
            # Path 2: From backend/services/flowgate-backend/app/services to project root/gateway
            os.path.normpath(os.path.join(current_dir, '..', '..', '..', '..', '..', '..', 'gateway', 'otel-collector-config-supervisor-gateway-2.yaml')),
            # Path 3: Relative to /app (Docker container)
            '/app/../gateway/otel-collector-config-supervisor-gateway-2.yaml',
            # Path 4: If gateway is mounted at /gateway
            '/gateway/otel-collector-config-supervisor-gateway-2.yaml',
            # Path 5: Environment variable override
            os.environ.get('DEFAULT_CONFIG_FILE_PATH', ''),
        ]
        
        # Filter out empty paths
        possible_paths = [p for p in possible_paths if p]
        
        for config_file_path in possible_paths:
            if os.path.exists(config_file_path):
                logger.info(f"Reading default config from: {config_file_path}")
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        # If file not found, return a default template based on the provided YAML
        logger.warning(f"Default config file not found in any of these paths: {possible_paths}. Using built-in default.")
        return self._get_default_config_yaml()
    
    def _get_default_config_yaml(self) -> str:
        """Return default config YAML as fallback when file is not found"""
        # Use the exact content from otel-collector-config-supervisor-gateway-2.yaml
        return """receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-collector'
          scrape_interval: 10s
          static_configs:
            - targets: ['localhost:8888']

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    limit_mib: 512
    check_interval: 1s
  # Transformations will be injected here via OpAMP Supervisor

exporters:
  otlp:
    endpoint: localhost:4317
    tls:
      insecure: true
  otlp/observability-backend:
    endpoint: vector-observability-backend:4317
    tls:
      insecure: true
  debug:
    verbosity: normal
  # Backend exporters will be configured via OpAMP Supervisor

extensions:
  opamp:
    server:
      ws:
        # In supervisor mode, collector connects to supervisor's local endpoint
        # The supervisor exposes a local OpAMP server on the port specified in supervisor.yaml
        # The supervisor's local server typically uses /v1/opamp path
        endpoint: ws://localhost:4321/v1/opamp
        tls:
          insecure: true
          insecure_skip_verify: true
    # OpAMP extension capabilities
    # Reference: https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/extension/opampextension/config.go
    # The OpAMP extension supports 3 configurable capabilities (all default to true):
    # - reports_effective_config: Agent reports its effective configuration
    # - reports_health: Agent reports health status
    # - reports_available_components: Agent reports available collector components
    # Note: ReportsStatus is always enabled (hardcoded in extension)
    capabilities:
      reports_effective_config: true
      reports_health: true
      reports_available_components: true
      # Note: In supervisor mode, most capabilities are handled by the supervisor.
      # The collector's OpAMP extension only reports these limited capabilities to the supervisor.

service:
  pipelines:
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, batch]
      exporters: [otlp/observability-backend, debug]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/observability-backend, debug]
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/observability-backend, debug]
  
  extensions: [opamp]
  
  telemetry:
    logs:
      level: info
    metrics:
      level: detailed

"""
    
    def update_default_template(self, config_yaml: str, description: Optional[str] = None) -> SystemTemplate:
        """Update the default system template
        
        Args:
            config_yaml: New YAML content
            description: Optional new description
        
        Returns:
            Updated SystemTemplate instance
        """
        template = self.get_default_template()
        if not template:
            # Create if doesn't exist
            return self.initialize_default_template(config_yaml)
        
        template.config_yaml = config_yaml
        if description:
            template.description = description
        
        self.db.commit()
        self.db.refresh(template)
        logger.info(f"Updated default system template: {template.id}")
        return template

