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

class MultiFieldSearchQuery(BaseModel):
    """Schema for multi-field search with configurable weights"""
    query: str
    limit: int = 10
    offset: int = 0
    field_weights: Optional[FieldWeights] = None
    search_fields: Optional[List[Literal["title", "ingredients", "instructions"]]] = None
    query_type: Optional[Literal["default", "ingredient", "technique", "dish"]] = None
    categories: Optional[List[str]] = None
    category_ids: Optional[List[int]] = None
    sort_by: Optional[str] = "relevance"  # Options: relevance, newest, popular

class SearchResult(BaseModel):
    """Search result with score information"""
    recipe_id: int
    score: float
    field_scores: Optional[Dict[str, float]] = None

class MultiFieldSearchResponse(BaseModel):
    """Response schema for multi-field search"""
    results: List[SearchResult]
    total: int
    limit: int
    offset: int
    query: str
    weights_used: FieldWeights 