# TODO: Define Recipe database model
from sqlalchemy import Column, Integer, String, Text, ARRAY, ForeignKey, DateTime, Float, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB
from database.session import Base

class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    ingredients = Column(ARRAY(String), nullable=False)
    cleaned_ingredients = Column(ARRAY(String), nullable=True)  # Added for raw vs cleaned ingredients
    instructions = Column(Text, nullable=False)  # Changed from ARRAY to Text to support the single block format
    image_url = Column(String(255), nullable=True)
    image_name = Column(String(255), nullable=True)  # Added to support Image_Name field
    categories = Column(ARRAY(String), nullable=True)  # Maps to labels in sample data
    labels = Column(ARRAY(String), nullable=True)  # Added explicit labels field for clarity
    prompt = Column(Text, nullable=True)  # Added to support prompt field
    prep_time = Column(Integer, nullable=True)  # minutes
    cook_time = Column(Integer, nullable=True)  # minutes
    servings = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to user with back reference
    user = relationship("User", back_populates="recipes")
    
    # LSH-related fields for text-based search
    text_feature_vector = Column(PG_ARRAY(Float), nullable=True)
    text_hash_buckets = Column(ARRAY(Integer), nullable=True)
    
    # LSH-related fields for image-based search
    image_feature_vector = Column(PG_ARRAY(Float), nullable=True)
    image_hash_buckets = Column(ARRAY(Integer), nullable=True)
    
    # Combined hash buckets for hybrid search
    combined_hash_buckets = Column(ARRAY(Integer), nullable=True)
    
    # Additional field for raw JSON data
    raw_data = Column(JSONB, nullable=True)  # Store the original JSON data
    
    # Add indices for performance optimization
    __table_args__ = (
        Index('idx_recipe_title', 'title'),
        Index('idx_recipe_user_id', 'user_id'),
        Index('idx_recipe_text_hash', 'text_hash_buckets', postgresql_using='gin'),
        Index('idx_recipe_image_hash', 'image_hash_buckets', postgresql_using='gin'),
        Index('idx_recipe_combined_hash', 'combined_hash_buckets', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<Recipe {self.title}>"