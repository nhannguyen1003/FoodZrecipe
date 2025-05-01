import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.session import Base
from database.repositories.category_repository import CategoryRepository
from backend.models.category import Category
from backend.models.recipe import Recipe
from backend.models.user import User
import datetime

# Test database URL
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """Create a SQLite in-memory database for testing"""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)

@pytest.fixture
def category_repo(db_session):
    """Create a CategoryRepository instance for testing"""
    return CategoryRepository(db_session)

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_categories(db_session):
    """Create sample categories for testing"""
    categories = [
        Category(name="Breakfast", description="Morning meals"),
        Category(name="Lunch", description="Midday meals"),
        Category(name="Dinner", description="Evening meals")
    ]
    for category in categories:
        db_session.add(category)
    db_session.commit()
    return categories

@pytest.fixture
def sample_recipe(db_session, sample_user):
    """Create a sample recipe for testing"""
    recipe = Recipe(
        title="Test Recipe",
        description="A test recipe",
        ingredients=["ingredient1", "ingredient2"],
        instructions="Test instructions",
        user_id=sample_user.id,
        categories=["Breakfast", "Quick"]
    )
    db_session.add(recipe)
    db_session.commit()
    return recipe

def test_get_by_name(category_repo, sample_categories):
    """Test getting a category by name"""
    # Get an existing category
    category = category_repo.get_by_name("Breakfast")
    assert category is not None
    assert category.name == "Breakfast"
    assert category.description == "Morning meals"
    
    # Get a non-existent category
    non_existent = category_repo.get_by_name("NonExistent")
    assert non_existent is None

def test_get_all_with_recipe_count(db_session, category_repo, sample_categories, sample_recipe, sample_user):
    """Test getting all categories with recipe counts"""
    # First, create a relationship between the recipe and a category
    category_id = sample_categories[0].id  # Breakfast
    recipe_id = sample_recipe.id
    
    category_repo.add_recipe_to_category(category_id, recipe_id)
    
    # Get all categories with counts
    results = category_repo.get_all_with_recipe_count()
    
    # Check the results
    assert len(results) == 3  # We have 3 sample categories
    
    # Convert results to a dict for easier testing
    category_counts = {category.name: count for category, count in results}
    
    # Breakfast should have 1 recipe
    assert category_counts["Breakfast"] == 1
    
    # Lunch and Dinner should have 0 recipes
    assert category_counts["Lunch"] == 0
    assert category_counts["Dinner"] == 0

def test_add_recipe_to_category(db_session, category_repo, sample_categories, sample_recipe):
    """Test adding a recipe to a category"""
    category_id = sample_categories[0].id  # Breakfast
    recipe_id = sample_recipe.id
    
    # Add recipe to category
    success = category_repo.add_recipe_to_category(category_id, recipe_id)
    assert success is True
    
    # Verify relationship was created
    categories = category_repo.get_categories_for_recipe(recipe_id)
    assert len(categories) == 1
    assert categories[0].name == "Breakfast"
    
    # Try adding the same relationship again (should return False)
    success = category_repo.add_recipe_to_category(category_id, recipe_id)
    assert success is False

def test_remove_recipe_from_category(db_session, category_repo, sample_categories, sample_recipe):
    """Test removing a recipe from a category"""
    category_id = sample_categories[0].id  # Breakfast
    recipe_id = sample_recipe.id
    
    # First add the recipe to the category
    category_repo.add_recipe_to_category(category_id, recipe_id)
    
    # Verify relationship exists
    categories = category_repo.get_categories_for_recipe(recipe_id)
    assert len(categories) == 1
    
    # Remove the recipe from the category
    success = category_repo.remove_recipe_from_category(category_id, recipe_id)
    assert success is True
    
    # Verify relationship was removed
    categories = category_repo.get_categories_for_recipe(recipe_id)
    assert len(categories) == 0
    
    # Try removing a relationship that doesn't exist
    success = category_repo.remove_recipe_from_category(category_id, recipe_id)
    assert success is False

def test_get_recipes_by_category(db_session, category_repo, sample_categories, sample_recipe, sample_user):
    """Test getting recipes by category"""
    category_id = sample_categories[0].id  # Breakfast
    recipe_id = sample_recipe.id
    
    # Add recipe to category
    category_repo.add_recipe_to_category(category_id, recipe_id)
    
    # Add another recipe to the same category
    recipe2 = Recipe(
        title="Another Recipe",
        description="Another test recipe",
        ingredients=["ingredient1", "ingredient2"],
        instructions="Test instructions",
        user_id=sample_user.id
    )
    db_session.add(recipe2)
    db_session.commit()
    
    category_repo.add_recipe_to_category(category_id, recipe2.id)
    
    # Get recipes for the category
    recipes = category_repo.get_recipes_by_category(category_id)
    
    # Verify the recipes
    assert len(recipes) == 2
    recipe_titles = [r.title for r in recipes]
    assert "Test Recipe" in recipe_titles
    assert "Another Recipe" in recipe_titles
    
    # Test pagination
    recipes = category_repo.get_recipes_by_category(category_id, limit=1)
    assert len(recipes) == 1

def test_get_categories_for_recipe(db_session, category_repo, sample_categories, sample_recipe):
    """Test getting categories for a recipe"""
    recipe_id = sample_recipe.id
    
    # Add recipe to multiple categories
    category_repo.add_recipe_to_category(sample_categories[0].id, recipe_id)  # Breakfast
    category_repo.add_recipe_to_category(sample_categories[1].id, recipe_id)  # Lunch
    
    # Get categories for the recipe
    categories = category_repo.get_categories_for_recipe(recipe_id)
    
    # Verify the categories
    assert len(categories) == 2
    category_names = [c.name for c in categories]
    assert "Breakfast" in category_names
    assert "Lunch" in category_names
    assert "Dinner" not in category_names 