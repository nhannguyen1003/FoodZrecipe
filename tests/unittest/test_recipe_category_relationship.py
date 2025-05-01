import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.session import Base
from backend.models.category import Category, recipe_category
from backend.models.recipe import Recipe
from backend.models.user import User
from database.repositories.recipe_repository import RecipeRepository

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
def recipe_repo(db_session):
    """Create a RecipeRepository instance for testing"""
    return RecipeRepository(db_session)

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
        user_id=sample_user.id
    )
    db_session.add(recipe)
    db_session.commit()
    return recipe

def test_recipe_category_relationship(db_session, sample_recipe, sample_categories):
    """Test the many-to-many relationship between recipes and categories"""
    # Get recipe and category
    recipe = sample_recipe
    category = sample_categories[0]
    
    # Add the relationship
    stmt = recipe_category.insert().values(
        recipe_id=recipe.id,
        category_id=category.id
    )
    db_session.execute(stmt)
    db_session.commit()
    
    # Refresh the recipe from the database to get the relationship
    db_session.refresh(recipe)
    
    # Check the relationship
    assert len(recipe.category_relations) == 1
    assert recipe.category_relations[0].id == category.id
    assert recipe.category_relations[0].name == "Breakfast"
    
    # Check the reverse relationship
    assert len(category.recipes) == 1
    assert category.recipes[0].id == recipe.id
    assert category.recipes[0].title == "Test Recipe"

def test_recipe_multiple_categories(db_session, sample_recipe, sample_categories):
    """Test a recipe can belong to multiple categories"""
    # Add the recipe to multiple categories
    for category in sample_categories:
        stmt = recipe_category.insert().values(
            recipe_id=sample_recipe.id,
            category_id=category.id
        )
        db_session.execute(stmt)
    db_session.commit()
    
    # Refresh the recipe from the database
    db_session.refresh(sample_recipe)
    
    # Check the relationships
    assert len(sample_recipe.category_relations) == 3
    category_names = [c.name for c in sample_recipe.category_relations]
    assert "Breakfast" in category_names
    assert "Lunch" in category_names
    assert "Dinner" in category_names

def test_category_multiple_recipes(db_session, sample_categories, sample_user):
    """Test a category can have multiple recipes"""
    # Create multiple recipes
    recipes = [
        Recipe(title="Recipe 1", ingredients=["ingredient1"], instructions="Instructions 1", user_id=sample_user.id),
        Recipe(title="Recipe 2", ingredients=["ingredient2"], instructions="Instructions 2", user_id=sample_user.id),
        Recipe(title="Recipe 3", ingredients=["ingredient3"], instructions="Instructions 3", user_id=sample_user.id)
    ]
    for recipe in recipes:
        db_session.add(recipe)
    db_session.commit()
    
    # Add all recipes to the first category
    category = sample_categories[0]
    for recipe in recipes:
        stmt = recipe_category.insert().values(
            recipe_id=recipe.id,
            category_id=category.id
        )
        db_session.execute(stmt)
    db_session.commit()
    
    # Refresh the category from the database
    db_session.refresh(category)
    
    # Check the relationships
    assert len(category.recipes) == 3
    recipe_titles = [r.title for r in category.recipes]
    assert "Recipe 1" in recipe_titles
    assert "Recipe 2" in recipe_titles
    assert "Recipe 3" in recipe_titles

def test_delete_recipe_cascade(db_session, sample_recipe, sample_categories):
    """Test deleting a recipe also removes the relationships to categories"""
    # Add the recipe to all categories
    for category in sample_categories:
        stmt = recipe_category.insert().values(
            recipe_id=sample_recipe.id,
            category_id=category.id
        )
        db_session.execute(stmt)
    db_session.commit()
    
    # Verify the relationships exist
    relationships = db_session.query(recipe_category).filter(
        recipe_category.c.recipe_id == sample_recipe.id
    ).all()
    assert len(relationships) == 3
    
    # Delete the recipe
    db_session.delete(sample_recipe)
    db_session.commit()
    
    # Verify the relationships are gone
    relationships = db_session.query(recipe_category).filter(
        recipe_category.c.recipe_id == sample_recipe.id
    ).all()
    assert len(relationships) == 0
    
    # Verify the categories still exist
    categories = db_session.query(Category).all()
    assert len(categories) == 3

def test_delete_category_cascade(db_session, sample_recipe, sample_categories):
    """Test deleting a category also removes the relationships to recipes"""
    category = sample_categories[0]
    
    # Add the recipe to the category
    stmt = recipe_category.insert().values(
        recipe_id=sample_recipe.id,
        category_id=category.id
    )
    db_session.execute(stmt)
    db_session.commit()
    
    # Verify the relationship exists
    relationship = db_session.query(recipe_category).filter(
        recipe_category.c.recipe_id == sample_recipe.id,
        recipe_category.c.category_id == category.id
    ).first()
    assert relationship is not None
    
    # Delete the category
    db_session.delete(category)
    db_session.commit()
    
    # Verify the relationship is gone
    relationship = db_session.query(recipe_category).filter(
        recipe_category.c.recipe_id == sample_recipe.id,
        recipe_category.c.category_id == category.id
    ).first()
    assert relationship is None
    
    # Verify the recipe still exists
    recipe = db_session.query(Recipe).filter(Recipe.id == sample_recipe.id).first()
    assert recipe is not None

def test_create_recipe_with_categories(db_session, recipe_repo, sample_categories, sample_user):
    """Test creating a recipe with categories using the repository"""
    # Create a recipe with categories
    recipe_data = {
        "title": "Recipe with Categories",
        "description": "A recipe with categories",
        "ingredients": ["ingredient1", "ingredient2"],
        "instructions": "Test instructions",
        "category_ids": [sample_categories[0].id, sample_categories[1].id]
    }
    
    # Create the recipe
    recipe = recipe_repo.create_with_categories(recipe_data, sample_user.id)
    
    # Verify the recipe was created with the correct categories
    assert recipe.id is not None
    assert recipe.title == "Recipe with Categories"
    
    # Refresh the recipe to get the relationships
    db_session.refresh(recipe)
    
    # Verify the categories
    assert len(recipe.category_relations) == 2
    category_names = [c.name for c in recipe.category_relations]
    assert "Breakfast" in category_names
    assert "Lunch" in category_names 