# TODO: Implement user-specific repository operations
from typing import Optional, List, Any, Dict
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.user import User, UserRole
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
        # Implement password hashing in create method
        hashed_password = get_password_hash(obj_in.password)
        
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=hashed_password,
            role=obj_in.role,
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
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
        
        update_data["updated_at"] = datetime.now(UTC)
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        # Complete authentication method with secure password verification
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Only authenticate active users
        if not user.is_active:
            return None
            
        # Update last login timestamp
        user.last_login = datetime.now(UTC)
        db.commit()
        
        return user
    
    def is_active(self, user: User) -> bool:
        return user.is_active
    
    def is_admin(self, user: User) -> bool:
        return user.role == UserRole.ADMIN
    
    # Add role-based query methods
    def get_users_by_role(self, db: Session, *, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).filter(User.role == role).offset(skip).limit(limit).all()
    
    def count_users_by_role(self, db: Session, *, role: UserRole) -> int:
        return db.query(User).filter(User.role == role).count()
    
    # Implement account status management
    def activate_user(self, db: Session, *, user_id: int) -> Optional[User]:
        user = self.get(db, id=user_id)
        if not user:
            return None
        
        user.is_active = True
        user.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(user)
        return user
    
    def deactivate_user(self, db: Session, *, user_id: int) -> Optional[User]:
        user = self.get(db, id=user_id)
        if not user:
            return None
        
        user.is_active = False
        user.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(user)
        return user
    
    def change_user_role(self, db: Session, *, user_id: int, new_role: UserRole) -> Optional[User]:
        user = self.get(db, id=user_id)
        if not user:
            return None
        
        user.role = new_role
        user.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(user)
        return user
    
    def create_user_direct(self, db: Session, **user_data) -> User:
        """
        Create a user directly with provided data (mainly for testing)
        
        This method bypasses the schema validation and allows creating users
        with pre-hashed passwords.
        """
        db_obj = User(**user_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

user_repository = UserRepository(User)