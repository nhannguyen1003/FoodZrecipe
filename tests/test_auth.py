import pytest
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.models.user import User, UserRole
from backend.core.security import (
    verify_password, 
    get_password_hash,
    create_access_token
)
from database.repositories.user_repository import user_repository
from backend.schemas.user import UserCreate, UserUpdate

def test_password_hashing():
    """Test password hashing and verification."""
    original_password = "testpassword123"
    hashed_password = get_password_hash(original_password)
    
    # Verify passwords don't match as plain text
    assert original_password != hashed_password
    
    # Verify password verification works
    assert verify_password(original_password, hashed_password) is True
    
    # Verify wrong password fails
    assert verify_password("wrongpassword", hashed_password) is False

def test_token_creation():
    """Test JWT token creation."""
    token = create_access_token(subject="testuser")
    assert token is not None
    assert isinstance(token, str)
    
    # Sleep a short time to ensure different expiration timestamps
    time.sleep(1)
    
    # Test token with custom expiration
    custom_expires = timedelta(minutes=30)
    token_with_exp = create_access_token(subject="testuser", expires_delta=custom_expires)
    assert token_with_exp is not None
    assert isinstance(token_with_exp, str)
    
    # Tokens should be different
    assert token != token_with_exp

def test_user_authentication(db_session: Session):
    """Test user authentication flow."""
    # Create test user
    user_data = UserCreate(
        username="authtest",
        email="authtest@example.com",
        password="securepassword",
        role=UserRole.REGULAR
    )
    
    user = user_repository.create(db_session, obj_in=user_data)
    
    # Successful authentication
    authenticated = user_repository.authenticate(
        db_session, username="authtest", password="securepassword"
    )
    assert authenticated is not None
    assert authenticated.id == user.id
    assert authenticated.last_login is not None
    
    # Check the last_login was updated
    first_login = authenticated.last_login
    
    # Failed authentication with wrong username
    wrong_user = user_repository.authenticate(
        db_session, username="nonexistent", password="securepassword"
    )
    assert wrong_user is None
    
    # Failed authentication with wrong password
    wrong_pass = user_repository.authenticate(
        db_session, username="authtest", password="wrongpassword"
    )
    assert wrong_pass is None
    
    # Wait a moment to ensure last_login timestamp will be different
    time.sleep(1)
    
    # Successful auth again should update last_login
    authenticated_again = user_repository.authenticate(
        db_session, username="authtest", password="securepassword"
    )
    assert authenticated_again is not None
    assert authenticated_again.last_login > first_login

def test_inactive_user(db_session: Session):
    """Test authentication for inactive users."""
    # Create inactive user
    now = datetime.utcnow()
    inactive_user = User(
        username="inactive",
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.REGULAR,
        is_active=False,  # Inactive user
        created_at=now,
        updated_at=now
    )
    db_session.add(inactive_user)
    db_session.commit()
    
    # Authentication should fail for inactive users
    auth_inactive = user_repository.authenticate(
        db_session, username="inactive", password="password123"
    )
    assert auth_inactive is None
    
    # Activate the user
    inactive_user.is_active = True
    db_session.commit()
    
    # Authentication should now succeed
    auth_active = user_repository.authenticate(
        db_session, username="inactive", password="password123"
    )
    assert auth_active is not None
    assert user_repository.is_active(auth_active) is True

def test_role_checks(db_session: Session):
    """Test user role checking functionality."""
    # Create admin user
    admin_data = UserCreate(
        username="roleadmin",
        email="roleadmin@example.com",
        password="adminpass",
        role=UserRole.ADMIN
    )
    admin = user_repository.create(db_session, obj_in=admin_data)
    
    # Create regular user
    regular_data = UserCreate(
        username="roleuser",
        email="roleuser@example.com",
        password="userpass",
        role=UserRole.REGULAR
    )
    regular = user_repository.create(db_session, obj_in=regular_data)
    
    # Check admin role
    assert user_repository.is_admin(admin) is True
    assert user_repository.is_admin(regular) is False
    
    # Update regular user to admin
    update_data = UserUpdate(role=UserRole.ADMIN)
    updated_user = user_repository.update(db_session, db_obj=regular, obj_in=update_data)
    
    # Check role was updated
    assert user_repository.is_admin(updated_user) is True
