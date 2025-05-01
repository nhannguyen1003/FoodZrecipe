"""
Common test utilities shared across test categories
"""

import os
from PIL import Image
from io import BytesIO
from fastapi import UploadFile

def create_test_image(width=100, height=100, format="jpeg"):
    """Generate a test image with given dimensions and format"""
    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format=format)
    img_byte_arr.seek(0)
    return img_byte_arr

def create_upload_file(file_content, filename="test_image.jpg"):
    """Create a FastAPI UploadFile from BytesIO content"""
    return UploadFile(
        filename=filename,
        file=file_content,
        content_type=f"image/{os.path.splitext(filename)[1][1:]}"
    ) 