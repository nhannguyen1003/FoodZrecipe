from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class CategoryWithRecipesResponse(CategoryResponse):
    recipe_count: int = 0
    
    class Config:
        orm_mode = True 