# Pydantic models for recipe data validation
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from backend.schemas.category import CategoryResponse

class RecipeBase(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: List[str]
    instructions: Union[str, List[str]] = Field(...)  # Accept either string or list of strings
    image_url: Optional[str] = None
    image_name: Optional[str] = None  # Added to support Image_Name
    categories: Optional[List[str]] = None  # Legacy field
    labels: Optional[List[str]] = None  # Added to support labels field
    cleaned_ingredients: Optional[List[str]] = None  # Added to support Cleaned_Ingredients
    prompt: Optional[str] = None  # Added to support prompt field
    prep_time: Optional[int] = None  # Made optional
    cook_time: Optional[int] = None  # Made optional
    servings: Optional[int] = None   # Made optional
    raw_data: Optional[Dict[str, Any]] = None  # Added to store original JSON

class RecipeCreate(RecipeBase):
    category_ids: Optional[List[int]] = None

class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[Union[str, List[str]]] = None  # Allow both formats
    image_url: Optional[str] = None
    image_name: Optional[str] = None  # Added
    categories: Optional[List[str]] = None  # Legacy field
    labels: Optional[List[str]] = None  # Added
    cleaned_ingredients: Optional[List[str]] = None  # Added
    prompt: Optional[str] = None  # Added
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    raw_data: Optional[Dict[str, Any]] = None  # Added
    category_ids: Optional[List[int]] = None

class RecipeResponse(RecipeBase):
    id: int
    user_id: Optional[int] = None  # Changed to Optional to handle null values
    created_at: datetime
    category_relations: Optional[List[CategoryResponse]] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2
        
class RecipeInternalResponse(RecipeResponse):
    """Internal schema with LSH fields - only used by admin dashboard"""
    # Original LSH fields
    text_feature_vector: Optional[List[float]] = None
    text_hash_buckets: Optional[List[int]] = None
    image_feature_vector: Optional[List[float]] = None
    image_hash_buckets: Optional[List[int]] = None
    combined_hash_buckets: Optional[List[int]] = None
    
    # Multi-field LSH fields
    title_feature_vector: Optional[List[float]] = None
    ingredients_feature_vector: Optional[List[float]] = None
    instructions_feature_vector: Optional[List[float]] = None
    title_hash_buckets: Optional[List[int]] = None
    ingredients_hash_buckets: Optional[List[int]] = None
    instructions_hash_buckets: Optional[List[int]] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class RecipeSearchQuery(BaseModel):
    query: str
    limit: int = 10
    offset: int = 0
    categories: Optional[List[str]] = None
    category_ids: Optional[List[int]] = None
    sort_by: Optional[str] = "relevance"  # Options: relevance, newest, popular
    
class LSHSearchQuery(BaseModel):
    text_hash_buckets: Optional[List[int]] = None
    image_hash_buckets: Optional[List[int]] = None
    combined_hash_buckets: Optional[List[int]] = None
    feature_vector: Optional[List[float]] = None  # For re-ranking
    limit: int = 10
    offset: int = 0
    category_ids: Optional[List[int]] = None