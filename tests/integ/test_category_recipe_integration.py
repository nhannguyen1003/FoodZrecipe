import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.session import Base, get_db

from main import app
from backend.models.category import Category
from backend.models.user import User
from backend.models.recipe import Recipe
from backend.core.auth import create_access_token

# Override the dependency to use test database
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    """Setup test database before each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    """Get DB session"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def user(db):
    """Create user for testing"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_admin=False
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def user_token(user):
    """Create user JWT token"""
    return create_access_token({"sub": str(user.id), "admin": False})

@pytest.fixture
def categories(db):
    """Create sample categories"""
    categories = [
        Category(name="Breakfast", description="Morning meals"),
        Category(name="Lunch", description="Midday meals"),
        Category(name="Dinner", description="Evening meals"),
        Category(name="Vegetarian", description="Meat-free recipes")
    ]
    for category in categories:
        db.add(category)
    db.commit()
    return categories

def test_create_recipe_with_categories(user_token, categories):
    """Test creating a recipe with categories"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Get category IDs
    breakfast_id = categories[0].id
    vegetarian_id = categories[3].id
    
    # Create recipe with categories
    recipe_data = {
        "title": "Veggie Breakfast Bowl",
        "description": "A nutritious vegetarian breakfast",
        "ingredients": ["eggs", "spinach", "avocado", "tomatoes"],
        "instructions": "Mix all ingredients in a bowl and enjoy!",
        "category_ids": [breakfast_id, vegetarian_id]
    }
    
    response = client.post("/api/v1/recipes/", json=recipe_data, headers=headers)
    assert response.status_code == 201
    
    recipe_id = response.json()["id"]
    
    # Verify the recipe was created with the correct categories
    # First check in the breakfast category
    response = client.get(f"/api/v1/categories/{breakfast_id}/recipes")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 1
    assert recipes[0]["id"] == recipe_id
    
    # Then check in the vegetarian category
    response = client.get(f"/api/v1/categories/{vegetarian_id}/recipes")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 1
    assert recipes[0]["id"] == recipe_id

def test_update_recipe_categories(user_token, categories, db, user):
    """Test updating a recipe's categories"""
    # First create a recipe
    recipe = Recipe(
        title="Original Recipe",
        description="A test recipe",
        ingredients=["ingredient1", "ingredient2"],
        instructions="Test instructions",
        user_id=user.id
    )
    db.add(recipe)
    db.commit()
    
    recipe_id = recipe.id
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Initially add to breakfast category
    breakfast_id = categories[0].id
    lunch_id = categories[1].id
    dinner_id = categories[2].id
    
    # Add to breakfast
    client.post(f"/api/v1/categories/{breakfast_id}/recipes/{recipe_id}", headers=headers)
    
    # Update to include lunch and dinner instead
    update_data = {
        "title": "Updated Recipe",
        "category_ids": [lunch_id, dinner_id]
    }
    
    response = client.put(f"/api/v1/recipes/{recipe_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    
    # Check the recipe is no longer in breakfast category
    response = client.get(f"/api/v1/categories/{breakfast_id}/recipes")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 0
    
    # Check the recipe is now in lunch and dinner categories
    response = client.get(f"/api/v1/categories/{lunch_id}/recipes")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 1
    
    response = client.get(f"/api/v1/categories/{dinner_id}/recipes")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 1

def test_delete_recipe_removes_from_categories(user_token, categories, db, user):
    """Test that deleting a recipe removes it from all categories"""
    # Create a recipe
    recipe = Recipe(
        title="Recipe to Delete",
        description="This recipe will be deleted",
        ingredients=["ingredient1", "ingredient2"],
        instructions="Test instructions",
        user_id=user.id
    )
    db.add(recipe)
    db.commit()
    
    recipe_id = recipe.id
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Add to all categories
    for category in categories:
        client.post(f"/api/v1/categories/{category.id}/recipes/{recipe_id}", headers=headers)
    
    # Verify the recipe is in all categories
    for category in categories:
        response = client.get(f"/api/v1/categories/{category.id}/recipes")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 1
    
    # Delete the recipe
    response = client.delete(f"/api/v1/recipes/{recipe_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify the recipe is no longer in any category
    for category in categories:
        response = client.get(f"/api/v1/categories/{category.id}/recipes")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 0

def test_search_recipe_by_category(user_token, categories, db, user):
    """Test searching recipes with category filter"""
    # Create test recipes in different categories
    breakfast_id = categories[0].id
    lunch_id = categories[1].id
    
    # Breakfast recipe
    breakfast_recipe = Recipe(
        title="Breakfast Recipe",
        description="A breakfast recipe",
        ingredients=["eggs", "bread"],
        instructions="Cook eggs, toast bread",
        user_id=user.id
    )
    db.add(breakfast_recipe)
    
    # Lunch recipe
    lunch_recipe = Recipe(
        title="Lunch Recipe",
        description="A lunch recipe",
        ingredients=["chicken", "rice"],
        instructions="Cook chicken, serve with rice",
        user_id=user.id
    )
    db.add(lunch_recipe)
    db.commit()
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Add recipes to their respective categories
    client.post(f"/api/v1/categories/{breakfast_id}/recipes/{breakfast_recipe.id}", headers=headers)
    client.post(f"/api/v1/categories/{lunch_id}/recipes/{lunch_recipe.id}", headers=headers)
    
    # Search with breakfast category filter
    response = client.get(f"/api/v1/search?query=recipe&category_ids={breakfast_id}")
    assert response.status_code == 200
    results = response.json()
    
    # Should only return the breakfast recipe
    assert len(results) > 0
    recipe_titles = [r["title"] for r in results]
    assert "Breakfast Recipe" in recipe_titles
    assert "Lunch Recipe" not in recipe_titles
    
    # Search with lunch category filter
    response = client.get(f"/api/v1/search?query=recipe&category_ids={lunch_id}")
    assert response.status_code == 200
    results = response.json()
    
    # Should only return the lunch recipe
    assert len(results) > 0
    recipe_titles = [r["title"] for r in results]
    assert "Lunch Recipe" in recipe_titles
    assert "Breakfast Recipe" not in recipe_titles 