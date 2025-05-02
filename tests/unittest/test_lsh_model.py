"""
Unit tests for verifying the Recipe model with multi-field LSH support
Part of SEARCH-102 implementation.
"""
import pytest
import json
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, JSON, ForeignKey, Text, DateTime
from sqlalchemy.orm import Session, relationship
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import func
from typing import List, Dict, Any, Optional

from tests.unittest.test_models import TestBase, TestUser, UserRole


class TestLSHRecipe(TestBase):
    """Test Recipe model with multi-field LSH support"""
    __tablename__ = "test_lsh_recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    ingredients = Column(JSON, nullable=False)
    instructions = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("test_users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Basic LSH-related fields
    text_feature_vector = Column(JSON, nullable=True)
    text_hash_buckets = Column(JSON, nullable=True)
    
    # Multi-field LSH-related fields
    title_feature_vector = Column(JSON, nullable=True)
    ingredients_feature_vector = Column(JSON, nullable=True)
    instructions_feature_vector = Column(JSON, nullable=True)
    title_hash_buckets = Column(JSON, nullable=True)
    ingredients_hash_buckets = Column(JSON, nullable=True)
    instructions_hash_buckets = Column(JSON, nullable=True)
    
    # Relationship to user
    user = relationship("TestUser", back_populates="lsh_recipes")


# Add a back reference to TestUser
TestUser.lsh_recipes = relationship("TestLSHRecipe", back_populates="user")


@pytest.fixture
def db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestBase.metadata.create_all(bind=engine)
    
    session = Session(bind=engine)
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def test_user(db):
    """Create a test user"""
    user = TestUser(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword",
        role=UserRole.REGULAR,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_lsh_recipes(db, test_user):
    """Create test recipes with multi-field LSH vectors"""
    recipes = [
        TestLSHRecipe(
            title="Chocolate Cake",
            description="Delicious chocolate cake recipe",
            ingredients=json.dumps(["flour", "sugar", "cocoa powder", "eggs", "butter"]),
            instructions="Mix dry ingredients. Add wet ingredients. Bake at 350F for 30 minutes.",
            user_id=test_user.id,
            # Original text vector
            text_feature_vector=json.dumps([0.1, 0.2, 0.3, 0.4]),
            text_hash_buckets=json.dumps([1, 2, 3]),
            # Field-specific vectors
            title_feature_vector=json.dumps([0.5, 0.6, 0.7]),
            ingredients_feature_vector=json.dumps([0.2, 0.3, 0.4, 0.5]),
            instructions_feature_vector=json.dumps([0.1, 0.2, 0.3, 0.4, 0.5]),
            title_hash_buckets=json.dumps([4, 5, 6]),
            ingredients_hash_buckets=json.dumps([7, 8, 9]),
            instructions_hash_buckets=json.dumps([10, 11, 12])
        ),
        TestLSHRecipe(
            title="Pasta Carbonara",
            description="Classic Italian pasta dish",
            ingredients=json.dumps(["pasta", "eggs", "bacon", "parmesan", "black pepper"]),
            instructions="Cook pasta. Fry bacon. Mix eggs and cheese. Combine all while pasta is hot.",
            user_id=test_user.id,
            # Original text vector
            text_feature_vector=json.dumps([0.5, 0.6, 0.7, 0.8]),
            text_hash_buckets=json.dumps([4, 5, 6]),
            # Field-specific vectors
            title_feature_vector=json.dumps([0.3, 0.4, 0.5]),
            ingredients_feature_vector=json.dumps([0.6, 0.7, 0.8, 0.9]),
            instructions_feature_vector=json.dumps([0.5, 0.6, 0.7, 0.8, 0.9]),
            title_hash_buckets=json.dumps([13, 14, 15]),
            ingredients_hash_buckets=json.dumps([16, 17, 18]),
            instructions_hash_buckets=json.dumps([19, 20, 21])
        )
    ]
    
    for recipe in recipes:
        db.add(recipe)
    
    db.commit()
    
    # Refresh the recipes to get their IDs
    for recipe in recipes:
        db.refresh(recipe)
    
    return recipes


class TestMultiFieldLSHModel:
    def test_model_structure(self, db):
        """Test that the model has all required multi-field LSH columns"""
        # Verify the model has the correct columns
        recipe = TestLSHRecipe()
        
        # Basic fields
        assert hasattr(recipe, 'id')
        assert hasattr(recipe, 'title')
        assert hasattr(recipe, 'ingredients')
        assert hasattr(recipe, 'instructions')
        
        # Original LSH fields
        assert hasattr(recipe, 'text_feature_vector')
        assert hasattr(recipe, 'text_hash_buckets')
        
        # Multi-field LSH fields
        assert hasattr(recipe, 'title_feature_vector')
        assert hasattr(recipe, 'ingredients_feature_vector') 
        assert hasattr(recipe, 'instructions_feature_vector')
        assert hasattr(recipe, 'title_hash_buckets')
        assert hasattr(recipe, 'ingredients_hash_buckets')
        assert hasattr(recipe, 'instructions_hash_buckets')
    
    def test_store_and_retrieve_multi_field_vectors(self, db, test_user):
        """Test storing and retrieving field-specific feature vectors"""
        # Create a recipe with multi-field vectors
        recipe = TestLSHRecipe(
            title="Apple Pie",
            description="Traditional apple pie",
            ingredients=json.dumps(["apples", "flour", "sugar", "cinnamon", "butter"]),
            instructions="Make pie crust. Fill with apple mixture. Bake until golden.",
            user_id=test_user.id,
            # Field-specific vectors
            title_feature_vector=json.dumps([0.1, 0.2, 0.3]),
            ingredients_feature_vector=json.dumps([0.4, 0.5, 0.6, 0.7]),
            instructions_feature_vector=json.dumps([0.8, 0.9, 1.0, 1.1, 1.2]),
            title_hash_buckets=json.dumps([1, 2, 3]),
            ingredients_hash_buckets=json.dumps([4, 5, 6]),
            instructions_hash_buckets=json.dumps([7, 8, 9])
        )
        
        # Add the recipe to the database
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        
        # Retrieve the recipe from the database
        retrieved_recipe = db.query(TestLSHRecipe).filter(TestLSHRecipe.id == recipe.id).first()
        
        # Verify field-specific vectors were properly stored and retrieved
        assert json.loads(retrieved_recipe.title_feature_vector) == [0.1, 0.2, 0.3]
        assert json.loads(retrieved_recipe.ingredients_feature_vector) == [0.4, 0.5, 0.6, 0.7]
        assert json.loads(retrieved_recipe.instructions_feature_vector) == [0.8, 0.9, 1.0, 1.1, 1.2]
        
        # Verify field-specific hash buckets were properly stored and retrieved
        assert json.loads(retrieved_recipe.title_hash_buckets) == [1, 2, 3]
        assert json.loads(retrieved_recipe.ingredients_hash_buckets) == [4, 5, 6]
        assert json.loads(retrieved_recipe.instructions_hash_buckets) == [7, 8, 9]
    
    def test_multi_field_and_legacy_coexistence(self, test_lsh_recipes):
        """Test that both multi-field and legacy vectors coexist"""
        recipe = test_lsh_recipes[0]  # Get the first test recipe
        
        # Verify legacy vectors exist
        assert recipe.text_feature_vector is not None
        assert recipe.text_hash_buckets is not None
        
        # Verify multi-field vectors exist
        assert recipe.title_feature_vector is not None
        assert recipe.ingredients_feature_vector is not None
        assert recipe.instructions_feature_vector is not None
        
        # Verify hash buckets exist
        assert recipe.title_hash_buckets is not None
        assert recipe.ingredients_hash_buckets is not None
        assert recipe.instructions_hash_buckets is not None
        
        # Verify content matches expectations
        title_vector = json.loads(recipe.title_feature_vector)
        assert isinstance(title_vector, list)
        assert len(title_vector) > 0
    
    def test_different_dimension_vectors(self, db, test_user):
        """Test storing vectors with different dimensions for each field"""
        # Create a recipe with varying vector dimensions
        recipe = TestLSHRecipe(
            title="Green Salad",
            description="Fresh green salad",
            ingredients=json.dumps(["lettuce", "cucumber", "avocado", "olive oil"]),
            instructions="Wash and chop vegetables. Combine in bowl. Add dressing.",
            user_id=test_user.id,
            # Field-specific vectors with different dimensions
            title_feature_vector=json.dumps([0.1, 0.2]),  # 2-dim
            ingredients_feature_vector=json.dumps([0.3, 0.4, 0.5, 0.6]),  # 4-dim
            instructions_feature_vector=json.dumps([0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]),  # 8-dim
            title_hash_buckets=json.dumps([1, 2]),
            ingredients_hash_buckets=json.dumps([3, 4, 5, 6]),
            instructions_hash_buckets=json.dumps([7, 8, 9, 10])
        )
        
        # Add the recipe to the database
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        
        # Retrieve the recipe from the database
        retrieved_recipe = db.query(TestLSHRecipe).filter(TestLSHRecipe.id == recipe.id).first()
        
        # Verify vectors with different dimensions were properly stored
        assert len(json.loads(retrieved_recipe.title_feature_vector)) == 2
        assert len(json.loads(retrieved_recipe.ingredients_feature_vector)) == 4
        assert len(json.loads(retrieved_recipe.instructions_feature_vector)) == 8 