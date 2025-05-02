import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.user import User, UserRole
from backend.models.recipe import Recipe
from backend.core.security import verify_password, get_password_hash
from database.repositories.user_repository import user_repository
from backend.schemas.user import UserCreate, UserUpdate

# Test User model basic functionality
def test_create_user(db_session: Session):
    """Test creating a user directly through ORM."""
    now = datetime.utcnow()
    user = User(
        username="newuser",
        email="newuser@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.REGULAR,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert verify_password("password123", user.hashed_password)
    assert user.role == UserRole.REGULAR
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.last_login is None

# Test unique constraints
def test_unique_username_constraint(db_session: Session, test_user: User):
    """Test that username must be unique."""
    duplicate_user = User(
        username=test_user.username,  # Same username
        email="different@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.REGULAR,
        is_active=True
    )
    db_session.add(duplicate_user)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()

def test_unique_email_constraint(db_session: Session, test_user: User):
    """Test that email must be unique."""
    duplicate_user = User(
        username="differentuser",
        email=test_user.email,  # Same email
        hashed_password=get_password_hash("password123"),
        role=UserRole.REGULAR,
        is_active=True
    )
    db_session.add(duplicate_user)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()

# Test not null constraints
def test_username_not_null(db_session: Session):
    """Test that username cannot be null."""
    user = User(
        email="nouser@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.REGULAR,
        is_active=True
    )
    db_session.add(user)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()

# Test relationships
def test_user_recipe_relationship(db_session: Session, test_user: User):
    """Test relationship between user and recipes."""
    # Create recipes for the user
    for i in range(3):
        recipe = Recipe(
            title=f"Recipe {i}",
            description=f"Description {i}",
            ingredients=[f"Ingredient {j}" for j in range(3)],
            instructions=[f"Step {j}" for j in range(3)],
            user_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(recipe)
    
    db_session.commit()
    
    # Query the user and check recipes
    user = db_session.query(User).filter(User.id == test_user.id).first()
    assert len(user.recipes) == 3
    
    # Test cascade delete
    db_session.delete(user)
    db_session.commit()
    
    # Verify recipes are also deleted
    recipes = db_session.query(Recipe).filter(Recipe.user_id == test_user.id).all()
    assert len(recipes) == 0

# Test repository functionality
def test_user_repository_create(db_session: Session):
    """Test creating a user through the repository."""
    user_data = UserCreate(
        username="repouser",
        email="repo@example.com",
        password="repopassword",
        role=UserRole.REGULAR
    )
    
    user = user_repository.create(db_session, obj_in=user_data)
    
    assert user.id is not None
    assert user.username == "repouser"
    assert user.email == "repo@example.com"
    assert verify_password("repopassword", user.hashed_password)
    assert user.is_active is True

def test_user_repository_get_by_email(db_session: Session, test_user: User):
    """Test getting a user by email."""
    user = user_repository.get_by_email(db_session, email=test_user.email)
    assert user is not None
    assert user.id == test_user.id

def test_user_repository_get_by_username(db_session: Session, test_user: User):
    """Test getting a user by username."""
    user = user_repository.get_by_username(db_session, username=test_user.username)
    assert user is not None
    assert user.id == test_user.id

def test_user_repository_authenticate(db_session: Session):
    """Test user authentication."""
    # Create a user with known password
    user_data = UserCreate(
        username="authuser",
        email="auth@example.com",
        password="authpassword",
        role=UserRole.REGULAR
    )
    
    created_user = user_repository.create(db_session, obj_in=user_data)
    
    # Test successful authentication
    authenticated_user = user_repository.authenticate(
        db_session, username="authuser", password="authpassword"
    )
    assert authenticated_user is not None
    assert authenticated_user.id == created_user.id
    assert authenticated_user.last_login is not None
    
    # Test unsuccessful authentication
    wrong_user = user_repository.authenticate(
        db_session, username="authuser", password="wrongpassword"
    )
    assert wrong_user is None

def test_user_repository_update(db_session: Session, test_user: User):
    """Test updating a user."""
    user_update = UserUpdate(username="updateduser")
    
    updated_user = user_repository.update(
        db_session, db_obj=test_user, obj_in=user_update
    )
    
    assert updated_user.username == "updateduser"
    assert updated_user.email == test_user.email  # Unchanged
    
    # Test password update
    password_update = UserUpdate(password="newpassword")
    
    user_with_new_password = user_repository.update(
        db_session, db_obj=updated_user, obj_in=password_update
    )
    
    assert verify_password("newpassword", user_with_new_password.hashed_password)

def test_user_role_checks(db_session: Session):
    """Test role checking methods."""
    # Create users directly for this test to avoid fixture issues
    now = datetime.utcnow()
    
    # Create a regular user for testing
    test_regular = User(
        username="rolecheck_regular",
        email="rolecheck_regular@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.REGULAR,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(test_regular)
    
    # Create an admin user for testing
    test_admin = User(
        username="rolecheck_admin",
        email="rolecheck_admin@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(test_admin)
    db_session.commit()
    db_session.refresh(test_regular)
    db_session.refresh(test_admin)
    
    # Test the role check methods
    assert user_repository.is_active(test_regular) is True
    assert user_repository.is_admin(test_regular) is False
    
    assert user_repository.is_active(test_admin) is True
    assert user_repository.is_admin(test_admin) is True 