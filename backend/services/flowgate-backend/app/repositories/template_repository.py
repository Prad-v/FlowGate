"""Template repository"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.template import Template, TemplateVersion
from app.repositories.base_repository import BaseRepository


class TemplateRepository(BaseRepository[Template]):
    """Repository for Template operations"""

    def __init__(self, db: Session):
        super().__init__(Template, db)

    def get(self, id: UUID, org_id: Optional[UUID] = None) -> Optional[Template]:
        """Get a template by ID, handling both org-scoped and system templates"""
        query = self.db.query(Template).filter(Template.id == id)
        
        # For system templates (org_id is None), they're accessible to all orgs
        # For org-scoped templates, filter by org_id
        if org_id is not None:
            query = query.filter(
                (Template.org_id == org_id) | (Template.is_system_template == True)
            )
        
        return query.first()

    def get_by_name(self, name: str, org_id: UUID) -> Optional[Template]:
        """Get template by name and org"""
        return (
            self.db.query(Template)
            .filter(Template.name == name, Template.org_id == org_id)
            .first()
        )

    def get_versions(self, template_id: UUID, org_id: UUID) -> List[TemplateVersion]:
        """Get all versions for a template"""
        template = self.get(template_id, org_id)
        if not template:
            return []
        return (
            self.db.query(TemplateVersion)
            .filter(TemplateVersion.template_id == template_id)
            .order_by(TemplateVersion.version.desc())
            .all()
        )

    def get_version(self, template_id: UUID, version: int, org_id: UUID) -> Optional[TemplateVersion]:
        """Get a specific template version"""
        template = self.get(template_id, org_id)
        if not template:
            return None
        return (
            self.db.query(TemplateVersion)
            .filter(
                TemplateVersion.template_id == template_id,
                TemplateVersion.version == version,
            )
            .first()
        )

    def get_current_version(self, template_id: UUID, org_id: UUID) -> Optional[TemplateVersion]:
        """Get the current active version of a template"""
        template = self.get(template_id, org_id)
        if not template:
            return None
        return (
            self.db.query(TemplateVersion)
            .filter(
                TemplateVersion.template_id == template_id,
                TemplateVersion.version == template.current_version,
            )
            .first()
        )

    def create_version(self, version: TemplateVersion) -> TemplateVersion:
        """Create a new template version"""
        self.db.add(version)
        # Update template's current_version
        # Get template without org_id filter since we're updating it
        template = self.db.query(Template).filter(Template.id == version.template_id).first()
        if template:
            template.current_version = version.version
        self.db.commit()
        self.db.refresh(version)
        return version

