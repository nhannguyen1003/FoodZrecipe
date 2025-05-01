# TODO: Implement user-specific repository operations
from typing import Optional, List, Any, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate
from backend.core.security import get_password_hash, verify_password
from database.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            role=obj_in.role,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate | Dict[str, Any]) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        update_data["updated_at"] = datetime.utcnow()
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    def is_active(self, user: User) -> bool:
        return user.is_active
    
    def is_admin(self, user: User) -> bool:
        return user.role == "admin"

user_repository = UserRepository(User)