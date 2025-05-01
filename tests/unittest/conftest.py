import os
import sys
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import settings
from database.session import Base
from backend.models.user import User, UserRole
from backend.models.recipe import Recipe
from backend.core.security import get_password_hash

# Use the same database but with a test schema
TEST_SCHEMA = "test_schema"

@pytest.fixture(scope="session")
def engine():
    """Create an SQLAlchemy engine for testing."""
    engine = create_engine(settings.DATABASE_URL)
    
    # Create test schema if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}"))
        conn.commit()
    
    # Configure engine to use the test schema
    engine.update_execution_options(schema_translate_map={None: TEST_SCHEMA})
    
    return engine

@pytest.fixture(scope="session")
def create_tables(engine):
    """Create database tables."""
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(engine, create_tables):
    """Create a new database session for a test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    # First check if the user already exists
    existing_user = db_session.query(User).filter(User.username == "testuser").first()
    if existing_user:
        return existing_user
        
    now = datetime.utcnow()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        role=UserRole.REGULAR,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_admin(db_session):
    """Create a test admin user."""
    # First check if the admin already exists
    existing_admin = db_session.query(User).filter(User.username == "testadmin").first()
    if existing_admin:
        return existing_admin
        
    now = datetime.utcnow()
    admin = User(
        username="testadmin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword"),
        role=UserRole.ADMIN,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture
def test_recipe(db_session, test_user):
    """Create a test recipe."""
    # First check if the recipe already exists
    existing_recipe = db_session.query(Recipe).filter(
        Recipe.title == "Test Recipe",
        Recipe.user_id == test_user.id
    ).first()
    if existing_recipe:
        return existing_recipe
        
    now = datetime.now()
    recipe = Recipe(
        title="Test Recipe",
        description="A test recipe description",
        ingredients=["Ingredient 1", "Ingredient 2"],
        instructions=["Step 1", "Step 2"],
        user_id=test_user.id,
        created_at=now,
        updated_at=now
    )
    db_session.add(recipe)
    db_session.commit()
    db_session.refresh(recipe)
    return recipe

@pytest.fixture
def test_recipes_with_lsh(db_session, test_user):
    """Create test recipes with LSH feature vectors and hash buckets."""
    # First check if any LSH recipes already exist
    existing_lsh_recipes = db_session.query(Recipe).filter(
        Recipe.text_hash_buckets.isnot(None)
    ).all()
    
    if existing_lsh_recipes:
        return existing_lsh_recipes
    
    now = datetime.now()
    
    recipes = [
        Recipe(
            title="Pancakes with LSH",
            description="Classic breakfast recipe",
            ingredients=["flour", "eggs", "milk", "sugar"],
            instructions=["Mix", "Cook", "Serve"],
            categories=["breakfast", "sweet"],
            prep_time=10,
            cook_time=15,
            servings=4,
            user_id=test_user.id,
            text_feature_vector=[0.1, 0.2, 0.3, 0.4],
            text_hash_buckets=[1, 3, 5],
            image_feature_vector=[0.2, 0.3, 0.4, 0.5],
            image_hash_buckets=[2, 4, 6],
            combined_hash_buckets=[1, 2, 5],
            created_at=now,
            updated_at=now
        ),
        Recipe(
            title="Carbonara with LSH",
            description="Italian pasta dish",
            ingredients=["pasta", "eggs", "cheese", "bacon"],
            instructions=["Cook pasta", "Mix ingredients", "Serve hot"],
            categories=["dinner", "pasta", "italian"],
            prep_time=15,
            cook_time=25,
            servings=2,
            user_id=test_user.id,
            text_feature_vector=[0.3, 0.4, 0.5, 0.6],
            text_hash_buckets=[5, 7, 9],
            image_feature_vector=[0.4, 0.5, 0.6, 0.7],
            image_hash_buckets=[4, 6, 8],
            combined_hash_buckets=[5, 6, 9],
            created_at=now,
            updated_at=now
        ),
        Recipe(
            title="Cake with LSH",
            description="Rich dessert",
            ingredients=["flour", "sugar", "chocolate", "eggs"],
            instructions=["Mix dry ingredients", "Add wet ingredients", "Bake", "Frost"],
            categories=["dessert", "baking", "sweet"],
            prep_time=30,
            cook_time=45,
            servings=8,
            user_id=test_user.id,
            text_feature_vector=[0.5, 0.6, 0.7, 0.8],
            text_hash_buckets=[7, 9, 11],
            image_feature_vector=[0.6, 0.7, 0.8, 0.9],
            image_hash_buckets=[6, 8, 10],
            combined_hash_buckets=[7, 8, 11],
            created_at=now,
            updated_at=now
        ),
    ]
    
    for recipe in recipes:
        db_session.add(recipe)
    
    db_session.commit()
    
    # Refresh the recipes to get their IDs
    for recipe in recipes:
        db_session.refresh(recipe)
    
    return recipes
