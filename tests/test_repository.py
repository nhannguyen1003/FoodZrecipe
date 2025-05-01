"""
Tests for base repository pattern implementation
"""
import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, Integer, String, Text
from database.repositories.base_repository import BaseRepository
from backend.schemas.user import UserCreate, UserUpdate
from backend.models.user import User
from backend.schemas.recipe import RecipeCreate, RecipeUpdate
from backend.models.recipe import Recipe

# Test repositories
user_repository = BaseRepository[User, UserCreate, UserUpdate](User)
recipe_repository = BaseRepository[Recipe, RecipeCreate, RecipeUpdate](Recipe)

def test_get_by_id(db_session, test_user):
    """Test retrieving an object by ID."""
    retrieved_user = user_repository.get(db_session, test_user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == test_user.id
    assert retrieved_user.username == test_user.username

def test_get_multi(db_session, test_user):
    """Test retrieving multiple objects with pagination."""
    users = user_repository.get_multi(db_session, skip=0, limit=10)
    assert len(users) > 0
    assert any(user.id == test_user.id for user in users)

def test_get_count(db_session):
    """Test getting total count of objects."""
    count = user_repository.get_count(db_session)
    assert count > 0

def test_create(db_session):
    """Test creating a new object."""
    user_data = UserCreate(
        username="new_test_user",
        email="new_test@example.com",
        password="newpassword"
    )
    
    # Convert to dict for testing since we don't have the actual model initialization
    user_dict = user_data.dict()
    user_dict.pop("password", None)  # Remove password as it would be hashed
    user_dict["hashed_password"] = "fakehash"  # Add a fake hashed password
    
    new_user = user_repository.create(db_session, obj_in=user_dict)
    assert new_user is not None
    assert new_user.username == "new_test_user"
    assert new_user.email == "new_test@example.com"

def test_update(db_session, test_user):
    """Test updating an existing object."""
    update_data = {"username": "updated_username"}
    updated_user = user_repository.update(db_session, db_obj=test_user, obj_in=update_data)
    assert updated_user.username == "updated_username"

def test_remove(db_session):
    """Test removing an object."""
    # Create a user specifically to be deleted
    user_data = {
        "username": "to_be_deleted",
        "email": "delete_me@example.com",
        "hashed_password": "fakehash"
    }
    user_to_delete = user_repository.create(db_session, obj_in=user_data)
    
    # Verify it exists
    assert user_repository.exists(db_session, id=user_to_delete.id)
    
    # Delete it
    deleted_user = user_repository.remove(db_session, id=user_to_delete.id)
    assert deleted_user is not None
    assert deleted_user.id == user_to_delete.id
    
    # Verify it no longer exists
    assert not user_repository.exists(db_session, id=user_to_delete.id)

def test_transaction(db_session):
    """Test transaction context manager."""
    # Create initial data to test transaction
    user_data = {
        "username": "transaction_test",
        "email": "transaction@example.com",
        "hashed_password": "fakehash"
    }
    
    with user_repository.transaction(db_session) as tx_db:
        user = User(**user_data)
        tx_db.add(user)
        tx_db.flush()  # Flush to get ID
        
        # Verify user exists within transaction
        retrieved_user = tx_db.query(User).filter(User.username == "transaction_test").first()
        assert retrieved_user is not None
    
    # Verify user exists after transaction
    assert user_repository.exists(db_session, id=user.id)

def test_bulk_create(db_session):
    """Test bulk creation of objects."""
    users_data = [
        {
            "username": f"bulk_user_{i}",
            "email": f"bulk{i}@example.com",
            "hashed_password": "fakehash"
        }
        for i in range(3)
    ]
    
    created_users = user_repository.bulk_create(db_session, obj_list=users_data)
    assert len(created_users) == 3
    
    # Verify all users were created
    for i, user in enumerate(created_users):
        assert user.username == f"bulk_user_{i}"
        assert user.email == f"bulk{i}@example.com"

def test_get_by_filter(db_session):
    """Test retrieving objects by filter condition."""
    # Create test data
    user_data = {
        "username": "filter_test_user",
        "email": "filter@example.com",
        "hashed_password": "fakehash"
    }
    user_repository.create(db_session, obj_in=user_data)
    
    # Test filter
    users = user_repository.get_by_filter(
        db_session, 
        filter_condition=(User.username == "filter_test_user")
    )
    
    assert len(users) == 1
    assert users[0].username == "filter_test_user"
    assert users[0].email == "filter@example.com"

def test_exists(db_session):
    """Test checking if an object exists."""
    # Create a user specifically for testing exists
    user_data = {
        "username": "exists_test_user",
        "email": "exists_test@example.com",
        "hashed_password": "fakehash"
    }
    user = user_repository.create(db_session, obj_in=user_data)
    
    # Test that it exists
    assert user_repository.exists(db_session, id=user.id)
    # Test that a non-existent ID doesn't exist
    assert not user_repository.exists(db_session, id=99999) 