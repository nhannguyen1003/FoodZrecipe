import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from main import app
from database.session import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    """Ensure all tables including categories are created before tests run"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Verify categories table exists
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT * FROM categories LIMIT 1"))
        except Exception:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS recipe_category (
                    recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
                    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
                    PRIMARY KEY (recipe_id, category_id)
                )
            """))
            conn.commit()
    
    yield
    # No need to drop tables after tests as we're using a test schema

def test_text_search_with_filtering():
    """Test the text search endpoint with category filtering"""
    response = client.get("/api/v1/search/text?query=chicken&categories=dinner&sort_by=newest&limit=5")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    # If there are results, check that they match the category filter
    if results:
        # For this test to pass, we need at least one recipe with 'chicken' and category 'dinner'
        for recipe in results:
            assert "dinner" in [cat.lower() for cat in recipe.get("categories", [])]

def test_get_all_categories():
    """Test retrieving all categories"""
    response = client.get("/api/v1/search/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    # Categories should be strings
    if categories:
        assert all(isinstance(category, str) for category in categories)

def test_recipe_search_with_sorting():
    """Test the recipe search endpoint with sorting"""
    # Test newest sorting
    response = client.get("/api/v1/search/recipes/search?query=pasta&sort_by=newest&limit=5")
    assert response.status_code == 200
    newest_results = response.json()
    
    # Test relevance sorting
    response = client.get("/api/v1/search/recipes/search?query=pasta&sort_by=relevance&limit=5")
    assert response.status_code == 200
    relevance_results = response.json()
    
    # Results should be different when using different sorting methods
    # Note: This test may fail if there are very few recipes or they happen to sort the same way
    if len(newest_results) > 1 and len(relevance_results) > 1:
        # Check if the order is different (at least one recipe appears in a different position)
        newest_ids = [recipe["id"] for recipe in newest_results]
        relevance_ids = [recipe["id"] for recipe in relevance_results]
        assert newest_ids != relevance_ids or len(newest_ids) != len(relevance_ids) 