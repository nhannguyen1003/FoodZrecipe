# TODO: Define User database model
from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.session import Base
import enum

class UserRole(str, enum.Enum):
    REGULAR = "regular"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.REGULAR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Bi-directional relationship with Recipe model
    recipes = relationship("Recipe", back_populates="user", cascade="all, delete-orphan")
    
    # Create a composite index for efficient user lookup during authentication
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_username_active', 'username', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User {self.username}>"