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
        # Get the project root (assuming we're in backend/services/flowgate-backend)
        # Go up to project root: backend/services/flowgate-backend -> backend/services -> backend -> project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..', '..', '..', '..', '..')
        config_file_path = os.path.join(
            project_root,
            'gateway',
            'otel-collector-config-supervisor-gateway-2.yaml'
        )
        
        # Normalize path
        config_file_path = os.path.normpath(config_file_path)
        
        if not os.path.exists(config_file_path):
            # Try alternative path (if running from different location)
            alt_path = os.path.join(
                os.path.dirname(current_dir),
                '..', '..', '..', 'gateway',
                'otel-collector-config-supervisor-gateway-2.yaml'
            )
            alt_path = os.path.normpath(alt_path)
            if os.path.exists(alt_path):
                config_file_path = alt_path
            else:
                raise FileNotFoundError(
                    f"Default config file not found. Tried: {config_file_path}, {alt_path}"
                )
        
        with open(config_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
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

