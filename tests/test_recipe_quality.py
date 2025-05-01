#!/usr/bin/env python3
"""
Unit tests for validating the quality of recipe data.
"""

import unittest
import sys
import re
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, func

# Add parent directory to Python path to make imports work
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.session import engine


class TestRecipeQuality(unittest.TestCase):
    """Test cases for validating the quality of recipe data."""
    
    def setUp(self):
        """Set up test database session."""
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.session = self.SessionLocal()
    
    def tearDown(self):
        """Clean up after tests."""
        self.session.close()
    
    def test_no_empty_titles(self):
        """Test that all recipes have non-empty titles."""
        result = self.session.execute(
            text("SELECT COUNT(*) FROM recipes WHERE title = '' OR title IS NULL")
        )
        count = result.scalar()
        self.assertEqual(count, 0, "There should be no recipes with empty titles")
    
    def test_title_length(self):
        """Test that recipe titles have reasonable length."""
        # Titles should be between 3 and 100 characters
        result = self.session.execute(
            text("SELECT COUNT(*) FROM recipes WHERE LENGTH(title) < 3 OR LENGTH(title) > 100")
        )
        count = result.scalar()
        self.assertEqual(count, 0, "Recipe titles should have reasonable length (3-100 characters)")
    
    def test_ingredients_format(self):
        """Test that ingredient arrays are properly formatted."""
        # Get a sample of recipes
        recipes = self.session.execute(
            text("SELECT id, ingredients FROM recipes LIMIT 10")
        ).fetchall()
        
        for recipe in recipes:
            # Check that ingredients is a list
            self.assertIsInstance(recipe.ingredients, list)
            
            # Check that each ingredient is a string
            for ingredient in recipe.ingredients:
                self.assertIsInstance(ingredient, str)
                self.assertTrue(len(ingredient) > 0, "Ingredients should not be empty strings")
    
    def test_instructions_format(self):
        """Test that instruction arrays are properly formatted."""
        # Get a sample of recipes
        recipes = self.session.execute(
            text("SELECT id, instructions FROM recipes LIMIT 10")
        ).fetchall()
        
        for recipe in recipes:
            # Check that instructions is a list
            self.assertIsInstance(recipe.instructions, list)
            
            # Check that each instruction is a string
            for instruction in recipe.instructions:
                self.assertIsInstance(instruction, str)
                self.assertTrue(len(instruction) > 0, "Instructions should not be empty strings")
    
    def test_reasonable_ingredient_count(self):
        """Test that most recipes have a reasonable number of ingredients."""
        # Get total recipe count
        result = self.session.execute(
            text("SELECT COUNT(*) FROM recipes")
        )
        total_recipes = result.scalar()
        
        # Get count of recipes with unusual ingredient counts
        result = self.session.execute(
            text("""
                SELECT COUNT(*) FROM recipes 
                WHERE array_length(ingredients, 1) < 2 
                OR array_length(ingredients, 1) > 30
            """)
        )
        unusual_count = result.scalar()
        
        # Calculate percentage of recipes with unusual ingredient counts
        unusual_percentage = (unusual_count / total_recipes) * 100
        
        # Allow up to 1% of recipes to have unusual ingredient counts
        self.assertLessEqual(
            unusual_percentage, 1.0, 
            f"Too many recipes ({unusual_count} out of {total_recipes}, {unusual_percentage:.2f}%) have unusual ingredient counts"
        )
        
        # Report the finding but don't fail the test
        if unusual_count > 0:
            print(f"\nInfo: Found {unusual_count} recipes with unusual ingredient counts (<2 or >30 ingredients)")
            
            # Let's see what these unusual recipes are
            recipes = self.session.execute(
                text("""
                    SELECT id, title, array_length(ingredients, 1) as ingredient_count 
                    FROM recipes 
                    WHERE array_length(ingredients, 1) < 2 
                    OR array_length(ingredients, 1) > 30
                    ORDER BY array_length(ingredients, 1)
                """)
            ).fetchall()
            
            for recipe in recipes:
                print(f"  Recipe {recipe.id}: '{recipe.title}' has {recipe.ingredient_count} ingredients")
    
    def test_categories_data_type(self):
        """Test that categories are properly formatted as arrays of strings."""
        # Get recipes with categories
        recipes = self.session.execute(
            text("SELECT id, categories FROM recipes WHERE array_length(categories, 1) > 0 LIMIT 10")
        ).fetchall()
        
        for recipe in recipes:
            # Check that categories is a list
            self.assertIsInstance(recipe.categories, list)
            
            # Check that each category is a string
            for category in recipe.categories:
                self.assertIsInstance(category, str)
                self.assertTrue(len(category) > 0, "Categories should not be empty strings")
    
    def test_user_id_integrity(self):
        """Test that all recipes have valid user IDs."""
        # Check if any recipes have NULL user_id
        result = self.session.execute(
            text("SELECT COUNT(*) FROM recipes WHERE user_id IS NULL")
        )
        count = result.scalar()
        self.assertEqual(count, 0, "All recipes should have a user_id")
        
        # Check if all user_ids exist in the users table
        result = self.session.execute(
            text("""
                SELECT COUNT(*) FROM recipes r
                WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = r.user_id)
            """)
        )
        count = result.scalar()
        self.assertEqual(count, 0, "All recipe user_ids should exist in the users table")


if __name__ == "__main__":
    unittest.main() 