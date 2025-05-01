import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.user import User, UserRole
from backend.schemas.user import UserCreate, UserUpdate
from database.repositories.user_repository import user_repository
from backend.core.security import verify_password


def test_role_based_query_methods(db_session: Session):
    """Test the role-based query methods."""
    # Create users directly for this test
    # Create a regular user
    user_data = UserCreate(
        username="role_test_regular",
        email="role_test_regular@example.com",
        password="password123",
        role=UserRole.REGULAR
    )
    regular_user = user_repository.create(db_session, obj_in=user_data)
    
    # Create an admin user
    admin_data = UserCreate(
        username="role_test_admin",
        email="role_test_admin@example.com",
        password="password123",
        role=UserRole.ADMIN
    )
    admin_user = user_repository.create(db_session, obj_in=admin_data)
    
    # Test get_users_by_role for REGULAR role
    regular_users = user_repository.get_users_by_role(db_session, role=UserRole.REGULAR)
    assert len(regular_users) >= 1
    assert any(user.id == regular_user.id for user in regular_users)
    
    # Test get_users_by_role for ADMIN role
    admin_users = user_repository.get_users_by_role(db_session, role=UserRole.ADMIN)
    assert len(admin_users) >= 1
    assert any(user.id == admin_user.id for user in admin_users)
    
    # Test count_users_by_role for REGULAR role
    regular_count = user_repository.count_users_by_role(db_session, role=UserRole.REGULAR)
    assert regular_count >= 1
    
    # Test count_users_by_role for ADMIN role
    admin_count = user_repository.count_users_by_role(db_session, role=UserRole.ADMIN)
    assert admin_count >= 1


def test_account_status_management(db_session: Session):
    """Test account activation and deactivation functionality."""
    # Create a test user
    user_data = UserCreate(
        username="statustest",
        email="status@example.com",
        password="password123",
        role=UserRole.REGULAR
    )
    
    user = user_repository.create(db_session, obj_in=user_data)
    assert user.is_active is True
    
    # Test deactivation
    deactivated_user = user_repository.deactivate_user(db_session, user_id=user.id)
    assert deactivated_user.is_active is False
    
    # Test authentication with deactivated user
    inactive_auth = user_repository.authenticate(
        db_session, username="statustest", password="password123"
    )
    assert inactive_auth is None
    
    # Test activation
    activated_user = user_repository.activate_user(db_session, user_id=user.id)
    assert activated_user.is_active is True
    
    # Test authentication with reactivated user
    active_auth = user_repository.authenticate(
        db_session, username="statustest", password="password123"
    )
    assert active_auth is not None
    assert active_auth.id == user.id


def test_change_user_role(db_session: Session):
    """Test changing a user's role."""
    # Create a regular user
    user_data = UserCreate(
        username="rolechange",
        email="rolechange@example.com",
        password="password123",
        role=UserRole.REGULAR
    )
    
    user = user_repository.create(db_session, obj_in=user_data)
    assert user.role == UserRole.REGULAR
    
    # Change to admin role
    admin_user = user_repository.change_user_role(db_session, user_id=user.id, new_role=UserRole.ADMIN)
    assert admin_user.role == UserRole.ADMIN
    
    # Change back to regular role
    regular_user = user_repository.change_user_role(db_session, user_id=user.id, new_role=UserRole.REGULAR)
    assert regular_user.role == UserRole.REGULAR


def test_enhanced_authentication(db_session: Session):
    """Test the improved authentication logic."""
    # Create a test user
    user_data = UserCreate(
        username="authtest_enhanced",
        email="authtest_enhanced@example.com",
        password="correctpassword",
        role=UserRole.REGULAR
    )
    
    user = user_repository.create(db_session, obj_in=user_data)
    
    # Test authentication with correct credentials
    authenticated_user = user_repository.authenticate(
        db_session, username="authtest_enhanced", password="correctpassword"
    )
    assert authenticated_user is not None
    assert authenticated_user.id == user.id
    
    # Test last_login is updated
    first_login_time = authenticated_user.last_login
    assert first_login_time is not None
    
    # Test authentication with incorrect password
    invalid_auth = user_repository.authenticate(
        db_session, username="authtest_enhanced", password="wrongpassword"
    )
    assert invalid_auth is None
    
    # Test authentication with non-existent user
    nonexistent_auth = user_repository.authenticate(
        db_session, username="nonexistentuser", password="anypassword"
    )
    assert nonexistent_auth is None
    
    # Test authentication updates last_login timestamp
    # Wait a short time to ensure timestamp difference
    import time
    time.sleep(1)
    
    # First retrieve the user again to make sure we have the latest state
    db_session.refresh(user)
    
    authenticated_again = user_repository.authenticate(
        db_session, username="authtest_enhanced", password="correctpassword"
    )
    assert authenticated_again is not None
    assert authenticated_again.last_login > first_login_time


def test_password_hashing_in_create(db_session: Session):
    """Test that passwords are properly hashed during user creation."""
    plain_password = "securepassword123"
    user_data = UserCreate(
        username="hashtest",
        email="hashtest@example.com",
        password=plain_password,
        role=UserRole.REGULAR
    )
    
    user = user_repository.create(db_session, obj_in=user_data)
    
    # Ensure password is not stored in plain text
    assert user.hashed_password != plain_password
    
    # Ensure the hashed password can be verified
    assert verify_password(plain_password, user.hashed_password) is True 