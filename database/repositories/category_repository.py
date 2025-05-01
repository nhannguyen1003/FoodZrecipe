from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any, Tuple
from database.repositories.base_repository import BaseRepository
from backend.models.category import Category
from backend.models.recipe import Recipe, recipe_category

class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(db, Category)
    
    def get_by_name(self, name: str) -> Optional[Category]:
        """Get a category by name"""
        return self.db.query(self.model).filter(self.model.name == name).first()
    
    def get_all_with_recipe_count(self) -> List[Tuple[Category, int]]:
        """Get all categories with recipe count"""
        result = (
            self.db.query(
                self.model, 
                func.count(recipe_category.c.recipe_id).label("recipe_count")
            )
            .outerjoin(recipe_category, self.model.id == recipe_category.c.category_id)
            .group_by(self.model.id)
            .all()
        )
        return result

    def add_recipe_to_category(self, category_id: int, recipe_id: int) -> bool:
        """Add a recipe to a category"""
        # Check if the relationship already exists
        exists = (
            self.db.query(recipe_category)
            .filter(
                recipe_category.c.category_id == category_id,
                recipe_category.c.recipe_id == recipe_id
            )
            .first()
        )
        
        if exists:
            return False
            
        # Add the relationship
        stmt = recipe_category.insert().values(
            category_id=category_id, 
            recipe_id=recipe_id
        )
        self.db.execute(stmt)
        self.db.commit()
        return True
        
    def remove_recipe_from_category(self, category_id: int, recipe_id: int) -> bool:
        """Remove a recipe from a category"""
        stmt = recipe_category.delete().where(
            recipe_category.c.category_id == category_id,
            recipe_category.c.recipe_id == recipe_id
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
    
    def get_recipes_by_category(self, category_id: int, limit: int = 100, offset: int = 0) -> List[Recipe]:
        """Get all recipes in a category"""
        recipes = (
            self.db.query(Recipe)
            .join(recipe_category, Recipe.id == recipe_category.c.recipe_id)
            .filter(recipe_category.c.category_id == category_id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return recipes
    
    def get_categories_for_recipe(self, recipe_id: int) -> List[Category]:
        """Get all categories for a recipe"""
        categories = (
            self.db.query(Category)
            .join(recipe_category, Category.id == recipe_category.c.category_id)
            .filter(recipe_category.c.recipe_id == recipe_id)
            .all()
        )
        return categories 