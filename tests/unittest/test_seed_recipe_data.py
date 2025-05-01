#!/usr/bin/env python3
"""
Unit tests for validating recipe data in the database.
"""

import unittest
import sys
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add parent directory to Python path to make imports work
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.session import engine


class TestRecipeData(unittest.TestCase):
    """Test cases for validating recipe data."""
    
    def setUp(self):
        """Set up test database session."""
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.session = self.SessionLocal()
    
    def tearDown(self):
        """Clean up after tests."""
        self.session.close()
    
    def test_recipe_count(self):
        """Test that the expected number of recipes were added."""
        result = self.session.execute(text("SELECT COUNT(*) FROM recipes"))
        count = result.scalar()
        # We should have at least 1000 recipes from our seeding
        self.assertGreaterEqual(count, 1000, "Expected at least 1000 recipes")
    
    def test_recipe_categories_distribution(self):
        """Test that recipes have a good distribution of categories."""
        # Check count of recipes with categories
        result = self.session.execute(
            text("SELECT COUNT(*) FROM recipes WHERE array_length(categories, 1) > 0")
        )
        recipes_with_categories = result.scalar()
        
        # Check total recipe count
        result = self.session.execute(text("SELECT COUNT(*) FROM recipes"))
        total_recipes = result.scalar()
        
        # Assert that at least 50% of recipes have categories
        self.assertGreaterEqual(
            recipes_with_categories / total_recipes, 
            0.5, 
            "Expected at least 50% of recipes to have categories"
        )
        
        # Check for specific categories
        categories = ['Desserts', 'Breakfast', 'Chicken', 'Pasta', 'Healthy']
        for category in categories:
            result = self.session.execute(
                text("SELECT COUNT(*) FROM recipes WHERE :category = ANY(categories)"),
                {"category": category}
            )
            count = result.scalar()
            self.assertGreater(
                count, 0, f"Expected to find recipes in category '{category}'"
            )
    
    def test_recipe_ingredients(self):
        """Test that recipes have proper ingredients."""
        # Get a sample recipe
        recipe = self.session.execute(
            text("SELECT * FROM recipes LIMIT 1")
        ).fetchone()
        
        # Check ingredients array
        self.assertIsInstance(recipe.ingredients, list, "Ingredients should be an array")
        self.assertGreater(len(recipe.ingredients), 0, "Recipe should have ingredients")
        
        # Check random recipe for reasonable ingredient count
        result = self.session.execute(
            text("SELECT AVG(array_length(ingredients, 1)) FROM recipes")
        )
        avg_ingredient_count = result.scalar()
        self.assertGreater(
            avg_ingredient_count, 3, 
            "Recipes should have a reasonable number of ingredients on average"
        )
    
    def test_recipe_instructions(self):
        """Test that recipes have proper instructions."""
        # Check that instructions exist and are an array
        recipe = self.session.execute(
            text("SELECT * FROM recipes LIMIT 1")
        ).fetchone()
        
        self.assertIsInstance(recipe.instructions, list, "Instructions should be an array")
        self.assertGreater(len(recipe.instructions), 0, "Recipe should have instructions")
        
        # Check if any recipe has more than one instruction step
        result = self.session.execute(
            text("SELECT COUNT(*) FROM recipes WHERE array_length(instructions, 1) > 1")
        )
        count = result.scalar()
        self.assertGreater(
            count, 0, "Expected to find recipes with multiple instruction steps"
        )
    
    def test_specific_recipe_search(self):
        """Test that we can find specific recipes by title substring."""
        test_terms = ['Chicken', 'Cake', 'Pasta', 'Salad']
        
        for term in test_terms:
            result = self.session.execute(
                text("SELECT COUNT(*) FROM recipes WHERE title ILIKE :term"),
                {"term": f"%{term}%"}
            )
            count = result.scalar()
            self.assertGreater(
                count, 0, f"Expected to find recipes with '{term}' in the title"
            )


if __name__ == "__main__":
    unittest.main() 