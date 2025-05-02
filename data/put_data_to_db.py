#!/usr/bin/env python3
"""
Script to load recipe data with multi-field LSH embeddings into the database.
This script validates the database schema, truncates tables if requested, and loads recipe data.
"""
import json
import os
import psycopg2
from dotenv import load_dotenv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to Python path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the LSH constants from backend
from backend.utils.lsh_utils import (
    EMBEDDING_DIM_TITLE, 
    EMBEDDING_DIM_INGREDIENTS,
    EMBEDDING_DIM_INSTRUCTIONS,
    EMBEDDING_DIM_TEXT,
    EMBEDDING_DIM_IMAGE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_database_schema(conn) -> bool:
    """
    Verify that the database schema has the required columns for multi-field LSH.
    """
    logger.info("Verifying database schema for multi-field LSH embeddings...")
    
    required_columns = [
        "title_feature_vector", "title_hash_buckets",
        "ingredients_feature_vector", "ingredients_hash_buckets",
        "instructions_feature_vector", "instructions_hash_buckets",
        "text_feature_vector", "text_hash_buckets",
        "image_feature_vector", "image_hash_buckets"
    ]
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'recipe'
    """)
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    missing_columns = [col for col in required_columns if col not in existing_columns]
    
    if missing_columns:
        logger.error(f"Missing required columns in database schema: {missing_columns}")
        return False
    
    logger.info("Database schema verification successful")
    return True

def truncate_tables(conn, tables: List[str]):
    """
    Truncate the specified tables in the database.
    
    Args:
        conn: Database connection
        tables: List of table names to truncate
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Truncating tables: {tables}")
    
    cursor = conn.cursor()
    try:
        for table in tables:
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
            logger.info(f"Truncated table '{table}'")
        
        conn.commit()
        logger.info("Tables truncated successfully")
        return True
    except Exception as e:
        logger.error(f"Error truncating tables: {e}")
        conn.rollback()
        return False

def validate_vectors(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure that recipe vectors have the correct dimensions.
    If vectors are missing or incorrect, they are set to zero arrays.
    """
    # Validate title feature vector
    if 'title_feature_vector' in recipe:
        if len(recipe['title_feature_vector']) < EMBEDDING_DIM_TITLE:
            # Pad with zeros
            recipe['title_feature_vector'].extend([0.0] * (EMBEDDING_DIM_TITLE - len(recipe['title_feature_vector'])))
        elif len(recipe['title_feature_vector']) > EMBEDDING_DIM_TITLE:
            # Truncate
            recipe['title_feature_vector'] = recipe['title_feature_vector'][:EMBEDDING_DIM_TITLE]
    else:
        recipe['title_feature_vector'] = [0.0] * EMBEDDING_DIM_TITLE
        logger.warning(f"Missing title feature vector for recipe '{recipe.get('Title', 'unknown')}'")
    
    # Validate ingredients feature vector
    if 'ingredients_feature_vector' in recipe:
        if len(recipe['ingredients_feature_vector']) < EMBEDDING_DIM_INGREDIENTS:
            recipe['ingredients_feature_vector'].extend([0.0] * (EMBEDDING_DIM_INGREDIENTS - len(recipe['ingredients_feature_vector'])))
        elif len(recipe['ingredients_feature_vector']) > EMBEDDING_DIM_INGREDIENTS:
            recipe['ingredients_feature_vector'] = recipe['ingredients_feature_vector'][:EMBEDDING_DIM_INGREDIENTS]
    else:
        recipe['ingredients_feature_vector'] = [0.0] * EMBEDDING_DIM_INGREDIENTS
        logger.warning(f"Missing ingredients feature vector for recipe '{recipe.get('Title', 'unknown')}'")
    
    # Validate instructions feature vector
    if 'instructions_feature_vector' in recipe:
        if len(recipe['instructions_feature_vector']) < EMBEDDING_DIM_INSTRUCTIONS:
            recipe['instructions_feature_vector'].extend([0.0] * (EMBEDDING_DIM_INSTRUCTIONS - len(recipe['instructions_feature_vector'])))
        elif len(recipe['instructions_feature_vector']) > EMBEDDING_DIM_INSTRUCTIONS:
            recipe['instructions_feature_vector'] = recipe['instructions_feature_vector'][:EMBEDDING_DIM_INSTRUCTIONS]
    else:
        recipe['instructions_feature_vector'] = [0.0] * EMBEDDING_DIM_INSTRUCTIONS
        logger.warning(f"Missing instructions feature vector for recipe '{recipe.get('Title', 'unknown')}'")
    
    # Validate text feature vector
    if 'text_feature_vector' in recipe:
        if len(recipe['text_feature_vector']) < EMBEDDING_DIM_TEXT:
            recipe['text_feature_vector'].extend([0.0] * (EMBEDDING_DIM_TEXT - len(recipe['text_feature_vector'])))
        elif len(recipe['text_feature_vector']) > EMBEDDING_DIM_TEXT:
            recipe['text_feature_vector'] = recipe['text_feature_vector'][:EMBEDDING_DIM_TEXT]
    else:
        recipe['text_feature_vector'] = [0.0] * EMBEDDING_DIM_TEXT
        logger.warning(f"Missing text feature vector for recipe '{recipe.get('Title', 'unknown')}'")
    
    # Validate image feature vector
    if 'image_feature_vector' in recipe:
        if len(recipe['image_feature_vector']) < EMBEDDING_DIM_IMAGE:
            # Pad with zeros
            recipe['image_feature_vector'].extend([0.0] * (EMBEDDING_DIM_IMAGE - len(recipe['image_feature_vector'])))
        elif len(recipe['image_feature_vector']) > EMBEDDING_DIM_IMAGE:
            # Truncate
            recipe['image_feature_vector'] = recipe['image_feature_vector'][:EMBEDDING_DIM_IMAGE]
    else:
        recipe['image_feature_vector'] = [0.0] * EMBEDDING_DIM_IMAGE
        logger.warning(f"Missing image feature vector for recipe '{recipe.get('Title', 'unknown')}'")
    
    # Ensure hash buckets exist
    if 'title_hash_buckets' not in recipe:
        recipe['title_hash_buckets'] = []
        logger.warning(f"Missing title hash buckets for recipe '{recipe.get('Title', 'unknown')}'")
    
    if 'ingredients_hash_buckets' not in recipe:
        recipe['ingredients_hash_buckets'] = []
        logger.warning(f"Missing ingredients hash buckets for recipe '{recipe.get('Title', 'unknown')}'")
    
    if 'instructions_hash_buckets' not in recipe:
        recipe['instructions_hash_buckets'] = []
        logger.warning(f"Missing instructions hash buckets for recipe '{recipe.get('Title', 'unknown')}'")
    
    if 'text_hash_buckets' not in recipe:
        recipe['text_hash_buckets'] = []
        logger.warning(f"Missing text hash buckets for recipe '{recipe.get('Title', 'unknown')}'")
    
    # Ensure hash buckets exist for image
    if 'image_hash_buckets' not in recipe:
        recipe['image_hash_buckets'] = []
        logger.warning(f"Missing image hash buckets for recipe '{recipe.get('Title', 'unknown')}'")
    
    return recipe

def load_recipes_from_json(conn, json_file_path):
    """
    Load recipes from a JSON file and insert them into the database.
    The JSON file is expected to be in JSONL format (one JSON object per line).
    """
    logger.info(f"Loading recipes from {json_file_path}")
    
    cursor = conn.cursor()
    
    # Get the admin user ID
    cursor.execute('SELECT id FROM "user" WHERE email = %s', ('admin@example.com',))
    admin_result = cursor.fetchone()
    if admin_result is None:
        logger.error("Admin user not found. Make sure to run put_schemas_to_db.py first.")
        return False
    
    user_id = admin_result[0]
    
    # Generate embeddings if the file is not found
    if not os.path.exists(json_file_path):
        logger.error(f"File not found: {json_file_path}")
        logger.info("Please run get_data_lsh.py to generate embeddings first")
        return False
    
    recipes_loaded = 0
    recipes_error = 0
    
    try:
        with open(json_file_path, 'r') as f:
            # Process one line at a time (JSONL format)
            for line_number, line in enumerate(f, 1):
                try:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                        
                    recipe = json.loads(line)
                    
                    # Validate feature vectors and hash buckets
                    recipe = validate_vectors(recipe)
                    
                    # Insert the recipe
                    cursor.execute("""
                        INSERT INTO recipe (
                            title, ingredients, instructions, image_name, cleaned_ingredients,
                            user_id, text_feature_vector, text_hash_buckets,
                            title_feature_vector, title_hash_buckets,
                            ingredients_feature_vector, ingredients_hash_buckets,
                            instructions_feature_vector, instructions_hash_buckets,
                            image_feature_vector, image_hash_buckets
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        recipe.get('Title', ''),
                        recipe.get('Ingredients', []),
                        recipe.get('Instructions', ''),
                        recipe.get('Image_Name', ''),
                        recipe.get('Cleaned_Ingredients', []),
                        user_id,
                        recipe.get('text_feature_vector', []),
                        recipe.get('text_hash_buckets', []),
                        recipe.get('title_feature_vector', []),
                        recipe.get('title_hash_buckets', []),
                        recipe.get('ingredients_feature_vector', []),
                        recipe.get('ingredients_hash_buckets', []),
                        recipe.get('instructions_feature_vector', []),
                        recipe.get('instructions_hash_buckets', []),
                        recipe.get('image_feature_vector', []),
                        recipe.get('image_hash_buckets', [])
                    ))
                    
                    recipe_id = cursor.fetchone()[0]
                    
                    # Insert the labels
                    for label in recipe.get('labels', []):
                        cursor.execute("""
                            INSERT INTO recipe_label (recipe_id, label)
                            VALUES (%s, %s)
                            ON CONFLICT (recipe_id, label) DO NOTHING
                        """, (recipe_id, label))
                    
                    recipes_loaded += 1
                    
                    if recipes_loaded % 100 == 0:
                        logger.info(f"Loaded {recipes_loaded} recipes so far")
                        conn.commit()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON error on line {line_number}: {e}")
                    recipes_error += 1
                except Exception as e:
                    logger.error(f"Error processing recipe on line {line_number}: {e}")
                    recipes_error += 1
        
        conn.commit()
        logger.info(f"Loaded {recipes_loaded} recipes successfully")
        logger.info(f"Failed to load {recipes_error} recipes")
        return True
        
    except Exception as e:
        logger.error(f"Error loading recipes: {e}")
        conn.rollback()
        return False

def main():
    """
    Main function to load recipe data into the database.
    """
    load_dotenv()
    
    db_name = os.getenv('POSTGRES_DB', 'food_recipe')
    db_user = os.getenv('POSTGRES_USER', 'app_user')
    db_password = os.getenv('POSTGRES_PASSWORD', 'app_password')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    
    # Default paths
    data_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "db"
    json_path = data_dir / "sample_recipes_with_hashed.json"
    
    # Check if the path exists
    if not json_path.exists():
        logger.error(f"JSON file not found at {json_path}")
        return
    
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        
        # Verify database schema
        if not verify_database_schema(conn):
            logger.error("Database schema verification failed. Run migrations first.")
            return
        
        # Truncate tables
        tables_to_truncate = ['recipe', 'recipe_label']
        if not truncate_tables(conn, tables_to_truncate):
            logger.error("Failed to truncate tables")
            return
        
        # Load data
        if not load_recipes_from_json(conn, json_path):
            logger.error("Failed to load recipes")
            return
        
        conn.close()
        logger.info("Data loading complete")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 