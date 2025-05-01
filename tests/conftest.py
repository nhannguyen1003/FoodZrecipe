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
        
    now = datetime.utcnow()
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
