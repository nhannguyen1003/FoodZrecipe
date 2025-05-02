from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Path
from fastapi.responses import FileResponse
from typing import List, Optional
from sqlalchemy.orm import Session
import os
import uuid
import shutil
import imghdr
from database.session import get_db
from backend.core.security import get_current_active_user
from backend.models.user import User
from config import settings

router = APIRouter()

# Create upload directory if it doesn't exist
os.makedirs(settings.IMAGE_UPLOAD_DIR, exist_ok=True)

# Valid image types
VALID_IMAGE_TYPES = ["jpeg", "jpg", "png", "gif"]
# Maximum file size in MB
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/upload")
async def upload_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload an image file to the server
    Returns the image path that can be used for recipes
    """
    # Validate file type
    file_extension = os.path.splitext(image.filename)[1].lower()
    if file_extension not in [f".{ext}" for ext in VALID_IMAGE_TYPES]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(VALID_IMAGE_TYPES)}"
        )
    
    # Validate file size
    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"File size exceeds the {MAX_FILE_SIZE/1024/1024}MB limit"
        )
    
    # Reset file pointer after reading
    await image.seek(0)
    
    # Generate unique filename to prevent collisions
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
    image_path = os.path.join(settings.IMAGE_UPLOAD_DIR, unique_filename)
    
    # Save the file
    with open(image_path, "wb") as buffer:
        await image.seek(0)
        shutil.copyfileobj(image.file, buffer)
    
    # Verify the image is valid
    image_type = imghdr.what(image_path)
    if not image_type or image_type not in VALID_IMAGE_TYPES:
        # Remove invalid file
        os.remove(image_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file content"
        )
    
    # Return relative path for database storage
    return {
        "filename": unique_filename,
        "image_url": f"/food-images/{unique_filename}",  # Return path relative to API root
        "content_type": f"image/{image_type}"
    }

@router.get("/{filename}")
async def get_image(
    filename: str = Path(..., description="Image filename"),
    db: Session = Depends(get_db)
):
    """
    Get an image by filename
    """
    image_path = os.path.join(settings.IMAGE_UPLOAD_DIR, filename)
    
    # Check if file exists
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Determine content type
    image_type = imghdr.what(image_path)
    if not image_type:
        image_type = os.path.splitext(filename)[1].lstrip('.')
    
    # Return the file
    return FileResponse(
        path=image_path,
        media_type=f"image/{image_type}",
        filename=filename
    )

@router.delete("/{filename}")
async def delete_image(
    filename: str = Path(..., description="Image filename"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an image by filename
    Only the owner or admin can delete an image
    """
    # Basic security check to prevent unauthorized deletion
    # Only allow deletion if the filename starts with the user ID
    if not filename.startswith(f"{current_user.id}_") and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this image"
        )
    
    image_path = os.path.join(settings.IMAGE_UPLOAD_DIR, filename)
    
    # Check if file exists
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Delete the file
    os.remove(image_path)
    
    return {"detail": "Image deleted successfully"} 