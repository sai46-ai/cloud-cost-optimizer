"""
Generic CRUD Repository base class.
Provides create, read, update, delete, and list operations for any SQLAlchemy model.
"""

from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository implementing common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, entity_id: str) -> Optional[ModelType]:
        """Fetch a single entity by primary key."""
        return self.db.query(self.model).filter(self.model.id == entity_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch all entities with pagination."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def count(self) -> int:
        """Count total entities."""
        return self.db.query(func.count(self.model.id)).scalar() or 0

    def create(self, entity: ModelType) -> ModelType:
        """Create a new entity."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: ModelType, update_data: dict) -> ModelType:
        """Update an existing entity with the given data dict."""
        for key, value in update_data.items():
            if value is not None and hasattr(entity, key):
                setattr(entity, key, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: ModelType) -> None:
        """Delete an entity."""
        self.db.delete(entity)
        self.db.commit()

    def bulk_create(self, entities: List[ModelType]) -> List[ModelType]:
        """Bulk create multiple entities."""
        self.db.add_all(entities)
        self.db.commit()
        for entity in entities:
            self.db.refresh(entity)
        return entities
