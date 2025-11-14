"""Template repository."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.template import Template, TemplateVersion
from repositories.base import BaseRepository


class TemplateRepository(BaseRepository[Template]):
    """Repository for Template operations."""
    
    def __init__(self, db: Session):
        """Initialize template repository."""
        super().__init__(Template, db)
        self.db = db
    
    def get_by_name(self, name: str, org_id: UUID) -> Optional[Template]:
        """Get template by name and org."""
        return self.db.query(Template).filter(
            and_(
                Template.name == name,
                Template.org_id == org_id
            )
        ).first()
    
    def get_versions(
        self,
        template_id: UUID,
        org_id: Optional[UUID] = None
    ) -> List[TemplateVersion]:
        """Get all versions for a template."""
        query = self.db.query(TemplateVersion).filter(
            TemplateVersion.template_id == template_id
        )
        if org_id:
            query = query.join(Template).filter(Template.org_id == org_id)
        return query.order_by(TemplateVersion.version.desc()).all()
    
    def get_version(
        self,
        template_id: UUID,
        version: int,
        org_id: Optional[UUID] = None
    ) -> Optional[TemplateVersion]:
        """Get a specific template version."""
        query = self.db.query(TemplateVersion).filter(
            and_(
                TemplateVersion.template_id == template_id,
                TemplateVersion.version == version
            )
        )
        if org_id:
            query = query.join(Template).filter(Template.org_id == org_id)
        return query.first()
    
    def get_latest_version(
        self,
        template_id: UUID,
        org_id: Optional[UUID] = None
    ) -> Optional[TemplateVersion]:
        """Get the latest version of a template."""
        query = self.db.query(TemplateVersion).filter(
            TemplateVersion.template_id == template_id
        )
        if org_id:
            query = query.join(Template).filter(Template.org_id == org_id)
        return query.order_by(TemplateVersion.version.desc()).first()
    
    def create_version(
        self,
        template_id: UUID,
        version: int,
        config_yaml: str,
        org_id: UUID,
        change_summary: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> TemplateVersion:
        """Create a new template version."""
        version_obj = TemplateVersion(
            template_id=template_id,
            org_id=org_id,
            version=version,
            config_yaml=config_yaml,
            change_summary=change_summary,
            created_by=created_by
        )
        self.db.add(version_obj)
        self.db.commit()
        self.db.refresh(version_obj)
        return version_obj


