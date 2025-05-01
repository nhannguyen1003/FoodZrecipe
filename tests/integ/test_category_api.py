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
def admin_user(db):
    """Create admin user for testing"""
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="hashed_password",
        is_admin=True
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def normal_user(db):
    """Create normal user for testing"""
    user = User(
        username="user",
        email="user@example.com",
        full_name="Regular User",
        hashed_password="hashed_password",
        is_admin=False
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def admin_token(admin_user):
    """Create admin JWT token"""
    return create_access_token({"sub": str(admin_user.id), "admin": True})

@pytest.fixture
def user_token(normal_user):
    """Create user JWT token"""
    return create_access_token({"sub": str(normal_user.id), "admin": False})

@pytest.fixture
def sample_categories(db):
    """Create sample categories"""
    categories = [
        Category(name="Breakfast", description="Morning meals"),
        Category(name="Lunch", description="Midday meals"),
        Category(name="Dinner", description="Evening meals")
    ]
    for category in categories:
        db.add(category)
    db.commit()
    return categories

@pytest.fixture
def sample_recipe(db, normal_user):
    """Create a sample recipe"""
    recipe = Recipe(
        title="Test Recipe",
        description="A test recipe",
        ingredients=["ingredient1", "ingredient2"],
        instructions="Test instructions",
        user_id=normal_user.id
    )
    db.add(recipe)
    db.commit()
    return recipe

def test_get_all_categories(sample_categories):
    """Test getting all categories"""
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    
    # Verify returned data
    category_names = [category["name"] for category in data]
    assert "Breakfast" in category_names
    assert "Lunch" in category_names
    assert "Dinner" in category_names
    
    # Verify the recipe_count field is included
    for category in data:
        assert "recipe_count" in category
        assert category["recipe_count"] == 0

def test_get_category_by_id(sample_categories):
    """Test getting a specific category by ID"""
    category_id = sample_categories[0].id
    response = client.get(f"/api/v1/categories/{category_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == "Breakfast"
    assert data["description"] == "Morning meals"

def test_get_category_not_found():
    """Test getting a non-existent category"""
    response = client.get("/api/v1/categories/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"

def test_create_category_admin(admin_token):
    """Test creating a category as admin"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "name": "New Category",
        "description": "A new category for testing"
    }
    response = client.post("/api/v1/categories/", json=data, headers=headers)
    assert response.status_code == 201
    
    created_category = response.json()
    assert created_category["name"] == "New Category"
    assert created_category["description"] == "A new category for testing"
    assert "id" in created_category
    assert "created_at" in created_category

def test_create_category_normal_user(user_token):
    """Test creating a category as a normal user (should be forbidden)"""
    headers = {"Authorization": f"Bearer {user_token}"}
    data = {
        "name": "New Category",
        "description": "A new category for testing"
    }
    response = client.post("/api/v1/categories/", json=data, headers=headers)
    assert response.status_code == 403

def test_create_category_duplicate_name(admin_token, sample_categories):
    """Test creating a category with a duplicate name"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "name": "Breakfast",  # Already exists
        "description": "Another breakfast category"
    }
    response = client.post("/api/v1/categories/", json=data, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_update_category_admin(admin_token, sample_categories):
    """Test updating a category as admin"""
    category_id = sample_categories[0].id
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "name": "Updated Breakfast",
        "description": "Updated description"
    }
    response = client.put(f"/api/v1/categories/{category_id}", json=data, headers=headers)
    assert response.status_code == 200
    
    updated_category = response.json()
    assert updated_category["name"] == "Updated Breakfast"
    assert updated_category["description"] == "Updated description"

def test_update_category_normal_user(user_token, sample_categories):
    """Test updating a category as a normal user (should be forbidden)"""
    category_id = sample_categories[0].id
    headers = {"Authorization": f"Bearer {user_token}"}
    data = {
        "name": "Updated Breakfast",
        "description": "Updated description"
    }
    response = client.put(f"/api/v1/categories/{category_id}", json=data, headers=headers)
    assert response.status_code == 403

def test_delete_category_admin(admin_token, sample_categories):
    """Test deleting a category as admin"""
    category_id = sample_categories[0].id
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.delete(f"/api/v1/categories/{category_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify the category was deleted
    response = client.get(f"/api/v1/categories/{category_id}")
    assert response.status_code == 404

def test_delete_category_normal_user(user_token, sample_categories):
    """Test deleting a category as a normal user (should be forbidden)"""
    category_id = sample_categories[0].id
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.delete(f"/api/v1/categories/{category_id}", headers=headers)
    assert response.status_code == 403

def test_get_recipes_by_category(db, sample_categories, sample_recipe):
    """Test getting recipes by category"""
    category_id = sample_categories[0].id
    recipe_id = sample_recipe.id
    
    # Add the recipe to the category
    from backend.models.category import recipe_category
    stmt = recipe_category.insert().values(
        recipe_id=recipe_id,
        category_id=category_id
    )
    db.execute(stmt)
    db.commit()
    
    # Get recipes in the category
    response = client.get(f"/api/v1/categories/{category_id}/recipes")
    assert response.status_code == 200
    
    recipes = response.json()
    assert len(recipes) == 1
    assert recipes[0]["id"] == recipe_id
    assert recipes[0]["title"] == "Test Recipe"

def test_get_recipes_by_category_empty(sample_categories):
    """Test getting recipes for a category with no recipes"""
    category_id = sample_categories[0].id
    response = client.get(f"/api/v1/categories/{category_id}/recipes")
    assert response.status_code == 200
    
    recipes = response.json()
    assert len(recipes) == 0

def test_add_recipe_to_category(user_token, sample_categories, sample_recipe):
    """Test adding a recipe to a category"""
    category_id = sample_categories[0].id
    recipe_id = sample_recipe.id
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = client.post(f"/api/v1/categories/{category_id}/recipes/{recipe_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify the recipe was added to the category
    response = client.get(f"/api/v1/categories/{category_id}/recipes")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 1
    assert recipes[0]["id"] == recipe_id

def test_add_recipe_to_category_duplicate(user_token, db, sample_categories, sample_recipe):
    """Test adding a recipe to a category when it's already in the category"""
    category_id = sample_categories[0].id
    recipe_id = sample_recipe.id
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # First add the recipe to the category
    from backend.models.category import recipe_category
    stmt = recipe_category.insert().values(
        recipe_id=recipe_id,
        category_id=category_id
    )
    db.execute(stmt)
    db.commit()
    
    # Try to add it again
    response = client.post(f"/api/v1/categories/{category_id}/recipes/{recipe_id}", headers=headers)
    assert response.status_code == 400
    assert "already in this category" in response.json()["detail"]

def test_remove_recipe_from_category(user_token, db, sample_categories, sample_recipe):
    """Test removing a recipe from a category"""
    category_id = sample_categories[0].id
    recipe_id = sample_recipe.id
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # First add the recipe to the category
    from backend.models.category import recipe_category
    stmt = recipe_category.insert().values(
        recipe_id=recipe_id,
        category_id=category_id
    )
    db.execute(stmt)
    db.commit()
    
    # Remove the recipe from the category
    response = client.delete(f"/api/v1/categories/{category_id}/recipes/{recipe_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify the recipe was removed from the category
    response = client.get(f"/api/v1/categories/{category_id}/recipes")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 0

def test_remove_recipe_from_category_not_in_category(user_token, sample_categories, sample_recipe):
    """Test removing a recipe from a category when it's not in the category"""
    category_id = sample_categories[0].id
    recipe_id = sample_recipe.id
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = client.delete(f"/api/v1/categories/{category_id}/recipes/{recipe_id}", headers=headers)
    assert response.status_code == 400
    assert "not in this category" in response.json()["detail"] 