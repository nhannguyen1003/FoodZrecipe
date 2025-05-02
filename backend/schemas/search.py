"""
Schemas for search functionality including multi-field LSH search
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal

class FieldWeights(BaseModel):
    """Weights for different recipe fields in multi-field search"""
    title: float = 0.3
    ingredients: float = 0.4
    instructions: float = 0.3

class SearchQuery(BaseModel):
    """Basic search query schema"""
    query: str
    limit: int = 10
    offset: int = 0
    sort_by: Optional[str] = "relevance"  # Options: relevance, newest, popular

class RecipeSearchQuery(SearchQuery):
    """Recipe search query schema"""
    categories: Optional[List[str]] = None
    category_ids: Optional[List[int]] = None

class MultiFieldSearchQuery(BaseModel):
    """Multi-field search query schema"""
    title_query: Optional[str] = None
    ingredients_query: Optional[List[str]] = None
    instructions_query: Optional[str] = None
    weights: Optional[Dict[str, float]] = None
    limit: int = 10
    offset: int = 0
    category_ids: Optional[List[int]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "title_query": "Chocolate cake",
                "ingredients_query": ["flour", "sugar", "cocoa powder"],
                "instructions_query": "bake mix",
                "weights": {
                    "title": 0.4,
                    "ingredients": 0.4,
                    "instructions": 0.2
                },
                "limit": 10,
                "offset": 0,
                "category_ids": [1, 5]
            }
        }

class SearchResult(BaseModel):
    """Search result schema"""
    id: int
    title: str
    description: Optional[str] = None
    score: Optional[float] = None

class SearchResults(BaseModel):
    """Container for search results"""
    results: List[SearchResult]
    total: int
    limit: int
    offset: int

class MultiFieldSearchResponse(BaseModel):
    """Response schema for multi-field search"""
    results: List[SearchResult]
    total: int
    limit: int
    offset: int
    query: str
    weights_used: FieldWeights 