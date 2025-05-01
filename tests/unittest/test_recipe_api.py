import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from main import app
from database.session import get_db, Base
from backend.models.recipe import Recipe
from backend.core.security import create_access_token
from backend.models.user import User

# Create test client
client = TestClient(app)

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Create dependencies with test session
    def override_get_db():
        try:
            yield session
            session.commit()
        finally:
            session.close()
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides = {}

@pytest.fixture
def test_user(db_session):
    # Create a test user
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$Isz1Z8Iu22vZIP2jJNbOhuCQ3eTlrVYZ/3sgIJXfaCFNTn3GEqMj2",  # "testpassword"
        is_active=True,
        role="regular"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_recipe(db_session, test_user):
    # Create a test recipe
    recipe = Recipe(
        id=1,
        title="Test Recipe",
        description="A test recipe description",
        ingredients=["Ingredient 1", "Ingredient 2"],
        instructions="Step 1. Do this. Step 2. Do that.",
        user_id=test_user.id
    )
    db_session.add(recipe)
    db_session.commit()
    return recipe

@pytest.fixture
def authenticated_client(test_user):
    # Create access token for the test user
    access_token = create_access_token({"sub": test_user.username})
    
    # Return a client with auth headers
    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {access_token}"}
    return client

@pytest.fixture
def mock_recipe_repository():
    with patch("backend.api.recipe.recipe_repository") as mock:
        yield mock

class TestRecipeAPI:
    def test_get_recipes(self, db_session, test_recipe, mock_recipe_repository):
        """Test get_recipes endpoint"""
        # Setup mock return value
        mock_recipe_repository.get_multi.return_value = [test_recipe]
        
        # Call API
        response = client.get("/api/recipes/")
        
        # Check response
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Test Recipe"
        mock_recipe_repository.get_multi.assert_called_once()
    
    def test_get_recipes_with_category(self, db_session, test_recipe, mock_recipe_repository):
        """Test get_recipes endpoint with category filter"""
        # Setup mock return value
        mock_recipe_repository.get_by_category.return_value = [test_recipe]
        
        # Call API
        response = client.get("/api/recipes/?category=dinner")
        
        # Check response
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_recipe_repository.get_by_category.assert_called_once_with(db_session, category="dinner", skip=0, limit=100)
    
    def test_get_recipes_with_user_id(self, db_session, test_recipe, mock_recipe_repository):
        """Test get_recipes endpoint with user_id filter"""
        # Setup mock return value
        mock_recipe_repository.get_by_user_id.return_value = [test_recipe]
        
        # Call API
        response = client.get("/api/recipes/?user_id=1")
        
        # Check response
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_recipe_repository.get_by_user_id.assert_called_once_with(db_session, user_id=1, skip=0, limit=100)
    
    def test_get_my_recipes(self, db_session, test_recipe, authenticated_client, mock_recipe_repository):
        """Test get_my_recipes endpoint"""
        # Setup mock return value
        mock_recipe_repository.get_by_user_id.return_value = [test_recipe]
        
        # Call API
        response = authenticated_client.get("/api/recipes/mine")
        
        # Check response
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_recipe_repository.get_by_user_id.assert_called_once()
    
    def test_get_recipe(self, db_session, test_recipe, mock_recipe_repository):
        """Test get_recipe endpoint"""
        # Setup mock return value
        mock_recipe_repository.get.return_value = test_recipe
        
        # Call API
        response = client.get("/api/recipes/1")
        
        # Check response
        assert response.status_code == 200
        assert response.json()["title"] == "Test Recipe"
        mock_recipe_repository.get.assert_called_once_with(db_session, id=1)
    
    def test_get_recipe_not_found(self, db_session, mock_recipe_repository):
        """Test get_recipe endpoint with non-existent ID"""
        # Setup mock return value
        mock_recipe_repository.get.return_value = None
        
        # Call API
        response = client.get("/api/recipes/999")
        
        # Check response
        assert response.status_code == 404
        assert "Recipe not found" in response.json()["detail"]
    
    def test_delete_recipe(self, db_session, test_recipe, authenticated_client, mock_recipe_repository):
        """Test delete_recipe endpoint"""
        # Setup mock return values
        mock_recipe_repository.get.return_value = test_recipe
        mock_recipe_repository.remove.return_value = test_recipe
        
        # Call API
        response = authenticated_client.delete("/api/recipes/1")
        
        # Check response
        assert response.status_code == 200
        assert response.json()["title"] == "Test Recipe"
        mock_recipe_repository.remove.assert_called_once_with(db_session, id=1)
    
    def test_delete_recipe_unauthorized(self, db_session, authenticated_client, mock_recipe_repository):
        """Test delete_recipe endpoint with unauthorized user"""
        # Create a recipe owned by a different user
        unauthorized_recipe = Recipe(
            id=2,
            title="Unauthorized Recipe",
            description="A recipe owned by someone else",
            ingredients=["Ingredient 1", "Ingredient 2"],
            instructions="Instructions here",
            user_id=999  # Different user ID
        )
        
        # Setup mock return value
        mock_recipe_repository.get.return_value = unauthorized_recipe
        
        # Call API
        response = authenticated_client.delete("/api/recipes/2")
        
        # Check response
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
        mock_recipe_repository.remove.assert_not_called()
    
    def test_search_recipes(self, db_session, test_recipe, mock_recipe_repository):
        """Test search_recipes endpoint"""
        # Setup mock return value
        mock_recipe_repository.search_by_text.return_value = [test_recipe]
        
        # Call API
        response = client.get("/api/recipes/search?query=test")
        
        # Check response
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Test Recipe"
        mock_recipe_repository.search_by_text.assert_called_once_with(db_session, query="test", skip=0, limit=20) 