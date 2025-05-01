# TODO: Implement recipe API endpoints
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeResponse
from backend.core.security import get_current_user
from backend.models.user import User
from database.session import get_db
from database.repositories.recipe_repository import recipe_repository

router = APIRouter()

@router.get("/", response_model=List[RecipeResponse])
def get_recipes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all recipes with pagination"""
    recipes = recipe_repository.get_multi(db, skip=skip, limit=limit)
    return recipes

@router.post("/", response_model=RecipeResponse)
async def create_recipe(
    title: str = Form(...),
    description: str = Form(...),
    ingredients: str = Form(...),  # Comma-separated list
    instructions: str = Form(...),  # Newline-separated steps
    categories: str = Form(...),   # Comma-separated list
    prep_time: int = Form(...),
    cook_time: int = Form(...),
    servings: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
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
        "instructions": [i.strip() for i in instructions.split('\n') if i.strip()],
        "categories": [c.strip() for c in categories.split(',')],
        "prep_time": prep_time,
        "cook_time": cook_time,
        "servings": servings,
    }
    
    # Handle image upload if provided
    image_path = None
    if image:
        import os
        from config import settings
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save the file
        image_path = os.path.join(settings.UPLOAD_DIR, f"{current_user.id}_{image.filename}")
        with open(image_path, "wb") as buffer:
            contents = await image.read()
            buffer.write(contents)
        
        # Add image path to recipe data
        recipe_data["image_url"] = image_path
    
    # Create recipe object
    recipe_in = RecipeCreate(**recipe_data)
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
    prep_time: Optional[int] = Form(None),
    cook_time: Optional[int] = Form(None),
    servings: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
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
        update_data["instructions"] = [i.strip() for i in instructions.split('\n') if i.strip()]
    if categories is not None:
        update_data["categories"] = [c.strip() for c in categories.split(',')]
    if prep_time is not None:
        update_data["prep_time"] = prep_time
    if cook_time is not None:
        update_data["cook_time"] = cook_time
    if servings is not None:
        update_data["servings"] = servings
    
    # Handle image upload if provided
    if image:
        import os
        from config import settings
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save the file
        image_path = os.path.join(settings.UPLOAD_DIR, f"{current_user.id}_{image.filename}")
        with open(image_path, "wb") as buffer:
            contents = await image.read()
            buffer.write(contents)
        
        # Add image path to update data
        update_data["image_url"] = image_path
    
    # Create update object and update recipe
    recipe_in = RecipeUpdate(**update_data)
    recipe = recipe_repository.update(db, db_obj=recipe, obj_in=recipe_in)
    
    # Update feature vectors if text or image has changed
    if any(field in update_data for field in ["title", "description", "ingredients", "instructions", "image_url"]):
        recipe_repository.update_feature_vectors(db, recipe_id=recipe.id)
    
    return recipe

@router.delete("/{recipe_id}", response_model=RecipeResponse)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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