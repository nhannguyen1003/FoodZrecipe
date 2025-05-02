import os
import pytest
import tempfile
from fastapi.testclient import TestClient
from fastapi import Depends
from main import app
from config import settings
import sys
import shutil
from io import BytesIO
from PIL import Image
from unittest.mock import patch, MagicMock

# Import shared utilities
from tests.utils import create_test_image, create_upload_file
from backend.core.security import get_current_active_user
from database.session import get_db

# Mock the database session
@pytest.fixture(autouse=True)
def mock_db_dependency():
    """Override the database dependency"""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

# Override the authentication dependency
@pytest.fixture(autouse=True)
def mock_auth_dependency():
    """Override the authentication dependency"""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "test@example.com"
    mock_user.is_admin = False
    
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    yield
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]

# Test client
client = TestClient(app)

class TestImageAPI:
    @pytest.fixture(scope="class")
    def temp_upload_dir(self):
        """Create a temporary directory for test uploads"""
        original_upload_dir = settings.IMAGE_UPLOAD_DIR
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings.IMAGE_UPLOAD_DIR = tmp_dir
            # Ensure the directory exists
            os.makedirs(tmp_dir, exist_ok=True)
            yield tmp_dir
            # Restore original setting
            settings.IMAGE_UPLOAD_DIR = original_upload_dir
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for tests"""
        return {"Authorization": "Bearer test-token"}
    
    def test_get_image_endpoint(self, temp_upload_dir):
        """Test retrieving an image through the API endpoint"""
        # Create and save test image
        img_data = create_test_image()
        test_filename = "test_retrieve.jpg"
        img_path = os.path.join(temp_upload_dir, test_filename)
        with open(img_path, "wb") as f:
            f.write(img_data.getvalue())
        
        # Get the image
        response = client.get(f"{settings.API_PREFIX}/images/{test_filename}")
        
        # Check response
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        
        # Verify the content
        img = Image.open(BytesIO(response.content))
        assert img.size == (100, 100)
    
    def test_get_nonexistent_image(self):
        """Test retrieving a non-existent image"""
        response = client.get(f"{settings.API_PREFIX}/images/nonexistent.jpg")
        assert response.status_code == 404
    
    def test_upload_image_endpoint(self, temp_upload_dir, auth_headers):
        """Test uploading an image through the API endpoint"""
        # Create test image
        img_data = create_test_image()
        
        # Create upload file
        files = {"image": ("test_image.jpg", img_data, "image/jpeg")}
        
        # Upload the image
        response = client.post(
            f"{settings.API_PREFIX}/images/upload",
            files=files,
            headers=auth_headers
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "image_url" in data
        assert "content_type" in data
        assert data["content_type"] == "image/jpeg"
        
        # Check that file exists
        filename = data["filename"]
        assert os.path.exists(os.path.join(temp_upload_dir, filename))
    
    def test_delete_image_endpoint(self, temp_upload_dir, auth_headers):
        """Test deleting an image through the API endpoint"""
        # Create and save a test image with the correct user ID prefix
        img_data = create_test_image()
        test_filename = "1_test_delete.jpg"  # Matching the mocked user ID
        img_path = os.path.join(temp_upload_dir, test_filename)
        with open(img_path, "wb") as f:
            f.write(img_data.getvalue())
        
        # Delete the image
        delete_response = client.delete(
            f"{settings.API_PREFIX}/images/{test_filename}",
            headers=auth_headers
        )
        
        # Check response
        assert delete_response.status_code == 200
        assert delete_response.json()["detail"] == "Image deleted successfully"
        
        # Check that file no longer exists
        assert not os.path.exists(os.path.join(temp_upload_dir, test_filename))
    
    def test_upload_invalid_image(self, auth_headers):
        """Test uploading an invalid image"""
        # Create a text file instead of an image
        invalid_data = BytesIO(b"This is not an image")
        files = {"image": ("not_an_image.jpg", invalid_data, "image/jpeg")}
        
        # Upload the "image"
        response = client.post(
            f"{settings.API_PREFIX}/images/upload",
            files=files,
            headers=auth_headers
        )
        
        # Check response (should be an error)
        assert response.status_code == 400
    
    def test_unauthorized_delete(self, temp_upload_dir, auth_headers):
        """Test unauthorized image deletion"""
        # Create test image with a filename that doesn't match the authenticated user
        img_data = create_test_image()
        test_filename = "99_unauthorized.jpg"  # Different user ID
        img_path = os.path.join(temp_upload_dir, test_filename)
        with open(img_path, "wb") as f:
            f.write(img_data.getvalue())
        
        # Try to delete
        delete_response = client.delete(
            f"{settings.API_PREFIX}/images/{test_filename}",
            headers=auth_headers
        )
        
        # Should be forbidden
        assert delete_response.status_code == 403 