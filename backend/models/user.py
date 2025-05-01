# TODO: Define User database model
from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
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
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.REGULAR)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship to recipes
    recipes = relationship("Recipe", back_populates="user")