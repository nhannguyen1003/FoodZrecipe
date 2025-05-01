# TODO: Define Pydantic models for recipe data validation
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RecipeBase(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    image_url: Optional[str] = None
    categories: List[str]
    prep_time: int
    cook_time: int
    servings: int

class RecipeCreate(RecipeBase):
    pass

class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    image_url: Optional[str] = None
    categories: Optional[List[str]] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None

class RecipeResponse(RecipeBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class RecipeSearchQuery(BaseModel):
    query: str
    limit: int = 10
    offset: int = 0