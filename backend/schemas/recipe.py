# Pydantic models for recipe data validation
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.schemas.category import CategoryResponse

class RecipeBase(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: List[str]
    instructions: str  # Changed from List[str] to str to match the single-block format
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
    instructions: Optional[str] = None  # Changed from List[str] to str
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
    user_id: int
    created_at: datetime
    category_relations: Optional[List[CategoryResponse]] = None
    
    class Config:
        orm_mode = True
        
class RecipeInternalResponse(RecipeResponse):
    """Internal schema with LSH fields - only used by admin dashboard"""
    text_feature_vector: Optional[List[float]] = None
    text_hash_buckets: Optional[List[int]] = None
    image_feature_vector: Optional[List[float]] = None
    image_hash_buckets: Optional[List[int]] = None
    combined_hash_buckets: Optional[List[int]] = None
    
    class Config:
        orm_mode = True

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