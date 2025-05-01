from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from database.session import get_db
from database.repositories.category_repository import CategoryRepository
from backend.schemas.category import (
    CategoryResponse, 
    CategoryCreate, 
    CategoryUpdate,
    CategoryWithRecipesResponse
)
from backend.schemas.recipe import RecipeResponse
from backend.core.security import get_current_user, get_current_admin_user

# Initialize the category router
router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "Not found"}},
)

# Get all categories
@router.get("/", response_model=List[CategoryWithRecipesResponse])
def get_categories(
    db: Session = Depends(get_db),
):
    """Get all categories with recipe count"""
    category_repo = CategoryRepository(db)
    results = category_repo.get_all_with_recipe_count()
    
    # Format the response
    categories = []
    for category, recipe_count in results:
        category_dict = CategoryWithRecipesResponse.from_orm(category).dict()
        category_dict["recipe_count"] = recipe_count
        categories.append(CategoryWithRecipesResponse(**category_dict))
    
    return categories

# Get a specific category
@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    """Get a category by ID"""
    category_repo = CategoryRepository(db)
    category = category_repo.get(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    return category

# Get recipes by category
@router.get("/{category_id}/recipes", response_model=List[RecipeResponse])
def get_recipes_by_category(
    category_id: int,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Get all recipes in a category"""
    category_repo = CategoryRepository(db)
    category = category_repo.get(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    recipes = category_repo.get_recipes_by_category(
        category_id=category_id,
        limit=limit,
        offset=offset
    )
    
    return recipes

# Admin endpoints for category management
# Create a new category
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Create a new category (admin only)"""
    category_repo = CategoryRepository(db)
    
    # Check if category with same name already exists
    existing = category_repo.get_by_name(category.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )
    
    return category_repo.create(category.dict())

# Update a category
@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Update a category (admin only)"""
    category_repo = CategoryRepository(db)
    
    # Check if category exists
    existing = category_repo.get(category_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    # Check for name conflict if name is being updated
    if category_update.name and category_update.name != existing.name:
        name_conflict = category_repo.get_by_name(category_update.name)
        if name_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists",
            )
    
    # Update the category
    update_data = category_update.dict(exclude_unset=True)
    return category_repo.update(category_id, update_data)

# Delete a category
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Delete a category (admin only)"""
    category_repo = CategoryRepository(db)
    
    # Check if category exists
    existing = category_repo.get(category_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    # Delete the category
    category_repo.delete(category_id)
    return None

# Add a recipe to a category
@router.post("/{category_id}/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_recipe_to_category(
    category_id: int,
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Add a recipe to a category"""
    category_repo = CategoryRepository(db)
    
    # Check if category exists
    category = category_repo.get(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    # Add the recipe to the category
    success = category_repo.add_recipe_to_category(category_id, recipe_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipe is already in this category",
        )
    
    return None

# Remove a recipe from a category
@router.delete("/{category_id}/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_recipe_from_category(
    category_id: int,
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Remove a recipe from a category"""
    category_repo = CategoryRepository(db)
    
    # Check if category exists
    category = category_repo.get(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    # Remove the recipe from the category
    success = category_repo.remove_recipe_from_category(category_id, recipe_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipe is not in this category",
        )
    
    return None 