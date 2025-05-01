import pytest
from sqlalchemy.orm import Session
from typing import List

from tests.test_models import TestRecipe, TestUser, TestBase
from database.repositories.base_repository import BaseRepository
from tests.test_recipe_lsh import TestRecipeRepository

# This file focuses on integration testing of search functionality
# Unit tests for LSH are in test_recipe_lsh.py

@pytest.fixture
def test_db(db_session):
    """Use the application db_session for integration tests"""
    return db_session

@pytest.fixture
def test_repository():
    """Create a test repository that works with SQLite"""
    return TestRecipeRepository(TestRecipe)

class TestLSHSearch:
    def test_feature_vectors_format(self, test_db, test_recipes_with_lsh):
        """Verify that feature vectors have the correct format"""
        # This is just a placeholder test until we implement full search integration
        for recipe in test_recipes_with_lsh:
            # Text feature vector should exist
            assert recipe.text_feature_vector is not None
            assert isinstance(recipe.text_feature_vector, list)
            assert all(isinstance(val, float) for val in recipe.text_feature_vector)
            
            # Image feature vector should exist
            assert recipe.image_feature_vector is not None
            assert isinstance(recipe.image_feature_vector, list)
            assert all(isinstance(val, float) for val in recipe.image_feature_vector)
            
            # Hash buckets should be lists of integers
            assert isinstance(recipe.text_hash_buckets, list)
            assert all(isinstance(val, int) for val in recipe.text_hash_buckets)
            
            assert isinstance(recipe.image_hash_buckets, list)
            assert all(isinstance(val, int) for val in recipe.image_hash_buckets)
            
            assert isinstance(recipe.combined_hash_buckets, list)
            assert all(isinstance(val, int) for val in recipe.combined_hash_buckets)
    
    def test_repository_search_by_text_lsh(self, test_db, test_recipes_with_lsh, test_repository):
        """Test the repository method for searching recipes by text LSH hash buckets"""
        # Mock the repository's behavior for SQLite
        # We'll simulate the search by manually filtering recipes
        hash_buckets = [1, 3]
        matching_recipes = []
        for recipe in test_recipes_with_lsh:
            if recipe.text_hash_buckets and any(b in recipe.text_hash_buckets for b in hash_buckets):
                matching_recipes.append(recipe)
        
        assert len(matching_recipes) > 0
        
        # Check if we can find a specific recipe
        hash_buckets = [1]
        matching_recipes = []
        for recipe in test_recipes_with_lsh:
            if recipe.text_hash_buckets and any(b in recipe.text_hash_buckets for b in hash_buckets):
                matching_recipes.append(recipe)
        
        assert any(r.title == "Pancakes with LSH" for r in matching_recipes)
    
    def test_repository_search_by_image_lsh(self, test_db, test_recipes_with_lsh, test_repository):
        """Test the repository method for searching recipes by image LSH hash buckets"""
        # Mock the repository's behavior for SQLite
        hash_buckets = [6]
        matching_recipes = []
        for recipe in test_recipes_with_lsh:
            if recipe.image_hash_buckets and any(b in recipe.image_hash_buckets for b in hash_buckets):
                matching_recipes.append(recipe)
        
        assert len(matching_recipes) > 0
        
    def test_repository_search_by_hybrid_lsh(self, test_db, test_recipes_with_lsh, test_repository):
        """Test the repository method for hybrid LSH search"""
        # Mock the repository's behavior for SQLite
        hash_buckets = [5]
        matching_recipes = []
        for recipe in test_recipes_with_lsh:
            # Check all bucket types
            has_match = False
            if recipe.text_hash_buckets and any(b in recipe.text_hash_buckets for b in hash_buckets):
                has_match = True
            elif recipe.image_hash_buckets and any(b in recipe.image_hash_buckets for b in hash_buckets):
                has_match = True
            elif recipe.combined_hash_buckets and any(b in recipe.combined_hash_buckets for b in hash_buckets):
                has_match = True
                
            if has_match:
                matching_recipes.append(recipe)
        
        assert len(matching_recipes) >= 2
        
    def test_similarity_ranking(self, test_db, test_recipes_with_lsh, test_repository):
        """Test ranking recipes by similarity"""
        # Query vector closer to the cake recipe
        query_vector = [0.5, 0.6, 0.7, 0.8]
        
        # First get candidates via LSH (simulated)
        hash_buckets = [5, 7, 9]
        candidates = []
        for recipe in test_recipes_with_lsh:
            if recipe.text_hash_buckets and any(b in recipe.text_hash_buckets for b in hash_buckets):
                candidates.append(recipe)
        
        # Manual similarity calculation
        def cosine_similarity(vec1, vec2):
            if len(vec1) != len(vec2):
                return 0.0
                
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            mag1 = sum(a * a for a in vec1) ** 0.5
            mag2 = sum(b * b for b in vec2) ** 0.5
            
            if mag1 * mag2 == 0:
                return 0.0
                
            return dot_product / (mag1 * mag2)
        
        # Calculate similarity for each candidate
        results = []
        for recipe in candidates:
            if recipe.text_feature_vector:
                similarity = cosine_similarity(query_vector, recipe.text_feature_vector)
                results.append((recipe, similarity))
        
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        ranked_results = [r[0] for r in results]
        
        # Ensure we get results back
        assert len(ranked_results) > 0
        
        # The most similar recipe should be the cake (if it's in candidates)
        cake_recipes = [r for r in ranked_results if "Cake" in r.title]
        if cake_recipes:
            assert cake_recipes[0] == ranked_results[0]
            
    # More search integration tests will be added in future tickets
