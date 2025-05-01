import os
import pytest
import tempfile
import shutil
import imghdr
from PIL import Image
import uuid
import numpy as np
from io import BytesIO
from config import settings

# Import shared utilities
from tests.utils import create_test_image, create_upload_file

class TestImageUtils:
    @pytest.fixture(scope="class")
    def temp_upload_dir(self):
        """Create a temporary directory for test uploads"""
        original_upload_dir = settings.UPLOAD_DIR
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings.UPLOAD_DIR = tmp_dir
            yield tmp_dir
            settings.UPLOAD_DIR = original_upload_dir
    
    def test_image_format_validation(self, temp_upload_dir):
        """Test validation of different image formats"""
        # Test valid formats
        valid_formats = ["jpeg", "png", "gif"]
        for fmt in valid_formats:
            img_data = create_test_image(format=fmt)
            img_path = os.path.join(temp_upload_dir, f"test.{fmt}")
            with open(img_path, "wb") as f:
                f.write(img_data.getvalue())
            
            # Verify imghdr correctly identifies the format
            detected_format = imghdr.what(img_path)
            assert detected_format in ["jpeg", "png", "gif"]
    
    def test_image_size_validation(self, temp_upload_dir):
        """Test validation of image sizes"""
        # Small image
        small_img = create_test_image(width=50, height=50)
        small_size = len(small_img.getvalue())
        assert small_size < 1024 * 1024  # Should be less than 1MB
        
        # Larger image
        large_img = create_test_image(width=1000, height=1000)
        large_size = len(large_img.getvalue())
        assert large_size > small_size
    
    def test_unique_filename_generation(self):
        """Test generation of unique filenames"""
        user_id = 1
        filename1 = f"{user_id}_{uuid.uuid4().hex}.jpg"
        filename2 = f"{user_id}_{uuid.uuid4().hex}.jpg"
        
        # Filenames should be different even with same user_id
        assert filename1 != filename2
        
        # Both should start with user_id
        assert filename1.startswith(f"{user_id}_")
        assert filename2.startswith(f"{user_id}_")
        
        # Both should end with .jpg
        assert filename1.endswith(".jpg")
        assert filename2.endswith(".jpg")
    
    def test_image_storage(self, temp_upload_dir):
        """Test storing images on the filesystem"""
        # Create test image
        img_data = create_test_image()
        filename = "test_store.jpg"
        img_path = os.path.join(temp_upload_dir, filename)
        
        # Save the image
        with open(img_path, "wb") as f:
            f.write(img_data.getvalue())
        
        # Verify file exists and has content
        assert os.path.exists(img_path)
        assert os.path.getsize(img_path) > 0
        
        # Verify it's a valid image
        assert imghdr.what(img_path) == "jpeg"
        
        # Test loading the image
        img = Image.open(img_path)
        assert img.size == (100, 100)
        assert img.mode == "RGB" 