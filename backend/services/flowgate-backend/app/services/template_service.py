"""Template service"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
import yaml
import json
from app.repositories.template_repository import TemplateRepository
from app.models.template import Template, TemplateVersion
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateVersionCreate


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

        # Create template
        template = Template(
            name=template_data.name,
            description=template_data.description,
            template_type=template_data.template_type,
            org_id=template_data.org_id,
            is_active=True,
            current_version=1,
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
        self.repository.create_version(version)

        return template

    def get_template(self, template_id: UUID, org_id: UUID) -> Optional[Template]:
        """Get a template by ID"""
        return self.repository.get(template_id, org_id)

    def get_templates(self, org_id: UUID, skip: int = 0, limit: int = 100) -> List[Template]:
        """Get all templates for an organization"""
        return self.repository.get_by_org(org_id, skip, limit)

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

    def rollback_to_version(self, template_id: UUID, version: int, org_id: UUID) -> Optional[TemplateVersion]:
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

