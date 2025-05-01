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
    categories: Optional[List[str]] = Query(None, description="Filter by categories"),
    sort_by: Optional[str] = Query("relevance", description="Sort options: relevance, newest, popular"),
    limit: int = Query(10, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Search recipes by text query with filtering and sorting options
    
    1. Convert query text to feature vector (if LSH available)
    2. Use FAISS to search for similar recipes (if LSH available)
    3. Apply filters and sorting
    4. Return matching recipes
    """
    try:
        # Check if LSH is available
        if not recipe_repository.text_index or recipe_repository.text_index.ntotal == 0:
            # Fall back to regular text search with filtering and sorting
            return recipe_repository.advanced_search(
                db, 
                query=query, 
                categories=categories,
                sort_by=sort_by,
                skip=offset, 
                limit=limit
            )
        
        # If LSH is available, use it for search but apply filtering and sorting afterwards
        # This is a simplified implementation that doesn't take advantage of all LSH capabilities
        # with the filter/sort parameters, but it's a good starting point
        
        # LSH search using the recipe repository's FAISS implementation
        lsh_results = recipe_repository.search_by_text_query(db, query=query, k=100)  # Get more results to apply filtering
        
        # Apply category filtering if specified
        if categories and len(categories) > 0:
            filtered_results = []
            for recipe in lsh_results:
                if recipe.categories:
                    # Check if any category in the recipe matches any of the requested categories
                    if any(category in recipe.categories for category in categories):
                        filtered_results.append(recipe)
            lsh_results = filtered_results
        
        # Apply sorting
        if sort_by == "newest":
            lsh_results.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == "popular":
            # For now, just use ID as a proxy for popularity
            lsh_results.sort(key=lambda x: x.id, reverse=True)
        # Default is relevance, which is the order from LSH search
        
        # Apply pagination
        return lsh_results[offset:offset+limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/image", response_model=List[RecipeResponse])
async def search_recipes_by_image(
    image: UploadFile = File(...),
    categories: Optional[str] = Form(None, description="Comma-separated categories to filter by"),
    sort_by: Optional[str] = Form("relevance", description="Sort options: relevance, newest, popular"),
    limit: int = Form(10, description="Number of results to return"),
    offset: int = Form(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Search recipes by uploaded image using LSH
    
    1. Save uploaded image temporarily
    2. Extract image features
    3. Use FAISS to search for similar recipes
    4. Apply filtering by categories
    5. Apply sorting options
    6. Return matching recipes
    """
    # Parse categories if provided
    category_list = None
    if categories:
        category_list = [c.strip() for c in categories.split(',')]
        
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
            
            # Use FAISS for image search - get more results to apply filtering
            results = recipe_repository.search_by_image_path(db, image_path=temp_file_path, k=100)
            
            # Apply category filtering if specified
            if category_list and len(category_list) > 0:
                filtered_results = []
                for recipe in results:
                    if recipe.categories:
                        # Check if any category in the recipe matches any of the requested categories
                        if any(category in recipe.categories for category in category_list):
                            filtered_results.append(recipe)
                results = filtered_results
            
            # Apply sorting
            if sort_by == "newest":
                results.sort(key=lambda x: x.created_at, reverse=True)
            elif sort_by == "popular":
                # For now, just use ID as a proxy for popularity
                results.sort(key=lambda x: x.id, reverse=True)
            # Default is relevance, which is the order from image search
            
            # Apply pagination
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
    categories: Optional[str] = Form(None, description="Comma-separated categories to filter by"),
    sort_by: Optional[str] = Form("relevance", description="Sort options: relevance, newest, popular"),
    limit: int = Form(10, description="Number of results to return"),
    offset: int = Form(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Hybrid search using both text and image if available
    
    1. Process text query if provided
    2. Process image if provided
    3. Apply filtering by categories
    4. Apply sorting options
    5. Return top matches
    """
    if not text_query and not image:
        raise HTTPException(status_code=400, detail="Either text query or image must be provided")
    
    # Parse categories if provided
    category_list = None
    if categories:
        category_list = [c.strip() for c in categories.split(',')]
    
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
        
        # Perform hybrid search - we'll get more results to allow for filtering
        results = recipe_repository.hybrid_search(
            db, 
            text_query=text_query, 
            image_path=temp_file_path if image else None,
            k=100  # Get more results to apply filtering
        )
        
        # Apply category filtering if specified
        if category_list and len(category_list) > 0:
            filtered_results = []
            for recipe in results:
                if recipe.categories:
                    # Check if any category in the recipe matches any of the requested categories
                    if any(category in recipe.categories for category in category_list):
                        filtered_results.append(recipe)
            results = filtered_results
        
        # Apply sorting
        if sort_by == "newest":
            results.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == "popular":
            # For now, just use ID as a proxy for popularity
            results.sort(key=lambda x: x.id, reverse=True)
        # Default is relevance, which is the order from hybrid search
        
        # Apply pagination
        return results[offset:offset+limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@router.get("/categories", response_model=List[str])
def get_all_categories(db: Session = Depends(get_db)):
    """
    Get all available recipe categories for filtering
    
    Returns a sorted list of all unique categories in the database
    """
    try:
        return recipe_repository.get_all_categories(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve categories: {str(e)}")

@router.get("/recipes/search", response_model=List[RecipeResponse])
def search_recipes(
    query: str = Query(..., description="Text search query"),
    categories: Optional[List[str]] = Query(None, description="Filter by categories"),
    sort_by: Optional[str] = Query("relevance", description="Sort options: relevance, newest, popular"),
    limit: int = Query(10, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Search recipes by text query with filtering and sorting options
    
    1. Parse query and filter parameters
    2. Apply advanced search with proper PostgreSQL operations
    3. Return matching recipes
    """
    try:
        return recipe_repository.advanced_search(
            db, 
            query=query, 
            categories=categories,
            sort_by=sort_by,
            skip=offset, 
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recipe search failed: {str(e)}")