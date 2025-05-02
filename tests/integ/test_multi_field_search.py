import pytest
from sqlalchemy.orm import Session
import json
from typing import List, Dict, Any, Optional

from backend.models.recipe import Recipe
from backend.models.user import User
from backend.services.multi_field_search_service import multi_field_search_service
from database.repositories.recipe_repository import recipe_repository


@pytest.fixture
def setup_test_data(db_session, test_user):
    """Create test recipes with multi-field data for integration testing"""
    # Delete existing recipes to avoid conflicts
    db_session.query(Recipe).delete()
    db_session.commit()
    
    # Create test recipes
    recipes = [
        Recipe(
            title="Classic Chocolate Cake",
            description="Rich and moist chocolate cake for any occasion",
            ingredients=["flour", "sugar", "cocoa powder", "eggs", "butter", "milk"],
            instructions="Mix dry ingredients. Add wet ingredients. Bake at 350F for 30 minutes.",
            user_id=test_user.id
        ),
        Recipe(
            title="Pasta Carbonara",
            description="Traditional Italian pasta dish",
            ingredients=["pasta", "eggs", "pancetta", "parmesan cheese", "black pepper", "salt"],
            instructions="Cook pasta. Fry pancetta. Mix eggs and cheese. Combine while pasta is hot.",
            user_id=test_user.id
        ),
        Recipe(
            title="Banana Bread",
            description="Sweet and delicious banana bread",
            ingredients=["bananas", "flour", "sugar", "eggs", "butter", "baking soda", "salt"],
            instructions="Mash bananas. Mix wet ingredients. Add dry ingredients. Bake until done.",
            user_id=test_user.id
        ),
        Recipe(
            title="Chicken Curry",
            description="Spicy chicken curry with coconut milk",
            ingredients=["chicken", "curry powder", "onions", "garlic", "coconut milk", "rice"],
            instructions="Cook chicken. Add spices. Simmer in coconut milk. Serve with rice.",
            user_id=test_user.id
        ),
        Recipe(
            title="Chocolate Chip Cookies",
            description="Classic chocolate chip cookies",
            ingredients=["flour", "sugar", "brown sugar", "butter", "eggs", "chocolate chips", "vanilla"],
            instructions="Cream butter and sugars. Add eggs. Mix in dry ingredients. Add chocolate chips. Bake.",
            user_id=test_user.id
        )
    ]
    
    # Add recipes to the database
    for recipe in recipes:
        db_session.add(recipe)
    
    db_session.commit()
    
    # Generate embeddings for all recipes
    multi_field_search_service.generate_embeddings_for_all_recipes(db_session)
    
    # Ensure indices are built
    multi_field_search_service.build_indices(db_session)
    
    # Fetch recipes with generated embeddings
    return recipe_repository.get_all(db_session)


class TestMultiFieldSearchIntegration:
    """Integration tests for multi-field search functionality"""
    
    def test_generate_embeddings(self, db_session, setup_test_data):
        """Test that embeddings are generated correctly for all fields"""
        recipes = setup_test_data
        
        # Verify all recipes have field-specific vectors
        for recipe in recipes:
            assert recipe.title_feature_vector is not None
            assert recipe.ingredients_feature_vector is not None
            assert recipe.instructions_feature_vector is not None
            
            assert recipe.title_hash_buckets is not None
            assert recipe.ingredients_hash_buckets is not None
            assert recipe.instructions_hash_buckets is not None
    
    def test_search_by_title(self, db_session, setup_test_data):
        """Test searching by title field"""
        # Search for chocolate recipes
        title_query = "chocolate"
        
        # Search by title
        recipe_ids, _ = multi_field_search_service.search_by_title(title_query)
        
        # Verify results
        assert len(recipe_ids) > 0
        
        # Get the actual recipes
        recipes = recipe_repository.get_multi_by_ids(db_session, ids=recipe_ids)
        
        # Manually check for recipes with "chocolate" in the title
        chocolate_titles = [r for r in recipes if "chocolate" in r.title.lower()]
        assert len(chocolate_titles) > 0
        
        # Verify that at least one specific chocolate recipe is found
        found_recipes = [r.title for r in recipes]
        assert any(name in found_recipes for name in ["Classic Chocolate Cake", "Chocolate Chip Cookies"])
    
    def test_search_by_ingredients(self, db_session, setup_test_data):
        """Test searching by ingredients field"""
        # Search for recipes with chicken
        ingredient_query = ["chicken", "curry"]
        
        # Search by ingredients
        recipe_ids, _ = multi_field_search_service.search_by_ingredients(ingredient_query)
        
        # Verify results
        assert len(recipe_ids) > 0
        
        # Get the actual recipes
        recipes = recipe_repository.get_multi_by_ids(db_session, ids=recipe_ids)
        
        # Check if "chicken" is in the ingredients of any recipe
        found_chicken = False
        for recipe in recipes:
            ingredients_str = ' '.join(recipe.ingredients).lower()
            if "chicken" in ingredients_str:
                found_chicken = True
                break
        
        assert found_chicken, "No recipes found with 'chicken' in the ingredients"
        
        # Verify that the Chicken Curry recipe is found
        recipe_titles = [r.title for r in recipes]
        assert "Chicken Curry" in recipe_titles
    
    def test_search_by_instructions(self, db_session, setup_test_data):
        """Test searching by instructions field"""
        # Search for baking instructions
        instructions_query = "bake mix ingredients"
        
        # Search by instructions
        recipe_ids, _ = multi_field_search_service.search_by_instructions(instructions_query)
        
        # Verify results
        assert len(recipe_ids) > 0
        
        # Get the actual recipes
        recipes = recipe_repository.get_multi_by_ids(db_session, ids=recipe_ids)
        
        # Check if "bake" is in the instructions of any recipe
        found_bake = False
        for recipe in recipes:
            if "bake" in recipe.instructions.lower():
                found_bake = True
                break
        
        assert found_bake, "No recipes found with 'bake' in the instructions"
    
    def test_multi_field_search(self, db_session, setup_test_data):
        """Test searching across multiple fields"""
        # Search for chocolate desserts
        title_query = "chocolate"
        ingredients_query = ["flour", "sugar", "eggs"]
        instructions_query = "mix bake"
        
        # Custom weights prioritizing title and ingredients
        weights = {
            "title": 0.4,
            "ingredients": 0.4,
            "instructions": 0.2
        }
        
        # Perform multi-field search
        results = multi_field_search_service.multi_field_search(
            db_session,
            title_query=title_query,
            ingredients_query=ingredients_query,
            instructions_query=instructions_query,
            weights=weights,
            k=3
        )
        
        # Verify we got results
        assert len(results) > 0
        
        # Check if any result contains "chocolate" in the title
        chocolate_recipes = [r for r in results if "chocolate" in r.title.lower()]
        assert len(chocolate_recipes) > 0, "No recipes found with 'chocolate' in the title"
        
        # Check if the baking instructions are in any recipe
        found_bake = False
        for recipe in results:
            if "bake" in recipe.instructions.lower():
                found_bake = True
                break
        
        assert found_bake, "No recipes found with 'bake' in the instructions"
    
    def test_update_recipe_embeddings(self, db_session, setup_test_data):
        """Test updating embeddings for a single recipe"""
        # Get a recipe to update
        recipes = setup_test_data
        recipe_to_update = recipes[0]
        
        # Store the original ID to verify we get the same recipe back
        original_id = recipe_to_update.id
        
        # Update the recipe
        recipe_to_update.title = "Updated Chocolate Cake Recipe"
        recipe_to_update.ingredients = ["updated", "ingredient", "list"]
        db_session.add(recipe_to_update)
        db_session.commit()
        
        # Clear existing embeddings
        recipe_to_update.title_feature_vector = None
        recipe_to_update.ingredients_feature_vector = None
        recipe_to_update.instructions_feature_vector = None
        db_session.add(recipe_to_update)
        db_session.commit()
        
        # Update embeddings
        updated_recipe = multi_field_search_service.update_recipe_embeddings(db_session, recipe_to_update.id)
        
        # Verify embeddings were generated
        assert updated_recipe.title_feature_vector is not None
        assert updated_recipe.ingredients_feature_vector is not None
        assert updated_recipe.instructions_feature_vector is not None
        
        # Verify correct recipe was updated
        assert updated_recipe.id == original_id
        assert "updated" in updated_recipe.title.lower()
        
        # Test search with updated recipe
        recipe_ids, _ = multi_field_search_service.search_by_title("updated recipe")
        assert updated_recipe.id in recipe_ids 