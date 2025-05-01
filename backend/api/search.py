# TODO: Implement search API endpoints
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional
import tempfile
import os
import numpy as np
from sqlalchemy.orm import Session
from backend.schemas.recipe import RecipeResponse, RecipeSearchQuery
from backend.services.lsh_service import lsh_service
from database.session import get_db
from database.repositories.recipe_repository import recipe_repository

router = APIRouter()

@router.get("/text", response_model=List[RecipeResponse])
def search_recipes_by_text(
    query: str = Query(..., description="Text search query"),
    limit: int = Query(10, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Search recipes by text query using LSH
    
    1. Convert query text to feature vector
    2. Use FAISS to search for similar recipes
    3. Return matching recipes
    """
    try:
        # First try standard text search if recipe repository doesn't have indices loaded
        if not recipe_repository.text_index or recipe_repository.text_index.ntotal == 0:
            # Fall back to regular text search
            return recipe_repository.search_by_text(db, query=query, skip=offset, limit=limit)
        
        # LSH search using the recipe repository's FAISS implementation
        results = recipe_repository.search_by_text_query(db, query=query, k=limit)
        
        return results[offset:offset+limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/image", response_model=List[RecipeResponse])
async def search_recipes_by_image(
    image: UploadFile = File(...),
    limit: int = Form(10, description="Number of results to return"),
    offset: int = Form(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Search recipes by uploaded image using LSH
    
    1. Save uploaded image temporarily
    2. Extract image features
    3. Use FAISS to search for similar recipes
    4. Return matching recipes
    """
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as temp_file:
            # Write content to temp file
            contents = await image.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        try:
            # Search using recipe repository
            if not recipe_repository.image_index or recipe_repository.image_index.ntotal == 0:
                # Cannot perform image search without index
                raise HTTPException(status_code=400, detail="Image search not available - no index built")
            
            # Use FAISS for image search
            results = recipe_repository.search_by_image_path(db, image_path=temp_file_path, k=limit)
            
            return results[offset:offset+limit]
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

@router.post("/hybrid", response_model=List[RecipeResponse])
async def hybrid_search(
    text_query: Optional[str] = Form(None, description="Text search query"),
    image: Optional[UploadFile] = File(None, description="Image file for search"),
    limit: int = Form(10, description="Number of results to return"),
    offset: int = Form(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Hybrid search using both text and image if available
    
    1. Process text query if provided
    2. Process image if provided
    3. Combine results from both searches
    4. Return top matches
    """
    if not text_query and not image:
        raise HTTPException(status_code=400, detail="Either text query or image must be provided")
    
    temp_file_path = None
    try:
        # Process image if provided
        if image:
            # Save uploaded file to temp location
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as temp_file:
                # Write content to temp file
                contents = await image.read()
                temp_file.write(contents)
                temp_file_path = temp_file.name
        
        # Perform hybrid search
        results = recipe_repository.hybrid_search(
            db, 
            text_query=text_query, 
            image_path=temp_file_path if image else None,
            k=limit + offset
        )
        
        return results[offset:offset+limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)