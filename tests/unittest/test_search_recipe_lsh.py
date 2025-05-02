import pytest
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.models.recipe import Recipe
from tests.unittest.test_models import TestRecipe, TestUser, TestBase
from database.repositories.base_repository import BaseRepository
from backend.schemas.recipe import RecipeCreate, RecipeUpdate


class TestRecipeRepository(BaseRepository[TestRecipe, RecipeCreate, RecipeUpdate]):
    """Test repository for Recipe that works with SQLite tests"""
    
    def search_by_text_query(self, db: Session, query: str, limit: int = 10) -> List[TestRecipe]:
        """Simplified search by text query for testing"""
        recipes = db.query(self.model).all()
        # Simple filter that checks if query is in title or description
        return [r for r in recipes if query.lower() in r.title.lower() or 
                (r.description and query.lower() in r.description.lower())]
                
    def search_by_text_hash_buckets(self, db: Session, hash_buckets: List[int], limit: int = 10) -> List[TestRecipe]:
        """Search by text LSH hash buckets"""
        recipes = db.query(self.model).all()
        # Filter recipes that have matching hash buckets
        results = []
        for recipe in recipes:
            if recipe.text_hash_buckets and any(b in recipe.text_hash_buckets for b in hash_buckets):
                results.append(recipe)
        return results[:limit]
    
    def search_by_image_hash_buckets(self, db: Session, hash_buckets: List[int], limit: int = 10) -> List[TestRecipe]:
        """Search by image LSH hash buckets"""
        recipes = db.query(self.model).all()
        # Filter recipes that have matching hash buckets
        results = []
        for recipe in recipes:
            if recipe.image_hash_buckets and any(b in recipe.image_hash_buckets for b in hash_buckets):
                results.append(recipe)
        return results[:limit]
    
    def search_by_combined_hash_buckets(self, db: Session, hash_buckets: List[int], limit: int = 10) -> List[TestRecipe]:
        """Search by combined LSH hash buckets"""
        recipes = db.query(self.model).all()
        # Filter recipes that have matching hash buckets
        results = []
        for recipe in recipes:
            if recipe.combined_hash_buckets and any(b in recipe.combined_hash_buckets for b in hash_buckets):
                results.append(recipe)
        return results[:limit]
    
    def search_hybrid(self, db: Session, hash_buckets: List[int], limit: int = 10) -> List[TestRecipe]:
        """Search across multiple hash bucket types"""
        recipes = db.query(self.model).all()
        # Filter recipes that have matching hash buckets in any field
        results = []
        for recipe in recipes:
            has_match = False
            if recipe.text_hash_buckets and any(b in recipe.text_hash_buckets for b in hash_buckets):
                has_match = True
            elif recipe.image_hash_buckets and any(b in recipe.image_hash_buckets for b in hash_buckets):
                has_match = True
            elif recipe.combined_hash_buckets and any(b in recipe.combined_hash_buckets for b in hash_buckets):
                has_match = True
                
            if has_match:
                results.append(recipe)
        return results[:limit] 