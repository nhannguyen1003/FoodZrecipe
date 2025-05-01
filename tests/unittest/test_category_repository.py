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
class CategoryRepository:
    def __init__(self, db):
        self.db = db
        
    def get(self, id):
        return self.db.query(Category).filter(Category.id == id).first()
        
    def get_by_name(self, name):
        return self.db.query(Category).filter(Category.name == name).first()
        
    def get_all(self):
        return self.db.query(Category).all()
        
    def get_all_with_recipe_count(self):
        """Get all categories with count of recipes in each"""
        from sqlalchemy import func
        
        # Count recipes in each category via the association table
        results = self.db.query(
            Category, 
            func.count(recipe_category.c.recipe_id).label('recipe_count')
        ).outerjoin(
            recipe_category, 
            Category.id == recipe_category.c.category_id
        ).group_by(Category.id).all()
        
        return results
        
    def create(self, obj_in):
        category = Category(**obj_in)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
        
    def update(self, id, obj_in):
        category = self.get(id)
        if not category:
            return None
            
        for key, value in obj_in.items():
            setattr(category, key, value)
            
        category.updated_at = datetime.datetime.now()
        self.db.commit()
        self.db.refresh(category)
        return category
        
    def delete(self, id):
        category = self.get(id)
        if not category:
            return False
            
        self.db.delete(category)
        self.db.commit()
        return True
        
    def add_recipe_to_category(self, category_id, recipe_id):
        """Add a recipe to a category"""
        # Check if relationship already exists
        exists = self.db.query(recipe_category).filter(
            recipe_category.c.recipe_id == recipe_id,
            recipe_category.c.category_id == category_id
        ).first()
        
        if exists:
            return False
        
        # Add relationship
        stmt = recipe_category.insert().values(
            recipe_id=recipe_id,
            category_id=category_id
        )
        self.db.execute(stmt)
        self.db.commit()
        return True
        
    def remove_recipe_from_category(self, category_id, recipe_id):
        """Remove a recipe from a category"""
        # Check if relationship exists
        exists = self.db.query(recipe_category).filter(
            recipe_category.c.recipe_id == recipe_id,
            recipe_category.c.category_id == category_id
        ).first()
        
        if not exists:
            return False
        
        # Remove relationship
        stmt = recipe_category.delete().where(
            recipe_category.c.recipe_id == recipe_id,
            recipe_category.c.category_id == category_id
        )
        self.db.execute(stmt)
        self.db.commit()
        return True
        
    def get_recipes_by_category(self, category_id, limit=None, offset=None):
        """Get all recipes in a category"""
        query = self.db.query(Recipe).join(
            recipe_category, 
            Recipe.id == recipe_category.c.recipe_id
        ).filter(
            recipe_category.c.category_id == category_id
        )
        
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
            
        return query.all()
        
    def get_categories_for_recipe(self, recipe_id):
        """Get all categories for a recipe"""
        return self.db.query(Category).join(
            recipe_category, 
            Category.id == recipe_category.c.category_id
        ).filter(
            recipe_category.c.recipe_id == recipe_id
        ).all()

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