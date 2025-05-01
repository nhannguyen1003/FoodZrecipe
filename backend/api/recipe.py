# TODO: Implement recipe API endpoints
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeResponse
from backend.core.security import get_current_active_user, get_current_user
from backend.models.user import User
from database.session import get_db
from database.repositories.recipe_repository import recipe_repository
import json

router = APIRouter()

@router.get("/", response_model=List[RecipeResponse])
def get_recipes(
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all recipes with pagination and optional filtering by category or user
    """
    if category:
        return recipe_repository.get_by_category(db, category=category, skip=skip, limit=limit)
    elif user_id:
        return recipe_repository.get_by_user_id(db, user_id=user_id, skip=skip, limit=limit)
    else:
        return recipe_repository.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=RecipeResponse)
async def create_recipe(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    ingredients: str = Form(...),  # Comma-separated list
    instructions: str = Form(...),  # Now a full text block
    categories: Optional[str] = Form(None),   # Comma-separated list
    labels: Optional[str] = Form(None),   # Comma-separated list
    cleaned_ingredients: Optional[str] = Form(None),  # Comma-separated list
    prompt: Optional[str] = Form(None),
    prep_time: Optional[int] = Form(None),
    cook_time: Optional[int] = Form(None),
    servings: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    raw_data: Optional[str] = Form(None),  # JSON string with original data
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new recipe with optional image
    Also generates feature vectors for LSH search
    """
    # Process form data
    recipe_data = {
        "title": title,
        "description": description,
        "ingredients": [i.strip() for i in ingredients.split(',')],
        "instructions": instructions,  # Now storing as full text block
    }
    
    # Add optional fields if provided
    if categories:
        recipe_data["categories"] = [c.strip() for c in categories.split(',')]
    if labels:
        recipe_data["labels"] = [l.strip() for l in labels.split(',')]
    if cleaned_ingredients:
        recipe_data["cleaned_ingredients"] = [i.strip() for i in cleaned_ingredients.split(',')]
    if prompt:
        recipe_data["prompt"] = prompt
    if prep_time is not None:
        recipe_data["prep_time"] = prep_time
    if cook_time is not None:
        recipe_data["cook_time"] = cook_time
    if servings is not None:
        recipe_data["servings"] = servings
    if raw_data:
        try:
            recipe_data["raw_data"] = json.loads(raw_data)
        except json.JSONDecodeError:
            pass  # Ignore if invalid JSON
    
    # Handle image upload if provided
    image_path = None
    if image:
        import os
        from config import settings
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save the file
        image_filename = f"{current_user.id}_{image.filename}"
        image_path = os.path.join(settings.UPLOAD_DIR, image_filename)
        with open(image_path, "wb") as buffer:
            contents = await image.read()
            buffer.write(contents)
        
        # Add image info to recipe data
        recipe_data["image_url"] = image_path
        recipe_data["image_name"] = image_filename
    
    # Create recipe object
    recipe_in = RecipeCreate(**recipe_data)
    recipe = recipe_repository.create(db, obj_in=recipe_in, user_id=current_user.id)
    
    # Generate feature vectors and LSH hashes for the new recipe
    recipe_repository.update_feature_vectors(db, recipe_id=recipe.id)
    
    return recipe

@router.post("/import", response_model=RecipeResponse)
async def import_recipe(
    recipe_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """Import recipe data directly from JSON format"""
    
    # Transform data to match our schema
    transformed_data = {
        "title": recipe_data.get("Title", ""),
        "ingredients": recipe_data.get("Ingredients", []),
        "instructions": recipe_data.get("Instructions", ""),
        "raw_data": recipe_data  # Store original data
    }
    
    # Handle optional fields
    if "Image_Name" in recipe_data:
        transformed_data["image_name"] = recipe_data["Image_Name"]
    if "Cleaned_Ingredients" in recipe_data:
        transformed_data["cleaned_ingredients"] = recipe_data["Cleaned_Ingredients"]
    if "prompt" in recipe_data:
        transformed_data["prompt"] = recipe_data["prompt"]
    if "labels" in recipe_data:
        transformed_data["labels"] = recipe_data["labels"]
        transformed_data["categories"] = recipe_data["labels"]  # Use labels as categories too
    
    # Create recipe object
    recipe_in = RecipeCreate(**transformed_data)
    recipe = recipe_repository.create(db, obj_in=recipe_in, user_id=current_user.id)
    
    # Generate feature vectors and LSH hashes for the new recipe
    recipe_repository.update_feature_vectors(db, recipe_id=recipe.id)
    
    return recipe

@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Get recipe by ID"""
    recipe = recipe_repository.get(db, id=recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    ingredients: Optional[str] = Form(None),
    instructions: Optional[str] = Form(None),
    categories: Optional[str] = Form(None),
    labels: Optional[str] = Form(None),
    cleaned_ingredients: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    prep_time: Optional[int] = Form(None),
    cook_time: Optional[int] = Form(None),
    servings: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    raw_data: Optional[str] = Form(None),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """
    Update recipe with optional image
    Also updates feature vectors for LSH search
    """
    # Get current recipe
    recipe = recipe_repository.get(db, id=recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Check ownership
    if recipe.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to update this recipe")
    
    # Process update data
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if ingredients is not None:
        update_data["ingredients"] = [i.strip() for i in ingredients.split(',')]
    if instructions is not None:
        update_data["instructions"] = instructions  # Now storing as full text
    if categories is not None:
        update_data["categories"] = [c.strip() for c in categories.split(',')]
    if labels is not None:
        update_data["labels"] = [l.strip() for l in labels.split(',')]
    if cleaned_ingredients is not None:
        update_data["cleaned_ingredients"] = [i.strip() for i in cleaned_ingredients.split(',')]
    if prompt is not None:
        update_data["prompt"] = prompt
    if prep_time is not None:
        update_data["prep_time"] = prep_time
    if cook_time is not None:
        update_data["cook_time"] = cook_time
    if servings is not None:
        update_data["servings"] = servings
    if raw_data is not None:
        try:
            update_data["raw_data"] = json.loads(raw_data)
        except json.JSONDecodeError:
            pass  # Ignore if invalid JSON
    
    # Handle image upload if provided
    if image:
        import os
        from config import settings
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save the file
        image_filename = f"{current_user.id}_{image.filename}"
        image_path = os.path.join(settings.UPLOAD_DIR, image_filename)
        with open(image_path, "wb") as buffer:
            contents = await image.read()
            buffer.write(contents)
        
        # Add image info to update data
        update_data["image_url"] = image_path
        update_data["image_name"] = image_filename
    
    # Create update object and update recipe
    recipe_in = RecipeUpdate(**update_data)
    recipe = recipe_repository.update(db, db_obj=recipe, obj_in=recipe_in)
    
    # Update feature vectors if text or image has changed
    if any(field in update_data for field in ["title", "description", "ingredients", "instructions", "image_url"]):
        recipe_repository.update_feature_vectors(db, recipe_id=recipe.id)
    
    return recipe

@router.delete("/{recipe_id}", response_model=RecipeResponse)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Delete recipe"""
    recipe = recipe_repository.get(db, id=recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Check ownership
    if recipe.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this recipe")
    
    recipe = recipe_repository.remove(db, id=recipe_id)
    
    # Note: The indices should be rebuilt to remove this recipe from search results
    # This is not done here to avoid performance impacts, but would be scheduled
    # as a background task in a real system
    
    return recipe

@router.get("/mine", response_model=List[RecipeResponse])
def get_my_recipes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all recipes owned by the currently authenticated user
    """
    return recipe_repository.get_by_user_id(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/search", response_model=List[RecipeResponse])
def search_recipes(
    query: str,
    categories: Optional[List[str]] = Query(None, description="Filter by categories"),
    sort_by: Optional[str] = Query("relevance", description="Sort options: relevance, newest, popular"),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Search recipes by text query with filtering and sorting options
    """
    return recipe_repository.advanced_search(
        db, 
        query=query,
        categories=categories,
        sort_by=sort_by,
        skip=skip,
        limit=limit
    )