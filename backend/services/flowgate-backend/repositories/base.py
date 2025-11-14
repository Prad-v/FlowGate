"""Base repository with common operations."""
from typing import Generic, TypeVar, Type, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        """Initialize repository with model and database session."""
        self.model = model
        self.db = db
    
    def get(self, id: UUID, org_id: Optional[UUID] = None) -> Optional[ModelType]:
        """Get a single record by ID with optional org filtering."""
        query = self.db.query(self.model).filter(self.model.id == id)
        if org_id:
            query = query.filter(self.model.org_id == org_id)
        return query.first()
    
    def get_multi(
        self,
        org_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with optional org filtering."""
        query = self.db.query(self.model)
        if org_id:
            query = query.filter(self.model.org_id == org_id)
        return query.offset(skip).limit(limit).all()
    
    def create(self, obj: ModelType) -> ModelType:
        """Create a new record."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def update(self, id: UUID, org_id: Optional[UUID], **kwargs) -> Optional[ModelType]:
        """Update a record."""
        obj = self.get(id, org_id)
        if not obj:
            return None
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def delete(self, id: UUID, org_id: Optional[UUID] = None) -> bool:
        """Delete a record."""
        obj = self.get(id, org_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True


