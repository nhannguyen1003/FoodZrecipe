"""
Migration script to add multi-field LSH columns to the recipes table.
Part of SEARCH-102 implementation.
"""
import logging
import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from database.session import engine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_recipes_for_multi_field_lsh():
    """
    Add field-specific embedding columns to the recipes table for multi-field LSH search
    """
    logger.info("Starting migration for multi-field LSH columns in recipes table...")
    
    with engine.connect() as conn:
        # Check for missing title_feature_vector column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='title_feature_vector'"))
        if result.rowcount == 0:
            logger.info("Adding title_feature_vector column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN title_feature_vector FLOAT[]"))
            
        # Check for missing ingredients_feature_vector column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='ingredients_feature_vector'"))
        if result.rowcount == 0:
            logger.info("Adding ingredients_feature_vector column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN ingredients_feature_vector FLOAT[]"))
            
        # Check for missing instructions_feature_vector column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='instructions_feature_vector'"))
        if result.rowcount == 0:
            logger.info("Adding instructions_feature_vector column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN instructions_feature_vector FLOAT[]"))
            
        # Check for missing title_hash_buckets column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='title_hash_buckets'"))
        if result.rowcount == 0:
            logger.info("Adding title_hash_buckets column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN title_hash_buckets INTEGER[]"))
            
        # Check for missing ingredients_hash_buckets column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='ingredients_hash_buckets'"))
        if result.rowcount == 0:
            logger.info("Adding ingredients_hash_buckets column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN ingredients_hash_buckets INTEGER[]"))
            
        # Check for missing instructions_hash_buckets column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='instructions_hash_buckets'"))
        if result.rowcount == 0:
            logger.info("Adding instructions_hash_buckets column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN instructions_hash_buckets INTEGER[]"))
        
        # Create indices for the new hash bucket columns
        logger.info("Creating indices for the new hash bucket columns")
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_recipe_title_hash ON recipes USING gin(title_hash_buckets)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_hash ON recipes USING gin(ingredients_hash_buckets)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_recipe_instructions_hash ON recipes USING gin(instructions_hash_buckets)"))
        
        conn.commit()
        logger.info("Multi-field LSH migration completed successfully")

if __name__ == "__main__":
    migrate_recipes_for_multi_field_lsh() 