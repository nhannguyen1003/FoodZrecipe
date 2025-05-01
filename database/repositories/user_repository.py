# TODO: Implement user-specific repository operations
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate
from backend.core.security import get_password_hash, verify_password
from database.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    # TODO: Override create method to hash password
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        # Create user with hashed password
        # ...
    
    # TODO: Implement authentication method
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        # Authenticate user
        # ...

user_repository = UserRepository(User)