"""Base repository with common functionality"""

from typing import Generic, TypeVar, Type, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: UUID, org_id: Optional[UUID] = None) -> Optional[ModelType]:
        """Get a single record by ID with optional org filtering"""
        query = self.db.query(self.model).filter(self.model.id == id)
        if org_id and hasattr(self.model, "org_id"):
            query = query.filter(self.model.org_id == org_id)
        return query.first()

    def get_by_org(self, org_id: UUID, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records for an organization"""
        if not hasattr(self.model, "org_id"):
            return []
        return (
            self.db.query(self.model)
            .filter(self.model.org_id == org_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, obj: ModelType) -> ModelType:
        """Create a new record"""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        """Update an existing record"""
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: UUID, org_id: Optional[UUID] = None) -> bool:
        """Delete a record by ID"""
        obj = self.get(id, org_id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

