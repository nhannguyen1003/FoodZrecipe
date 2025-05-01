import pytest
from sqlalchemy.orm import Session
from typing import List

from backend.models.recipe import Recipe
from tests.unittest.test_models import TestRecipe
from database.repositories.recipe_repository import recipe_repository
from tests.unittest.test_recipe_lsh import TestRecipeRepository

@pytest.fixture
def test_db(db_session):
    """Use the application db_session for integration tests"""
    return db_session

@pytest.fixture
def test_repository():
    """Create a test repository that works with SQLite"""
    return TestRecipeRepository(TestRecipe)

class TestRecipeModel:
    def test_recipe_model_fields(self, test_db, test_recipe):
        """Test that the Recipe model has all required fields"""
        # Simple test to verify the model structure
        recipe = test_recipe
        
        # Basic fields
        assert hasattr(recipe, 'id')
        assert hasattr(recipe, 'title')
        assert hasattr(recipe, 'description')
        assert hasattr(recipe, 'ingredients')
        assert hasattr(recipe, 'instructions')
        assert hasattr(recipe, 'user_id')
        
        # LSH-related fields
        assert hasattr(recipe, 'text_feature_vector')
        assert hasattr(recipe, 'text_hash_buckets')
        assert hasattr(recipe, 'image_feature_vector')
        assert hasattr(recipe, 'image_hash_buckets')
        assert hasattr(recipe, 'combined_hash_buckets')
    
    def test_recipe_user_relationship(self, test_db, test_recipe):
        """Test the relationship between Recipe and User models"""
        recipe = test_recipe
        
        # Verify relationship to user is functional
        assert recipe.user is not None
        assert recipe.user.id == recipe.user_id
        
        # Verify back-relationship from user to recipes
        user = recipe.user
        assert recipe in user.recipes
        
    # More detailed tests for the Recipe model will be added in future tickets
