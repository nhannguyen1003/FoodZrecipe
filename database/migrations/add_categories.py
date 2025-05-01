"""
Migration script to add category functionality
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Table, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

from config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def run_migration():
    """Run the migration to add category tables"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Add default categories if needed
    session = SessionLocal()
    try:
        # Check if categories already exist
        result = session.execute("SELECT COUNT(*) FROM categories").scalar()
        
        # Add default categories if none exist
        if result == 0:
            # Add default categories
            default_categories = [
                {"name": "Breakfast", "description": "Morning recipes to start your day"},
                {"name": "Lunch", "description": "Midday meals"},
                {"name": "Dinner", "description": "Evening meals"},
                {"name": "Dessert", "description": "Sweet treats"},
                {"name": "Appetizer", "description": "Starters and small bites"},
                {"name": "Soup", "description": "Soups and stews"},
                {"name": "Salad", "description": "Fresh salads"},
                {"name": "Vegetarian", "description": "Meat-free recipes"},
                {"name": "Vegan", "description": "Plant-based recipes"},
                {"name": "Gluten-Free", "description": "Recipes without gluten"},
                {"name": "Quick & Easy", "description": "Fast recipes for busy days"},
                {"name": "Healthy", "description": "Nutritious options"},
                {"name": "Comfort Food", "description": "Hearty, satisfying recipes"},
                {"name": "Baking", "description": "Breads, pastries, and baked goods"},
                {"name": "Holiday", "description": "Special occasion recipes"}
            ]
            
            for category in default_categories:
                session.execute(
                    "INSERT INTO categories (name, description, created_at, updated_at) VALUES (:name, :description, :created_at, :updated_at)",
                    {
                        "name": category["name"],
                        "description": category["description"],
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                )
                
            session.commit()
            print(f"Added {len(default_categories)} default categories")
        else:
            print("Categories already exist, skipping default category creation")
            
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {e}")
    finally:
        session.close()

    print("Category migration completed successfully")

# Define models for migration
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Add index for performance
    __table_args__ = (
        Index('idx_category_name', 'name'),
    )

# Association table for many-to-many relationship between recipes and categories
recipe_category = Table(
    "recipe_category",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
)

if __name__ == "__main__":
    run_migration() 