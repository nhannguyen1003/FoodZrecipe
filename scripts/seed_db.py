#!/usr/bin/env python3
"""
Script to seed the database with initial users and recipes.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
import shutil
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add parent directory to Python path to make imports work
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from sqlalchemy import text
from database.session import engine
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def get_admin_user_id():
    """Get the ID of the admin user"""
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
        )
        user = result.fetchone()
        if user:
            return user[0]
        return None

def count_rows(table_name):
    """Count rows in a table"""
    with engine.connect() as connection:
        result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()

def seed_admin_user(session: Session, force: bool = False) -> int:
    """Seed admin user into the database and return the user ID."""
    try:
        # Check if admin user already exists
        admin = session.execute(
            text("SELECT id FROM users WHERE email = 'admin@example.com'")
        ).fetchone()
        
        if admin and not force:
            logger.info("Admin user already exists. Skipping.")
            return admin[0]
            
        if admin and force:
            logger.info("Admin user exists, but force flag is set. Recreating admin user.")
            session.execute(
                text("DELETE FROM users WHERE email = 'admin@example.com'")
            )
            session.commit()
        
        # Create password hash
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash("admin")
        
        # Insert admin user based on actual DB schema
        result = session.execute(
            text("""
            INSERT INTO users (
                username, email, hashed_password, role, is_active, created_at
            ) VALUES (
                'admin', 'admin@example.com', :hashed_password, 'admin', TRUE, NOW()
            ) RETURNING id
            """),
            {"hashed_password": hashed_password}
        )
        
        session.commit()
        admin_id = result.fetchone()[0]
        logger.info(f"Admin user created with ID: {admin_id}")
        return admin_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating admin user: {e}")
        return 0

def seed_users(force=False):
    """
    Seed database with sample users
    Returns the admin user ID
    """
    logger.info("Seeding users...")
    
    # Check if users already exist
    try:
        user_count = count_rows("users")
        if user_count > 0 and not force:
            logger.info(f"Users already exist in database ({user_count} users found)")
            # Get admin user ID
            admin_id = get_admin_user_id()
            return admin_id
    except Exception as e:
        logger.warning(f"Error checking for existing users: {e}")
    
    # Create sample users
    users = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "hashed_password": get_password_hash("adminpassword"),
            "role": "admin",
            "is_active": True
        },
        {
            "username": "user",
            "email": "user@example.com",
            "hashed_password": get_password_hash("userpassword"),
            "role": "regular",
            "is_active": True
        },
        {
            "username": "chef",
            "email": "chef@example.com",
            "hashed_password": get_password_hash("chefpassword"),
            "role": "regular",
            "is_active": True
        }
    ]
    
    # Insert users
    with engine.begin() as connection:
        for user in users:
            try:
                sql = """
                INSERT INTO users (username, email, hashed_password, role, is_active, created_at, updated_at)
                VALUES (:username, :email, :hashed_password, :role, :is_active, NOW(), NOW())
                """
                connection.execute(text(sql), user)
            except Exception as e:
                logger.error(f"Error inserting user {user['username']}: {e}")
    
    logger.info(f"Added {len(users)} users")
    
    # Get admin user ID
    admin_id = get_admin_user_id()
    return admin_id

def load_recipe_data(file_path):
    """
    Load recipe data from a line-delimited JSON file
    """
    logger.info(f"Loading recipe data from {file_path}")
    recipes = []
    invalid_lines = 0
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                try:
                    recipe = json.loads(line)
                    
                    # Verify required structure (title and ingredients are required)
                    title = recipe.get("title") or recipe.get("Title")
                    ingredients = recipe.get("ingredients") or recipe.get("Ingredients")
                    
                    if not title:
                        logger.warning(f"Line {line_num}: Missing title, setting default")
                        recipe["Title"] = "Untitled Recipe"
                    
                    if not ingredients:
                        logger.warning(f"Line {line_num}: Missing ingredients for '{title}'")
                        recipe["Ingredients"] = []
                    
                    recipes.append(recipe)
                    
                except json.JSONDecodeError as e:
                    invalid_lines += 1
                    logger.debug(f"Line {line_num}: Invalid JSON: {e}")
                    logger.debug(f"Problematic line: {line[:100]}...")
    except FileNotFoundError:
        logger.error(f"Recipe data file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error loading recipe data: {e}")
    
    if invalid_lines > 0:
        logger.warning(f"Skipped {invalid_lines} invalid JSON lines")
    
    logger.info(f"Loaded {len(recipes)} valid recipes")
    return recipes

def get_or_create_user(session: Session) -> int:
    """Get an existing user ID or create a dummy user and return its ID."""
    try:
        # Try to get any existing user
        user = session.execute(
            text("SELECT id FROM users LIMIT 1")
        ).fetchone()
        
        if user:
            logger.info(f"Using existing user with ID: {user[0]}")
            return user[0]
        
        # No users exist, create a basic dummy user
        logger.info("No users found. Creating a dummy user for recipes.")
        
        # Create password hash
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash("dummypassword")
        
        # Insert basic user with just required fields
        result = session.execute(
            text("""
            INSERT INTO users (
                username, email, hashed_password, role, is_active, created_at
            ) VALUES (
                'dummyuser', 'dummy@example.com', :hashed_password, 'regular', TRUE, NOW()
            ) RETURNING id
            """),
            {"hashed_password": hashed_password}
        )
        
        session.commit()
        dummy_id = result.fetchone()[0]
        logger.info(f"Created dummy user with ID: {dummy_id}")
        return dummy_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error getting/creating user: {e}")
        return None

def main():
    """
    Main entry point for the script
    """
    parser = argparse.ArgumentParser(description='Seed the database with initial data')
    parser.add_argument('--force', action='store_true', help='Force seeding even if data exists')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize database session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # Get existing user or create dummy user
        user_id = get_or_create_user(session)
        if not user_id:
            logger.error("Failed to get/create user for recipes")
            return
        
        # Get paths
        base_dir = Path(__file__).resolve().parent.parent
        data_dir = base_dir / "data" / "init_data" / "db"
        recipe_json_path = data_dir / "sample_recipes_cleaned.json"
        
        # Define images directory for reference (not copying)
        images_dir = data_dir / "Food Images"
        
        if not recipe_json_path.exists():
            logger.error(f"Recipe data file not found at {recipe_json_path}")
            return
        
        # Load recipe data
        logger.info(f"Loading recipe data from {recipe_json_path}...")
        recipe_data = load_recipe_data(recipe_json_path)
        
        if not recipe_data:
            logger.error("No valid recipe data found")
            return
            
        logger.info(f"Found {len(recipe_data)} recipes")
        
        # Seed recipes with user_id and images_dir
        added_count, failed_count = seed_recipes(session, recipe_data, args.force, user_id, images_dir)
        
        logger.info(f"Added {added_count} recipes, failed {failed_count} recipes")
        logger.info("Database seeding completed successfully")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        sys.exit(1)
        
    finally:
        if 'session' in locals():
            session.close()

def seed_recipes(session: Session, recipe_data: list, force: bool = False, user_id: int = None, images_dir: Path = None) -> Tuple[int, int]:
    """Seed recipes into the database."""
    added_count = 0
    failed_count = 0

    for recipe_json in recipe_data:
        try:
            # Process the recipe data
            title = recipe_json.get('Title', '')
            instructions = recipe_json.get('Instructions', '')
            ingredients = recipe_json.get('Ingredients', [])
            labels = recipe_json.get('labels', [])
            
            # Convert labels to categories
            categories = labels if labels else []
            
            # Get or set default values
            prep_time = None  # Allow null for prep_time
            cook_time = None  # Allow null for cook_time
            servings = 1 if recipe_json.get('servings') is None else recipe_json.get('servings')
            
            # Handle image
            image_name = recipe_json.get('image', '')
            image_url = None
            if image_name and images_dir:
                # Store the path to the original image
                image_url = str(images_dir / image_name)
            
            # Check if recipe already exists
            existing_recipe = session.execute(
                text("SELECT id FROM recipes WHERE title = :title"),
                {"title": title}
            ).fetchone()
            
            if existing_recipe and not force:
                logging.info(f"Recipe '{title}' already exists. Skipping.")
                continue
                
            # Create recipe dictionary based on actual DB schema
            recipe = {
                'title': title,
                'description': '',
                'ingredients': ingredients,
                'instructions': instructions.split('\n') if instructions else [],  # Convert to array
                'image_url': image_url,
                'categories': categories,
                'prep_time': prep_time,
                'cook_time': cook_time,
                'servings': servings,
                'user_id': user_id,
                'created_at': datetime.now()
            }
            
            # Insert recipe into database based on actual DB schema
            session.execute(
                text("""
                INSERT INTO recipes (
                    title, description, ingredients, instructions, image_url,
                    categories, prep_time, cook_time, servings, user_id,
                    created_at
                )
                VALUES (
                    :title, :description, :ingredients, :instructions, :image_url,
                    :categories, :prep_time, :cook_time, :servings, :user_id,
                    :created_at
                )
                """),
                recipe
            )
            session.commit()
            added_count += 1
            
        except Exception as e:
            session.rollback()
            logging.error(f"Error processing recipe : {e}")
            failed_count += 1
            
    return added_count, failed_count

if __name__ == "__main__":
    main() 