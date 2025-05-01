"""
Test-specific models to work with SQLite in tests
"""
import enum
from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.session import Base

class UserRole(str, enum.Enum):
    REGULAR = "regular"
    ADMIN = "admin"

class TestUser(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.REGULAR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationship to recipes
    recipes = relationship("TestRecipe", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"

class TestRecipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    # Use JSON for arrays in SQLite
    ingredients = Column(JSON, nullable=False)
    instructions = Column(JSON, nullable=False)
    image_url = Column(String(255), nullable=True)
    categories = Column(JSON, nullable=True)
    prep_time = Column(Integer, nullable=True)
    cook_time = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationship to user
    user = relationship("TestUser", back_populates="recipes")
    
    # Feature vector for LSH stored as JSON
    feature_vector = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Recipe {self.title}>" 