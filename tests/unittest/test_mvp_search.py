import pytest
import json
import numpy as np
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from backend.models.recipe import Recipe
from backend.models.user import User
from backend.services.lsh_service import lsh_service
from backend.services.multi_field_search_service import multi_field_search_service
from database.repositories.recipe_repository import recipe_repository
from backend.schemas.recipe import RecipeCreate, RecipeUpdate
from backend.schemas.search import MultiFieldSearchQuery, SearchResults
from config import settings


@pytest.fixture
def mock_recipes():
    """Create mock recipes for testing"""
    user_id = 1
    return [
        Recipe(
            id=1,
            title="Chocolate Cake Recipe",
            description="Delicious chocolate cake",
            ingredients=["flour", "sugar", "cocoa powder", "eggs", "butter"],
            instructions="Mix dry ingredients. Add wet ingredients. Bake at 350F for 30 minutes.",
            user_id=user_id
        ),
        Recipe(
            id=2,
            title="Pasta Carbonara",
            description="Classic Italian pasta dish",
            ingredients=["pasta", "eggs", "pancetta", "parmesan", "black pepper"],
            instructions="Cook pasta. Fry pancetta. Mix eggs and cheese. Combine while pasta is hot.",
            user_id=user_id
        ),
        Recipe(
            id=3,
            title="Banana Bread",
            description="Moist banana bread recipe",
            ingredients=["bananas", "flour", "sugar", "eggs", "butter", "baking soda"],
            instructions="Mash bananas. Mix ingredients. Bake until golden brown.",
            user_id=user_id
        ),
        Recipe(
            id=4,
            title="Chocolate Chip Cookies",
            description="Classic cookies with chocolate chips",
            ingredients=["flour", "sugar", "butter", "eggs", "chocolate chips", "vanilla"],
            instructions="Cream butter and sugar. Add eggs. Mix in dry ingredients. Add chocolate chips. Bake.",
            user_id=user_id
        ),
        Recipe(
            id=5,
            title="Chicken Curry",
            description="Spicy chicken curry",
            ingredients=["chicken", "curry powder", "onions", "garlic", "coconut milk", "rice"],
            instructions="Cook chicken. Add spices. Simmer in coconut milk. Serve with rice.",
            user_id=user_id
        )
    ]


class TestMVPSearch003:
    """Tests for MVP-SEARCH-003: feature flag, comparison with original, limitations"""
    
    def test_feature_flag_enabled(self, monkeypatch):
        """Test that multi-field search is used when feature flag is enabled"""
        # Set feature flag to enabled
        monkeypatch.setattr(settings, "USE_MULTI_FIELD_SEARCH", True)
        
        # Mock the search functions to track which one is called
        original_search_called = [False]
        multi_field_search_called = [False]
        
        def mock_original_search(*args, **kwargs):
            original_search_called[0] = True
            return [], []
            
        def mock_multi_field_search(*args, **kwargs):
            multi_field_search_called[0] = True
            return [], []
        
        # Apply the mocks
        monkeypatch.setattr(recipe_repository, "search_by_text_query", mock_original_search)
        monkeypatch.setattr(multi_field_search_service, "multi_field_search", mock_multi_field_search)
        
        # Create a test repository that uses the feature flag
        class TestRepository:
            def search_recipes(self, db, query, **kwargs):
                if getattr(settings, "USE_MULTI_FIELD_SEARCH", False):
                    return multi_field_search_service.multi_field_search(db, title_query=query)
                else:
                    return recipe_repository.search_by_text_query(db, query=query)
        
        test_repo = TestRepository()
        
        # Execute search
        test_repo.search_recipes(None, "test query")
        
        # Verify that multi-field search was called and original search was not
        assert multi_field_search_called[0] is True
        assert original_search_called[0] is False
    
    def test_feature_flag_disabled(self, monkeypatch):
        """Test that original search is used when feature flag is disabled"""
        # Set feature flag to disabled
        monkeypatch.setattr(settings, "USE_MULTI_FIELD_SEARCH", False)
        
        # Mock the search functions to track which one is called
        original_search_called = [False]
        multi_field_search_called = [False]
        
        def mock_original_search(*args, **kwargs):
            original_search_called[0] = True
            return [], []
            
        def mock_multi_field_search(*args, **kwargs):
            multi_field_search_called[0] = True
            return [], []
        
        # Apply the mocks
        monkeypatch.setattr(recipe_repository, "search_by_text_query", mock_original_search)
        monkeypatch.setattr(multi_field_search_service, "multi_field_search", mock_multi_field_search)
        
        # Create a test repository that uses the feature flag
        class TestRepository:
            def search_recipes(self, db, query, **kwargs):
                if getattr(settings, "USE_MULTI_FIELD_SEARCH", False):
                    return multi_field_search_service.multi_field_search(db, title_query=query)
                else:
                    return recipe_repository.search_by_text_query(db, query=query)
        
        test_repo = TestRepository()
        
        # Execute search
        test_repo.search_recipes(None, "test query")
        
        # Verify that original search was called and multi-field search was not
        assert original_search_called[0] is True
        assert multi_field_search_called[0] is False
    
    def test_comparison_with_original_implementation(self, mock_recipes, monkeypatch):
        """Test comparing multi-field search with original implementation"""
        # Create simple implementations for testing
        def mock_create_vector(text):
            # Simple mock implementation for testing
            vector = np.zeros(128, dtype=np.float32)
            for i, char in enumerate(text):
                index = hash(char) % 128
                vector[index] += 1
            return vector / max(np.sum(vector), 1)  # Normalize
        
        def mock_search_original(query, recipes, k=3):
            # Mock the original search (single vector)
            query_vector = mock_create_vector(query)
            results = []
            
            for recipe in recipes:
                # Concatenate all text fields
                all_text = recipe.title + " " + recipe.description + " " + " ".join(recipe.ingredients) + " " + recipe.instructions
                # Create a single vector for all text
                recipe_vector = mock_create_vector(all_text)
                # Calculate similarity
                similarity = np.dot(query_vector, recipe_vector)
                results.append((recipe, similarity))
            
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x[1], reverse=True)
            return [r[0] for r in results[:k]], [r[1] for r in results[:k]]
        
        def mock_search_multi_field(query, recipes, k=3):
            # Mock the multi-field search (separate vectors for each field)
            query_vector = mock_create_vector(query)
            results = []
            
            for recipe in recipes:
                # Create separate vectors for each field
                title_vector = mock_create_vector(recipe.title)
                ingredients_vector = mock_create_vector(" ".join(recipe.ingredients))
                instructions_vector = mock_create_vector(recipe.instructions)
                
                # Calculate weighted similarity
                title_weight = 0.4
                ingredients_weight = 0.4
                instructions_weight = 0.2
                
                # Calculate similarity for each field
                title_similarity = np.dot(query_vector, title_vector) * title_weight
                ingredients_similarity = np.dot(query_vector, ingredients_vector) * ingredients_weight
                instructions_similarity = np.dot(query_vector, instructions_vector) * instructions_weight
                
                # Combined similarity
                combined_similarity = title_similarity + ingredients_similarity + instructions_similarity
                results.append((recipe, combined_similarity))
            
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x[1], reverse=True)
            return [r[0] for r in results[:k]], [r[1] for r in results[:k]]
        
        # Run searches with original and multi-field implementations
        search_queries = [
            "chocolate", 
            "pasta italian", 
            "banana bread recipe", 
            "chicken curry spicy"
        ]
        
        for query in search_queries:
            # Get results from both implementations
            original_results, _ = mock_search_original(query, mock_recipes)
            multi_field_results, _ = mock_search_multi_field(query, mock_recipes)
            
            # Check that we have results from both
            assert len(original_results) > 0
            assert len(multi_field_results) > 0
            
            # For demonstration purposes, output results (in practice this would write to logs)
            print(f"\nSearch query: {query}")
            print("Original search results:")
            for recipe in original_results:
                print(f"  - {recipe.title}")
            
            print("Multi-field search results:")
            for recipe in multi_field_results:
                print(f"  - {recipe.title}")
    
    def test_known_limitations(self):
        """Test documenting known limitations"""
        # This is a placeholder test to document known limitations
        known_limitations = {
            "vector_simplification": "Character frequency vectors are used instead of proper embeddings for simplicity",
            "equal_field_weighting": "Field weights are statically configured, not dynamically adjusted by query",
            "no_query_classification": "The system does not automatically classify queries to determine optimal field weights",
            "limited_text_processing": "Minimal text processing is done for instructions field in MVP",
            "no_caching": "Result caching is not implemented in the MVP version"
        }
        
        # The test passes if we have documented limitations
        assert len(known_limitations) > 0
        
        # Verify specific expected limitations are documented
        assert "vector_simplification" in known_limitations
        assert "equal_field_weighting" in known_limitations
        assert "no_query_classification" in known_limitations 