# TODO: Implement search API endpoints
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from typing import List, Optional, Dict, Any
import tempfile
import os
import numpy as np
from sqlalchemy.orm import Session
from backend.schemas.recipe import RecipeResponse, RecipeSearchQuery
from backend.services.lsh_service import lsh_service
from database.session import get_db
from database.repositories.recipe_repository import recipe_repository
from backend.models.recipe import Recipe
from backend.schemas.search import MultiFieldSearchQuery, SearchResults, SearchResult
from backend.services.multi_field_search_service import multi_field_search_service
from config import settings

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
        # Use advanced search with filtering and sorting
        results = recipe_repository.advanced_search(
            db, 
            query=query, 
            categories=categories,
            sort_by=sort_by,
            skip=offset, 
            limit=limit
        )
        return results
    except Exception as e:
        # Raise the exception instead of returning empty list
        raise HTTPException(status_code=500, detail=f"Text search failed: {str(e)}")

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
    
    # Log detailed info about the request
    print(f"===== IMAGE SEARCH API CALL =====")
    print(f"Image search request: filename={image.filename}, size={image.size}, content_type={image.content_type}")
    print(f"Search parameters: categories={category_list}, sort_by={sort_by}, limit={limit}, offset={offset}")
    
    # Extract the raw filename
    image_filename = image.filename
    print(f"Image filename: {image_filename}")
    
    try:
        # Save uploaded file to temp location with the original filename
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1] if image.filename else ".jpg") as temp_file:
            # Write content to temp file
            contents = await image.read()
            print(f"Read image contents: {len(contents)} bytes")
            temp_file.write(contents)
            temp_file_path = temp_file.name
            print(f"Saved image to temporary file: {temp_file_path}")
        
        try:
            # Search using recipe repository
            if not recipe_repository.image_index or recipe_repository.image_index.ntotal == 0:
                # Cannot perform image search without index
                print("ERROR: Image index not initialized or empty")
                raise HTTPException(status_code=400, detail="Image search not available - no index built")
            
            print(f"Image index initialized with {recipe_repository.image_index.ntotal} images")
            
            # Use FAISS for image search - use exact k value as requested
            print(f"Performing image search on path: {temp_file_path}")
            results = recipe_repository.search_by_image_path(db, image_path=temp_file_path, k=limit*2)
            print(f"Image search found {len(results)} results before filtering")
            
            # Apply category filtering if specified
            if category_list and len(category_list) > 0 and results:
                print(f"Filtering results by categories: {category_list}")
                filtered_results = []
                for recipe in results:
                    if recipe.categories:
                        # Check if any category in the recipe matches any of the requested categories
                        if any(category in recipe.categories for category in category_list):
                            filtered_results.append(recipe)
                print(f"After category filtering: {len(filtered_results)} results")
                
                # Only use filtered results if we found some
                if filtered_results:
                    results = filtered_results
                else:
                    print("Category filtering removed all results, using unfiltered results")
            
            # Apply sorting
            if sort_by == "newest" and results:
                print("Sorting results by newest")
                results.sort(key=lambda x: x.created_at if x.created_at else x.id, reverse=True)
            elif sort_by == "popular" and results:
                print("Sorting results by popularity (ID)")
                # For now, just use ID as a proxy for popularity
                results.sort(key=lambda x: x.id, reverse=True)
            # Default is relevance, which is the order from image search
            
            # Apply pagination
            paginated_results = results[offset:offset+limit] if offset < len(results) else []
            print(f"Pagination: offset={offset}, limit={limit}")
            print(f"After pagination: {len(paginated_results)} results")
            
            # Log recipe IDs for debugging
            if paginated_results:
                result_ids = [recipe.id for recipe in paginated_results]
                recipe_titles = [recipe.title for recipe in paginated_results]
                print(f"Returning {len(paginated_results)} recipes")
                print(f"Recipe IDs: {result_ids}")
                print(f"Recipe titles: {recipe_titles}")
            else:
                print("No recipes found in search results")
            
            return paginated_results
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                print(f"Deleted temporary file: {temp_file_path}")
    except Exception as e:
        print(f"Image search failed with error: {str(e)}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_tb(e.__traceback__)
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
        # Use the more robust advanced_search method
        results = recipe_repository.advanced_search(
            db, 
            query=query, 
            categories=categories,
            sort_by=sort_by,
            skip=offset, 
            limit=limit
        )
        return results
    except Exception as e:
        # Raise the exception instead of returning empty list
        print(f"Error in search_recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/multi-field", response_model=List[RecipeResponse])
def search_recipes_multi_field(
    search_query: MultiFieldSearchQuery = Body(...),
    db: Session = Depends(get_db)
):
    """
    Search recipes using multi-field search with custom weights
    
    Allows searching by title, ingredients, and instructions separately with configurable weights.
    
    Fields:
    - title_query: Title search query (optional)
    - ingredients_query: List of ingredients to search for (optional)
    - instructions_query: Instructions search query (optional)
    - weights: Dictionary with field weights (e.g. {"title": 0.5, "ingredients": 0.3, "instructions": 0.2})
    - limit: Maximum number of results to return (default: 10)
    - offset: Pagination offset (default: 0)
    - category_ids: Optional list of category IDs to filter by
    
    At least one query field must be provided.
    """
    # Validate that at least one query field is provided
    if not any([search_query.title_query, search_query.ingredients_query, search_query.instructions_query]):
        raise HTTPException(
            status_code=400,
            detail="At least one of title_query, ingredients_query, or instructions_query must be provided"
        )
    
    # Validate weights if provided
    if search_query.weights:
        total_weight = sum(search_query.weights.values())
        if total_weight <= 0:
            raise HTTPException(
                status_code=400,
                detail="The sum of weights must be greater than 0"
            )
    
    # Perform multi-field search
    results = multi_field_search_service.multi_field_search(
        db,
        title_query=search_query.title_query,
        ingredients_query=search_query.ingredients_query,
        instructions_query=search_query.instructions_query,
        weights=search_query.weights,
        k=search_query.limit
    )
    
    # Apply category filtering if needed
    if search_query.category_ids:
        # Filter results by category IDs
        filtered_results = []
        for recipe in results:
            # Check if the recipe has categories and if any match the requested categories
            if recipe.category_relations and any(cat.id in search_query.category_ids for cat in recipe.category_relations):
                filtered_results.append(recipe)
        results = filtered_results
    
    # Apply pagination
    results = results[search_query.offset:search_query.offset + search_query.limit]
    
    return results

@router.get("/by-title", response_model=List[RecipeResponse])
def search_recipes_by_title(
    query: str = Query(..., description="Title search query"),
    limit: int = Query(10, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search recipes by title using semantic search
    """
    # Use the multi-field search service with title_query only
    results = multi_field_search_service.multi_field_search(
        db,
        title_query=query,
        weights={"title": 1.0, "ingredients": 0.0, "instructions": 0.0},
        k=limit
    )
    
    return results

@router.get("/by-ingredients", response_model=List[RecipeResponse])
def search_recipes_by_ingredients(
    ingredients: str = Query(..., description="Comma-separated list of ingredients"),
    limit: int = Query(10, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search recipes by ingredients using semantic search
    """
    # Parse ingredients from comma-separated string
    ingredient_list = [ing.strip() for ing in ingredients.split(',')]
    
    # Use the multi-field search service with ingredients_query only
    results = multi_field_search_service.multi_field_search(
        db,
        ingredients_query=ingredient_list,
        weights={"title": 0.0, "ingredients": 1.0, "instructions": 0.0},
        k=limit
    )
    
    return results

@router.get("/by-instructions", response_model=List[RecipeResponse])
def search_recipes_by_instructions(
    query: str = Query(..., description="Instructions search query"),
    limit: int = Query(10, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search recipes by cooking instructions using semantic search
    """
    # Use the multi-field search service with instructions_query only
    results = multi_field_search_service.multi_field_search(
        db,
        instructions_query=query,
        weights={"title": 0.0, "ingredients": 0.0, "instructions": 1.0},
        k=limit
    )
    
    return results