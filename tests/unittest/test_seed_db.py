#!/usr/bin/env python3
"""
Unit tests for the database seeding process.
"""

import unittest
import sys
from pathlib import Path
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func, text

# Add parent directory to Python path to make imports work
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.session import engine


class TestDatabaseSeeding(unittest.TestCase):
    """Test cases for database seeding functionality."""
    
    def setUp(self):
        """Set up test database session."""
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.session = self.SessionLocal()
    
    def tearDown(self):
        """Clean up after tests."""
        self.session.close()
    
    def test_users_exist(self):
        """Test that at least one user exists in the database."""
        result = self.session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        self.assertGreater(count, 0, "No users found in the database")
    
    def test_recipes_exist(self):
        """Test that recipes were added to the database."""
        result = self.session.execute(text("SELECT COUNT(*) FROM recipes"))
        count = result.scalar()
        self.assertGreater(count, 0, "No recipes found in the database")
    
    def test_recipe_content(self):
        """Test that recipe content is properly formatted."""
        # Get a sample recipe
        recipe = self.session.execute(
            text("SELECT * FROM recipes LIMIT 1")
        ).fetchone()
        
        # Verify recipe exists
        self.assertIsNotNone(recipe, "No recipe found in the database")
        
        # Verify recipe has required fields
        self.assertIsNotNone(recipe.title, "Recipe title is missing")
        self.assertIsInstance(recipe.ingredients, list, "Recipe ingredients should be a list")
        self.assertIsInstance(recipe.instructions, list, "Recipe instructions should be a list")
        
        # Check if ingredients list has content
        self.assertGreater(len(recipe.ingredients), 0, "Recipe ingredients list is empty")
    
    def test_recipe_categories(self):
        """Test that recipe categories were properly seeded."""
        # Get a recipe with categories
        recipe = self.session.execute(
            text("SELECT * FROM recipes WHERE array_length(categories, 1) > 0 LIMIT 1")
        ).fetchone()
        
        # Verify recipe with categories exists
        self.assertIsNotNone(recipe, "No recipe with categories found in the database")
        
        # Verify categories are correctly stored
        self.assertIsInstance(recipe.categories, list, "Recipe categories should be a list")
        self.assertGreater(len(recipe.categories), 0, "Recipe categories list is empty")
    
    def test_recipe_user_association(self):
        """Test that recipes are associated with a valid user."""
        # Get a sample recipe
        recipe = self.session.execute(
            text("SELECT * FROM recipes LIMIT 1")
        ).fetchone()
        
        # Verify recipe exists
        self.assertIsNotNone(recipe, "No recipe found in the database")
        
        # Verify user_id exists and is valid
        self.assertIsNotNone(recipe.user_id, "Recipe has no associated user_id")
        
        # Check if user exists
        user = self.session.execute(
            text("SELECT * FROM users WHERE id = :user_id"),
            {"user_id": recipe.user_id}
        ).fetchone()
        
        self.assertIsNotNone(user, f"User with ID {recipe.user_id} does not exist")


if __name__ == "__main__":
    unittest.main() 