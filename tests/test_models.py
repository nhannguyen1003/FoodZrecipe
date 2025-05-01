"""
Test-specific models to work with SQLite in tests
"""
import enum
from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Create a separate base for test models to avoid metadata conflicts
TestBase = declarative_base()

class UserRole(str, enum.Enum):
    REGULAR = "regular"
    ADMIN = "admin"

class TestUser(TestBase):
    __tablename__ = "test_users"
    
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

class TestRecipe(TestBase):
    __tablename__ = "test_recipes"
    
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
    user_id = Column(Integer, ForeignKey("test_users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationship to user
    user = relationship("TestUser", back_populates="recipes")
    
    # LSH-related fields for text-based search (using JSON for SQLite)
    text_feature_vector = Column(JSON, nullable=True)
    text_hash_buckets = Column(JSON, nullable=True)
    
    # LSH-related fields for image-based search
    image_feature_vector = Column(JSON, nullable=True)
    image_hash_buckets = Column(JSON, nullable=True)
    
    # Combined hash buckets for hybrid search
    combined_hash_buckets = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Recipe {self.title}>" 