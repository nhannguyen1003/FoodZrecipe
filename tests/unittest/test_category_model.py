import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey, Text, DateTime, MetaData
from sqlalchemy.orm import sessionmaker, mapper, relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

# Test database URL
TEST_DB_URL = "sqlite:///:memory:"

# Create a test-specific declarative base
TestBase = declarative_base()

# Create a simplified Category model for testing
class TestCategory(TestBase):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Category {self.name}>"

# Setup test database
@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL)
    
    # Create tables
    TestBase.metadata.create_all(engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        TestBase.metadata.drop_all(engine)

def test_create_category(db_session):
    """Test creating a category"""
    # Create a category
    category = TestCategory(name="Test Category", description="Test Description")
    db_session.add(category)
    db_session.commit()
    
    # Verify the category was created
    saved_category = db_session.query(TestCategory).filter(TestCategory.name == "Test Category").first()
    assert saved_category is not None
    assert saved_category.name == "Test Category"
    assert saved_category.description == "Test Description"
    assert saved_category.created_at is not None
    assert saved_category.updated_at is not None

def test_update_category(db_session):
    """Test updating a category"""
    # Create a category
    category = TestCategory(name="Initial Name", description="Initial Description")
    db_session.add(category)
    db_session.commit()
    
    # Update the category
    category.name = "Updated Name"
    category.description = "Updated Description"
    db_session.commit()
    
    # Verify the category was updated
    updated_category = db_session.query(TestCategory).filter(TestCategory.id == category.id).first()
    assert updated_category.name == "Updated Name"
    assert updated_category.description == "Updated Description"

def test_delete_category(db_session):
    """Test deleting a category"""
    # Create a category
    category = TestCategory(name="Category to Delete", description="Will be deleted")
    db_session.add(category)
    db_session.commit()
    
    # Verify the category exists
    category_id = category.id
    assert db_session.query(TestCategory).filter(TestCategory.id == category_id).first() is not None
    
    # Delete the category
    db_session.delete(category)
    db_session.commit()
    
    # Verify the category was deleted
    assert db_session.query(TestCategory).filter(TestCategory.id == category_id).first() is None

def test_category_unique_name_constraint(db_session):
    """Test that category names must be unique"""
    # Create a category
    category1 = TestCategory(name="Unique Name", description="First category")
    db_session.add(category1)
    db_session.commit()
    
    # Try to create another category with the same name
    category2 = TestCategory(name="Unique Name", description="Second category")
    db_session.add(category2)
    
    # Expect an integrity error due to unique constraint
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    # Rollback the transaction for cleanup
    db_session.rollback()

def test_category_nullable_description(db_session):
    """Test that category description is optional"""
    # Create a category without a description
    category = TestCategory(name="No Description")
    db_session.add(category)
    db_session.commit()
    
    # Verify the category was created successfully
    saved_category = db_session.query(TestCategory).filter(TestCategory.name == "No Description").first()
    assert saved_category is not None
    assert saved_category.description is None

def test_category_string_representation(db_session):
    """Test the string representation of a category"""
    category = TestCategory(name="Test Category")
    assert str(category) == "<Category Test Category>" 