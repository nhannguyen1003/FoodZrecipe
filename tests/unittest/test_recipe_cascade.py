import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.user import User, UserRole
from backend.models.recipe import Recipe
from backend.core.security import get_password_hash

def test_recipe_cascade_on_user_delete(db_session: Session):
    """Test that recipes are deleted when the user is deleted."""
    # Create a test user
    now = datetime.utcnow()
    user = User(
        username="cascadeuser",
        email="cascade@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.REGULAR,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create multiple recipes for the user
    recipe_ids = []
    for i in range(5):
        recipe = Recipe(
            title=f"Cascade Recipe {i}",
            description=f"Description {i}",
            ingredients=[f"Ingredient {j}" for j in range(3)],
            instructions=[f"Step {j}" for j in range(3)],
            user_id=user.id,
            created_at=now,
            updated_at=now
        )
        db_session.add(recipe)
        db_session.flush()
        recipe_ids.append(recipe.id)
    
    db_session.commit()
    
    # Verify recipes exist
    recipes = db_session.query(Recipe).filter(Recipe.user_id == user.id).all()
    assert len(recipes) == 5
    
    # Delete the user
    db_session.delete(user)
    db_session.commit()
    
    # Verify all recipes are deleted
    for recipe_id in recipe_ids:
        recipe = db_session.query(Recipe).filter(Recipe.id == recipe_id).first()
        assert recipe is None

def test_user_recipe_count(db_session: Session):
    """Test user-recipe relationship access."""
    # Create a test user
    now = datetime.utcnow()
    user = User(
        username="recipeowner",
        email="owner@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.REGULAR,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Initially no recipes
    assert len(user.recipes) == 0
    
    # Create recipes through the relationship
    for i in range(3):
        recipe = Recipe(
            title=f"Relation Recipe {i}",
            description=f"Description {i}",
            ingredients=[f"Ingredient {j}" for j in range(3)],
            instructions=[f"Step {j}" for j in range(3)],
            user_id=user.id,
            created_at=now,
            updated_at=now
        )
        db_session.add(recipe)
    
    db_session.commit()
    db_session.refresh(user)
    
    # Verify recipes count
    assert len(user.recipes) == 3
    
    # Access recipe properties through the relationship
    for recipe in user.recipes:
        assert recipe.title.startswith("Relation Recipe")
        assert recipe.user_id == user.id
        
        # Verify bidirectional relationship
        assert recipe.user.id == user.id
        assert recipe.user.username == "recipeowner" 