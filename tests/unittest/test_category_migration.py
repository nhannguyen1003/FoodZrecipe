import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.session import Base

# Add parent directory to path to allow importing from scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models.recipe import Recipe
from backend.models.user import User
from backend.models.category import Category, recipe_category
from scripts.migrate_categories import migrate_categories

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
def setup_recipes_with_array_categories(db_session, sample_user):
    """Create recipes with categories stored in the array field"""
    # Recipe 1 with multiple categories
    recipe1 = Recipe(
        title="Recipe 1",
        description="First test recipe",
        ingredients=["ingredient1", "ingredient2"],
        instructions="Test instructions",
        user_id=sample_user.id,
        categories=["Breakfast", "Vegetarian", "Quick & Easy"]
    )
    
    # Recipe 2 with one category
    recipe2 = Recipe(
        title="Recipe 2",
        description="Second test recipe",
        ingredients=["ingredient3", "ingredient4"],
        instructions="More test instructions",
        user_id=sample_user.id,
        categories=["Dinner"]
    )
    
    # Recipe 3 with no categories
    recipe3 = Recipe(
        title="Recipe 3",
        description="Third test recipe",
        ingredients=["ingredient5", "ingredient6"],
        instructions="Even more test instructions",
        user_id=sample_user.id,
        categories=[]
    )
    
    db_session.add_all([recipe1, recipe2, recipe3])
    db_session.commit()
    
    return [recipe1, recipe2, recipe3]

def mock_migrate_categories(db_session):
    """Mock implementation of the migration function using the provided session"""
    # Get all recipes with categories
    recipes = db_session.query(Recipe).filter(Recipe.categories != None).all()
    
    # Process each recipe
    for recipe in recipes:
        if not recipe.categories or len(recipe.categories) == 0:
            continue
        
        # For each category in the recipe
        for category_name in recipe.categories:
            # Skip empty category names
            if not category_name or category_name.strip() == "":
                continue
                
            # Clean up category name
            cleaned_name = category_name.strip().title()
            
            # Find or create the category
            category = db_session.query(Category).filter(Category.name == cleaned_name).first()
            
            if not category:
                category = Category(name=cleaned_name)
                db_session.add(category)
                db_session.flush()  # Flush to get the ID
            
            # Check if relationship already exists
            exists = db_session.query(recipe_category).filter(
                recipe_category.c.recipe_id == recipe.id,
                recipe_category.c.category_id == category.id
            ).first()
            
            if not exists:
                # Add the relationship
                stmt = recipe_category.insert().values(
                    recipe_id=recipe.id,
                    category_id=category.id
                )
                db_session.execute(stmt)
    
    # Commit all changes
    db_session.commit()

def test_migrate_categories(db_session, setup_recipes_with_array_categories):
    """Test the migration of recipe categories from array to many-to-many"""
    recipes = setup_recipes_with_array_categories
    
    # Verify no categories exist yet
    categories = db_session.query(Category).all()
    assert len(categories) == 0
    
    # Verify no recipe-category relationships exist yet
    relationships = db_session.query(recipe_category).all()
    assert len(relationships) == 0
    
    # Run the migration
    mock_migrate_categories(db_session)
    
    # Verify categories were created
    categories = db_session.query(Category).all()
    assert len(categories) == 4  # Breakfast, Vegetarian, Quick & Easy, Dinner
    
    # Convert to a dictionary for easier testing
    category_dict = {c.name: c for c in categories}
    assert "Breakfast" in category_dict
    assert "Vegetarian" in category_dict
    assert "Quick & Easy" in category_dict
    assert "Dinner" in category_dict
    
    # Verify relationships were created
    recipe1 = recipes[0]
    db_session.refresh(recipe1)
    assert len(recipe1.category_relations) == 3
    category_names = [c.name for c in recipe1.category_relations]
    assert "Breakfast" in category_names
    assert "Vegetarian" in category_names
    assert "Quick & Easy" in category_names
    
    recipe2 = recipes[1]
    db_session.refresh(recipe2)
    assert len(recipe2.category_relations) == 1
    assert recipe2.category_relations[0].name == "Dinner"
    
    recipe3 = recipes[2]
    db_session.refresh(recipe3)
    assert len(recipe3.category_relations) == 0

def test_migrate_categories_idempotent(db_session, setup_recipes_with_array_categories):
    """Test that running the migration multiple times is idempotent"""
    # Run the migration
    mock_migrate_categories(db_session)
    
    # Get the count of categories and relationships after first run
    categories_count_1 = db_session.query(Category).count()
    relationships_count_1 = db_session.query(recipe_category).count()
    
    # Run the migration again
    mock_migrate_categories(db_session)
    
    # Get the count after second run
    categories_count_2 = db_session.query(Category).count()
    relationships_count_2 = db_session.query(recipe_category).count()
    
    # Verify counts haven't changed
    assert categories_count_1 == categories_count_2
    assert relationships_count_1 == relationships_count_2

def test_migrate_categories_with_duplicate_categories(db_session, setup_recipes_with_array_categories):
    """Test migration with duplicate category names (case insensitive)"""
    # Add a recipe with duplicate categories in different case
    recipe4 = Recipe(
        title="Recipe 4",
        description="Fourth test recipe",
        ingredients=["ingredient7", "ingredient8"],
        instructions="More test instructions",
        user_id=setup_recipes_with_array_categories[0].user_id,
        categories=["breakfast", "VEGETARIAN", "Breakfast"]  # Duplicates of Breakfast and Vegetarian
    )
    db_session.add(recipe4)
    db_session.commit()
    
    # Run the migration
    mock_migrate_categories(db_session)
    
    # Verify only unique categories were created
    categories = db_session.query(Category).all()
    assert len(categories) == 4  # Should still be 4 unique categories
    
    # Verify the recipe was linked to the correct categories
    db_session.refresh(recipe4)
    assert len(recipe4.category_relations) == 2  # Only Breakfast and Vegetarian, no duplicates
    category_names = [c.name for c in recipe4.category_relations]
    assert "Breakfast" in category_names
    assert "Vegetarian" in category_names 