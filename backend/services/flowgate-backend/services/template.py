"""Template service."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from models.template import Template, TemplateVersion
from repositories.template import TemplateRepository
from schemas.template import TemplateCreate, TemplateUpdate, TemplateResponse, TemplateVersionResponse
import yaml
import json


class TemplateService:
    """Service for template operations."""
    
    def __init__(self, db: Session):
        """Initialize template service."""
        self.db = db
        self.repo = TemplateRepository(db)
    
    def create_template(
        self,
        org_id: UUID,
        template_data: TemplateCreate
    ) -> Template:
        """Create a new template with initial version."""
        # Validate YAML
        try:
            config_dict = yaml.safe_load(template_data.config_yaml)
            config_json = json.dumps(config_dict)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {str(e)}")
        
        # Create template
        template = Template(
            org_id=org_id,
            name=template_data.name,
            description=template_data.description,
            template_type=template_data.template_type,
            is_active=True,
            current_version=1
        )
        template = self.repo.create(template)
        
        # Create initial version
        version = self.repo.create_version(
            template_id=template.id,
            version=1,
            config_yaml=template_data.config_yaml,
            org_id=org_id,
            change_summary=template_data.change_summary or "Initial version"
        )
        
        return template
    
    def get_template(self, template_id: UUID, org_id: UUID) -> Optional[Template]:
        """Get a template by ID."""
        return self.repo.get(template_id, org_id)
    
    def get_templates(
        self,
        org_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Template]:
        """Get all templates for an organization."""
        return self.repo.get_multi(org_id=org_id, skip=skip, limit=limit)
    
    def update_template(
        self,
        template_id: UUID,
        org_id: UUID,
        template_data: TemplateUpdate
    ) -> Optional[Template]:
        """Update a template."""
        template = self.repo.get(template_id, org_id)
        if not template:
            return None
        
        update_data = template_data.model_dump(exclude_unset=True)
        
        # If config_yaml is being updated, create a new version
        if "config_yaml" in update_data:
            config_yaml = update_data.pop("config_yaml")
            try:
                yaml.safe_load(config_yaml)  # Validate
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML: {str(e)}")
            
            # Create new version
            new_version = template.current_version + 1
            self.repo.create_version(
                template_id=template.id,
                version=new_version,
                config_yaml=config_yaml,
                org_id=org_id,
                change_summary=update_data.get("change_summary", f"Update to version {new_version}")
            )
            template.current_version = new_version
        
        # Update other fields
        if update_data:
            self.repo.update(template_id, org_id, **update_data)
            template = self.repo.get(template_id, org_id)
        
        return template
    
    def delete_template(self, template_id: UUID, org_id: UUID) -> bool:
        """Delete a template."""
        return self.repo.delete(template_id, org_id)
    
    def get_template_versions(
        self,
        template_id: UUID,
        org_id: UUID
    ) -> List[TemplateVersion]:
        """Get all versions of a template."""
        return self.repo.get_versions(template_id, org_id)
    
    def get_template_version(
        self,
        template_id: UUID,
        version: int,
        org_id: UUID
    ) -> Optional[TemplateVersion]:
        """Get a specific template version."""
        return self.repo.get_version(template_id, version, org_id)


