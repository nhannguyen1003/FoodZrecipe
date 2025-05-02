import os
import pytest
import tempfile
# Try to import from unittest.mock, but fall back to the mock package if that fails
try:
    from unittest.mock import patch, MagicMock
except ImportError:
    try:
        from mock import patch, MagicMock
    except ImportError:
        import sys
        print("Error: Neither unittest.mock nor the mock package is available.")
        print("Please install the mock package with: pip install mock")
        sys.exit(1)
import logging

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def auth_headers() -> dict:
    """Return mock authentication headers for testing"""
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def mock_current_user():
    """Mock the current_user dependency for testing authenticated endpoints"""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "test@example.com"
    mock_user.email = "test@example.com"
    mock_user.is_admin = False
    
    return mock_user

@pytest.fixture(autouse=True)
def override_dependency():
    """Override get_current_active_user dependency for all tests"""
    from backend.core.security import get_current_active_user
    
    # Create a mock user object
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "test@example.com"
    mock_user.email = "test@example.com"
    mock_user.is_admin = False
    
    # Apply the patch during tests
    with patch("backend.api.image.get_current_active_user", return_value=mock_user):
        yield 