# TODO: Implement base repository pattern for database operations
from typing import TypeVar, Generic, Type, List, Optional, Any, Dict, Union, Callable
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from database.session import Base
import logging
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    @contextmanager
    def transaction(self, db: Session):
        """
        Provides transaction context for multi-operation tasks.
        Usage:
            with repository.transaction(db) as tx_db:
                repository.create(tx_db, obj_in=obj1)
                repository.create(tx_db, obj_in=obj2)
        """
        try:
            yield db
            db.commit()
            logger.debug(f"Transaction committed successfully for {self.model.__name__}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Transaction failed for {self.model.__name__}: {str(e)}")
            raise
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a single object by ID.
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving {self.model.__name__} with id {id}: {str(e)}")
            raise
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get multiple objects with pagination.
        """
        try:
            return db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving multiple {self.model.__name__}: {str(e)}")
            raise
    
    def get_count(self, db: Session) -> int:
        """
        Get total count of objects for pagination metadata.
        """
        try:
            return db.query(self.model).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__} objects: {str(e)}")
            raise
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new object.
        """
        try:
            obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.debug(f"Created {self.model.__name__} object with id {db_obj.id}")
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating {self.model.__name__} object: {str(e)}")
            raise
    
    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Update an existing object.
        """
        try:
            obj_data = db_obj.__dict__
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
                
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
                    
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.debug(f"Updated {self.model.__name__} object with id {db_obj.id}")
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating {self.model.__name__} object: {str(e)}")
            raise
    
    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Remove an object by ID.
        """
        try:
            obj = db.query(self.model).get(id)
            if obj is None:
                logger.warning(f"{self.model.__name__} with id {id} not found for deletion")
                return None
            db.delete(obj)
            db.commit()
            logger.debug(f"Deleted {self.model.__name__} object with id {id}")
            return obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__} object with id {id}: {str(e)}")
            raise
    
    def bulk_create(self, db: Session, *, obj_list: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple objects in a single transaction.
        """
        try:
            with self.transaction(db) as tx_db:
                result = []
                for obj_in in obj_list:
                    obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
                    db_obj = self.model(**obj_in_data)
                    tx_db.add(db_obj)
                    result.append(db_obj)
                tx_db.flush()  # Flush to get IDs without committing
            # Transaction context manager will commit
            logger.debug(f"Bulk created {len(result)} {self.model.__name__} objects")
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error in bulk creation of {self.model.__name__} objects: {str(e)}")
            raise
    
    def get_by_filter(self, db: Session, *, filter_condition: Any, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get multiple objects by a filter condition with pagination.
        """
        try:
            return db.query(self.model).filter(filter_condition).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving {self.model.__name__} objects by filter: {str(e)}")
            raise
    
    def exists(self, db: Session, *, id: Any) -> bool:
        """
        Check if an object with the given ID exists.
        """
        try:
            return db.query(db.query(self.model).filter(self.model.id == id).exists()).scalar()
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model.__name__} with id {id}: {str(e)}")
            raise