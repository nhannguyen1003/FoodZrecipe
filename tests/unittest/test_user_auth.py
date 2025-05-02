import pytest
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Table, Column, Integer, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.user import User, UserRole
from backend.core.security import (
    verify_password, 
    get_password_hash,
    create_access_token
)
from database.repositories.user_repository import user_repository
from backend.schemas.user import UserCreate, UserUpdate
from main import app
from config import settings
from database.session import get_db
from sqlalchemy.ext.declarative import declarative_base

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a test-specific Base
TestBase = declarative_base()

# Define test-specific User model for SQLite compatibility
class TestUser(TestBase):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.REGULAR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    last_login = Column(DateTime, nullable=True)

# Set up test database
TestBase.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the get_db dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    # Create tables
    TestBase.metadata.create_all(bind=engine)
    
    # Create test users
    db = TestingSessionLocal()
    try:
        # Create admin user
        admin_user = {
            "username": "testadmin",
            "email": "testadmin@example.com",
            "hashed_password": get_password_hash("testadmin"),
            "role": UserRole.ADMIN,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        user_repository.create_user_direct(db, **admin_user)
        
        # Create regular user
        regular_user = {
            "username": "testuser",
            "email": "testuser@example.com",
            "hashed_password": get_password_hash("testuser"),
            "role": UserRole.REGULAR,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        user_repository.create_user_direct(db, **regular_user)
        
        yield db
    
    finally:
        db.close()
        # Drop tables after test
        TestBase.metadata.drop_all(bind=engine)

def test_register_user(test_db):
    """Test user registration"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["role"] == UserRole.REGULAR

def test_register_duplicate_email(test_db):
    """Test registration with duplicate email"""
    # Register first user
    client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "password123"
        }
    )
    
    # Try to register with same email
    response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "user2",
            "email": "duplicate@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_admin(test_db):
    """Test admin login"""
    login_data = {
        "username": "testadmin",
        "password": "testadmin"
    }
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data=login_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_regular_user(test_db):
    """Test regular user login"""
    login_data = {
        "username": "testuser",
        "password": "testuser"
    }
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data=login_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(test_db):
    """Test login with wrong password"""
    login_data = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data=login_data
    )
    assert response.status_code == 401

def test_get_current_user(test_db):
    """Test getting current user info"""
    # First login to get token
    login_response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data={"username": "testuser", "password": "testuser"}
    )
    token = login_response.json()["access_token"]
    
    # Get user info
    response = client.get(
        f"{settings.API_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert data["role"] == UserRole.REGULAR

def test_admin_only_endpoint_with_admin(test_db):
    """Test admin-only endpoint with admin user"""
    # First login as admin to get token
    login_response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data={"username": "testadmin", "password": "testadmin"}
    )
    token = login_response.json()["access_token"]
    
    # Access admin-only endpoint
    response = client.post(
        f"{settings.API_PREFIX}/auth/test-admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_admin_only_endpoint_with_regular_user(test_db):
    """Test admin-only endpoint with regular user (should fail)"""
    # First login as regular user to get token
    login_response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data={"username": "testuser", "password": "testuser"}
    )
    token = login_response.json()["access_token"]
    
    # Try to access admin-only endpoint
    response = client.post(
        f"{settings.API_PREFIX}/auth/test-admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

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
    token = create_access_token(data={"sub": "testuser"})
    assert token is not None
    assert isinstance(token, str)
    
    # Sleep a short time to ensure different expiration timestamps
    time.sleep(1)
    
    # Test token with custom expiration
    custom_expires = timedelta(minutes=30)
    token_with_exp = create_access_token(data={"sub": "testuser"}, expires_delta=custom_expires)
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
