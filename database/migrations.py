"""
Database migrations script to update existing tables to match our models
"""
import logging
import os
import sys
import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.session import engine, SessionLocal, Base
from database.base import register_models

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_users_table():
    """Add missing columns to the users table"""
    logger.info("Running migration for users table...")
    
    with engine.connect() as conn:
        # Check if updated_at column exists
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='updated_at'"))
        if result.rowcount == 0:
            logger.info("Adding updated_at column to users table")
            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()"))
            
        # Check if last_login column exists
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='last_login'"))
        if result.rowcount == 0:
            logger.info("Adding last_login column to users table")
            conn.execute(text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP"))
            
        conn.commit()
        logger.info("Users table migration completed")
        
def migrate_recipes_table():
    """Update recipes table if needed"""
    logger.info("Checking recipes table structure...")
    
    with engine.connect() as conn:
        # Check for missing text_feature_vector column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='text_feature_vector'"))
        if result.rowcount == 0:
            logger.info("Adding text_feature_vector column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN text_feature_vector FLOAT[]"))
            
        # Check for missing text_hash_buckets column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='text_hash_buckets'"))
        if result.rowcount == 0:
            logger.info("Adding text_hash_buckets column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN text_hash_buckets INTEGER[]"))
            
        # Check for missing image_feature_vector column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='image_feature_vector'"))
        if result.rowcount == 0:
            logger.info("Adding image_feature_vector column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN image_feature_vector FLOAT[]"))
            
        # Check for missing image_hash_buckets column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='image_hash_buckets'"))
        if result.rowcount == 0:
            logger.info("Adding image_hash_buckets column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN image_hash_buckets INTEGER[]"))
            
        # Check for missing combined_hash_buckets column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='combined_hash_buckets'"))
        if result.rowcount == 0:
            logger.info("Adding combined_hash_buckets column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN combined_hash_buckets INTEGER[]"))
        
        # Check for missing cleaned_ingredients column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='cleaned_ingredients'"))
        if result.rowcount == 0:
            logger.info("Adding cleaned_ingredients column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN cleaned_ingredients VARCHAR[]"))
        
        # Check for missing image_name column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='image_name'"))
        if result.rowcount == 0:
            logger.info("Adding image_name column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN image_name VARCHAR(255)"))
        
        # Check for missing labels column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='labels'"))
        if result.rowcount == 0:
            logger.info("Adding labels column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN labels VARCHAR[]"))
        
        # Check for missing prompt column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='prompt'"))
        if result.rowcount == 0:
            logger.info("Adding prompt column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN prompt TEXT"))
        
        # Check for missing updated_at column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='updated_at'"))
        if result.rowcount == 0:
            logger.info("Adding updated_at column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()"))
        
        # Check for missing raw_data column
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' AND column_name='raw_data'"))
        if result.rowcount == 0:
            logger.info("Adding raw_data column to recipes table")
            conn.execute(text("ALTER TABLE recipes ADD COLUMN raw_data JSONB"))
        
        conn.commit()
        logger.info("Recipes table migration completed")
        
def run_migrations():
    """Run all migrations"""
    logger.info("Starting database migrations...")
    
    # Run all migrations
    migrate_users_table()
    migrate_recipes_table()
    
    logger.info("All migrations completed successfully")
    
if __name__ == "__main__":
    run_migrations() 