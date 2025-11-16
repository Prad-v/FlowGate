"""Template service"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import yaml
import json
import logging
from app.repositories.template_repository import TemplateRepository
from app.models.template import Template, TemplateVersion
from app.models.gateway import Gateway
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateVersionCreate

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for template operations"""

    def __init__(self, db: Session):
        self.repository = TemplateRepository(db)
        self.db = db

    def create_template(self, template_data: TemplateCreate) -> Template:
        """Create a new template with initial version"""
        # Validate YAML
        try:
            config_dict = yaml.safe_load(template_data.config_yaml)
            config_json = json.dumps(config_dict)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {str(e)}")

        # Validate system template constraints
        is_system_template = getattr(template_data, 'is_system_template', False)
        if is_system_template:
            # System templates must not have org_id
            org_id = None
            # Check for duplicate system template name
            existing = self.db.query(Template).filter(
                Template.name == template_data.name,
                Template.is_system_template == True
            ).first()
            if existing:
                raise ValueError(f"System template with name '{template_data.name}' already exists")
        else:
            # Org-scoped templates must have org_id
            org_id = template_data.org_id
            if not org_id:
                raise ValueError("org_id is required for non-system templates")
            # Check for duplicate org-scoped template name
            existing = self.db.query(Template).filter(
                Template.name == template_data.name,
                Template.org_id == org_id,
                Template.is_system_template == False
            ).first()
            if existing:
                raise ValueError(f"Template with name '{template_data.name}' already exists for this organization")

        # Create template
        template = Template(
            name=template_data.name,
            description=template_data.description,
            template_type=template_data.template_type,
            org_id=org_id,
            is_active=True,
            current_version=1,
            is_system_template=is_system_template,
        )
        template = self.repository.create(template)

        # Create initial version
        version = TemplateVersion(
            template_id=template.id,
            version=1,
            config_yaml=template_data.config_yaml,
            config_json=json.loads(config_json),
            description="Initial version",
            is_active=True,
        )
        version = self.repository.create_version(version)
        
        # Set first version as default
        template.default_version_id = version.id
        self.repository.update(template)

        return template

    def get_template(self, template_id: UUID, org_id: UUID) -> Optional[Template]:
        """Get a template by ID"""
        return self.repository.get(template_id, org_id)

    def get_templates(self, org_id: Optional[UUID] = None, skip: int = 0, limit: int = 100, is_system_template: Optional[bool] = None) -> List[Template]:
        """Get all templates for an organization or system templates
        
        Args:
            org_id: Organization ID (required for org-scoped templates)
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_system_template: Filter by system template flag (None = both)
        
        Returns:
            List of templates
        """
        query = self.db.query(Template)
        
        if is_system_template is True:
            # Only system templates
            query = query.filter(Template.is_system_template == True)
        elif is_system_template is False:
            # Only org-scoped templates
            query = query.filter(Template.is_system_template == False)
            if org_id:
                query = query.filter(Template.org_id == org_id)
        else:
            # Both: org-scoped for the org + all system templates
            if org_id:
                query = query.filter(
                    or_(
                        and_(Template.is_system_template == False, Template.org_id == org_id),
                        Template.is_system_template == True
                    )
                )
            else:
                # No org_id provided, return all system templates
                query = query.filter(Template.is_system_template == True)
        
        return query.offset(skip).limit(limit).all()

    def update_template(self, template_id: UUID, org_id: UUID, update_data: TemplateUpdate) -> Optional[Template]:
        """Update a template"""
        template = self.repository.get(template_id, org_id)
        if not template:
            return None

        if update_data.name is not None:
            template.name = update_data.name
        if update_data.description is not None:
            template.description = update_data.description
        if update_data.is_active is not None:
            template.is_active = update_data.is_active

        return self.repository.update(template)

    def delete_template(self, template_id: UUID, org_id: UUID) -> bool:
        """Delete a template"""
        return self.repository.delete(template_id, org_id)

    def create_version(self, template_id: UUID, org_id: UUID, version_data: TemplateVersionCreate) -> Optional[TemplateVersion]:
        """Create a new version of a template"""
        template = self.repository.get(template_id, org_id)
        if not template:
            return None

        # Validate YAML
        try:
            config_dict = yaml.safe_load(version_data.config_yaml)
            config_json = json.dumps(config_dict)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {str(e)}")

        # Create new version
        new_version = template.current_version + 1
        version = TemplateVersion(
            template_id=template_id,
            version=new_version,
            config_yaml=version_data.config_yaml,
            config_json=json.loads(config_json),
            description=version_data.description or f"Version {new_version}",
            is_active=True,
        )

        return self.repository.create_version(version)

    def get_versions(self, template_id: UUID, org_id: UUID) -> List[TemplateVersion]:
        """Get all versions of a template"""
        return self.repository.get_versions(template_id, org_id)

    def get_version(self, template_id: UUID, version: int, org_id: UUID) -> Optional[TemplateVersion]:
        """Get a specific template version"""
        return self.repository.get_version(template_id, version, org_id)

    def rollback_to_version(self, template_id: UUID, version: int, org_id: Optional[UUID] = None) -> Optional[TemplateVersion]:
        """Rollback template to a specific version"""
        template = self.repository.get(template_id, org_id)
        if not template:
            return None

        target_version = self.repository.get_version(template_id, version, org_id)
        if not target_version:
            return None

        # Update template's current_version
        template.current_version = version
        self.repository.update(template)

        return target_version
    
    def set_default_version(self, template_id: UUID, version: int, org_id: Optional[UUID] = None) -> Optional[Template]:
        """Set a specific version as the default version for a template
        
        Args:
            template_id: Template ID
            version: Version number to set as default
            org_id: Organization ID (optional, for validation)
        
        Returns:
            Updated Template or None if not found
        """
        template = self.repository.get(template_id, org_id)
        if not template:
            return None
        
        # Get the version
        target_version = self.repository.get_version(template_id, version, org_id)
        if not target_version:
            raise ValueError(f"Version {version} not found for template {template_id}")
        
        # Validate that the version belongs to this template
        if target_version.template_id != template.id:
            raise ValueError(f"Version {version} does not belong to template {template_id}")
        
        # Set as default
        template.default_version_id = target_version.id
        self.repository.update(template)
        
        logger.info(f"Set version {version} as default for template {template_id}")
        return template
    
    def load_config_from_gateway(self, gateway_id: UUID, org_id: UUID) -> Optional[str]:
        """Load effective configuration from a gateway via OpAMP
        
        Args:
            gateway_id: Gateway UUID
            org_id: Organization UUID
        
        Returns:
            Config YAML as string, or None if not available
        """
        gateway = self.db.query(Gateway).filter(
            Gateway.id == gateway_id,
            Gateway.org_id == org_id
        ).first()
        
        if not gateway:
            logger.warning(f"Gateway {gateway_id} not found for org {org_id}")
            return None
        
        # Try to get effective config from gateway's stored OpAMP data
        effective_config_yaml = gateway.opamp_effective_config_content
        
        if effective_config_yaml:
            logger.info(f"Loaded effective config from gateway {gateway_id} (from OpAMP message)")
            return effective_config_yaml
        
        # Fallback: try to get from last deployment
        if gateway.last_config_deployment_id:
            from app.models.opamp_config_deployment import OpAMPConfigDeployment
            deployment = self.db.query(OpAMPConfigDeployment).filter(
                OpAMPConfigDeployment.id == gateway.last_config_deployment_id
            ).first()
            
            if deployment and deployment.config_yaml:
                logger.info(f"Loaded config from gateway {gateway_id} (from last deployment)")
                return deployment.config_yaml
        
        logger.warning(f"No effective config available for gateway {gateway_id}")
        return None
    
    def migrate_system_template_to_template(self, system_template_id: UUID) -> Optional[Template]:
        """Migrate a SystemTemplate from system_templates table to Template with is_system_template=True
        
        This is a helper method to migrate existing SystemTemplate records to the unified Template system.
        
        Args:
            system_template_id: SystemTemplate UUID to migrate
        
        Returns:
            Created Template or None if SystemTemplate not found
        """
        from app.models.system_template import SystemTemplate
        
        system_template = self.db.query(SystemTemplate).filter(
            SystemTemplate.id == system_template_id
        ).first()
        
        if not system_template:
            logger.warning(f"SystemTemplate {system_template_id} not found")
            return None
        
        # Check if template already exists with this name
        existing = self.db.query(Template).filter(
            Template.name == system_template.name,
            Template.is_system_template == True
        ).first()
        
        if existing:
            logger.info(f"Template with name '{system_template.name}' already exists, skipping migration")
            return existing
        
        # Create template from system template
        from app.models.template import TemplateType
        template_data = TemplateCreate(
            name=system_template.name,
            description=system_template.description,
            template_type=TemplateType.COMPOSITE,  # Default type for system templates
            org_id=None,
            config_yaml=system_template.config_yaml,
            is_system_template=True,
        )
        
        try:
            template = self.create_template(template_data)
            logger.info(f"Migrated SystemTemplate {system_template_id} to Template {template.id}")
            return template
        except ValueError as e:
            logger.error(f"Failed to migrate SystemTemplate {system_template_id}: {e}")
            return None

