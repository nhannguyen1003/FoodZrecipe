import pytest
from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime

# Create a separate base for test models
TestBase = declarative_base()

# Test database URL
TEST_DB_URL = "sqlite:///:memory:"

# Define the recipe_category association table
recipe_category = Table(
    "recipe_category", 
    TestBase.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
)

# Define test-specific models
class User(TestBase):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    recipes = relationship("Recipe", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"

class Category(TestBase):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationship to recipes
    recipes = relationship("Recipe", secondary=recipe_category, back_populates="category_relations")
    
    def __repr__(self):
        return f"<Category {self.name}>"

class Recipe(TestBase):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    ingredients = Column(JSON, nullable=False)
    instructions = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Store categories as JSON array for migration testing
    categories = Column(JSON, nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="recipes")
    
    # Relationship to categories
    category_relations = relationship("Category", secondary=recipe_category, back_populates="recipes")
    
    def __repr__(self):
        return f"<Recipe {self.title}>"

# Simple repository class for testing
class RecipeRepository:
    def __init__(self, db):
        self.db = db
        
    def get(self, id):
        return self.db.query(Recipe).filter(Recipe.id == id).first()
        
    def create(self, recipe_data, categories=None):
        """Create a recipe with optional categories"""
        recipe = Recipe(**recipe_data)
        self.db.add(recipe)
        self.db.flush()  # Get the recipe ID
        
        # Add categories if provided
        if categories:
            for category_id in categories:
                stmt = recipe_category.insert().values(
                    recipe_id=recipe.id,
                    category_id=category_id
                )
                self.db.execute(stmt)
        
        self.db.commit()
        self.db.refresh(recipe)
        return recipe

@pytest.fixture
def db_session():
    """Create a SQLite in-memory database for testing"""
    engine = create_engine(TEST_DB_URL)
    TestBase.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        TestBase.metadata.drop_all(engine)

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
    # Get category IDs
    category_ids = [category.id for category in sample_categories]
    
    # Recipe data
    recipe_data = {
        "title": "New Recipe",
        "description": "A recipe created with categories",
        "ingredients": ["ingredient1", "ingredient2"],
        "instructions": "Test instructions",
        "user_id": sample_user.id
    }
    
    # Create recipe with categories
    recipe = recipe_repo.create(recipe_data, categories=category_ids)
    
    # Verify the recipe was created
    assert recipe.id is not None
    assert recipe.title == "New Recipe"
    
    # Verify the categories were associated
    assert len(recipe.category_relations) == 3
    category_names = [c.name for c in recipe.category_relations]
    assert "Breakfast" in category_names
    assert "Lunch" in category_names
    assert "Dinner" in category_names 