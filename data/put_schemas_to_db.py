#!/usr/bin/env python3
"""
Script to create and maintain the database schema for the FoodZrecipe application.
This script will create the necessary tables if they don't exist, and will
drop and recreate tables with incorrect schema.
"""
import os
import sys
import logging
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import from backend
from backend.utils.lsh_utils import (
    EMBEDDING_DIM_TITLE,
    EMBEDDING_DIM_INGREDIENTS,
    EMBEDDING_DIM_INSTRUCTIONS,
    EMBEDDING_DIM_TEXT
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_table_exists(conn, table_name):
    """
    Check if a table exists in the database.
    
    Args:
        conn: Database connection
        table_name: Name of the table to check
        
    Returns:
        True if the table exists, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        )
    """, (table_name,))
    
    return cursor.fetchone()[0]

def check_table_schema(conn, table_name, expected_columns):
    """
    Check if a table has the expected schema.
    
    Args:
        conn: Database connection
        table_name: Name of the table to check
        expected_columns: List of column names that should exist
        
    Returns:
        True if the table has all expected columns, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = %s
    """, (table_name,))
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    missing_columns = [col for col in expected_columns if col not in existing_columns]
    
    if missing_columns:
        logger.warning(f"Table {table_name} is missing columns: {missing_columns}")
        return False
    
    return True

def drop_table(conn, table_name):
    """
    Drop a table from the database.
    
    Args:
        conn: Database connection
        table_name: Name of the table to drop
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        logger.info(f"Dropping table {table_name}")
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error dropping table {table_name}: {e}")
        conn.rollback()
        return False

def create_user_table(conn):
    """
    Create the user table.
    
    Args:
        conn: Database connection
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        logger.info("Creating user table")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "user" (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating user table: {e}")
        conn.rollback()
        return False

def create_recipe_table(conn):
    """
    Create the recipe table with multi-field LSH support.
    
    Args:
        conn: Database connection
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        logger.info("Creating recipe table with multi-field LSH support")
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS recipe (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                ingredients TEXT[] NOT NULL,
                instructions TEXT NOT NULL,
                image_name VARCHAR(255),
                cleaned_ingredients TEXT[],
                user_id INTEGER REFERENCES "user"(id),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                
                -- Multi-field LSH columns
                title_feature_vector FLOAT[{EMBEDDING_DIM_TITLE}],
                title_hash_buckets INTEGER[],
                ingredients_feature_vector FLOAT[{EMBEDDING_DIM_INGREDIENTS}],
                ingredients_hash_buckets INTEGER[],
                instructions_feature_vector FLOAT[{EMBEDDING_DIM_INSTRUCTIONS}],
                instructions_hash_buckets INTEGER[],
                text_feature_vector FLOAT[{EMBEDDING_DIM_TEXT}],
                text_hash_buckets INTEGER[]
            )
        """)
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating recipe table: {e}")
        conn.rollback()
        return False

def create_recipe_label_table(conn):
    """
    Create the recipe_label table.
    
    Args:
        conn: Database connection
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        logger.info("Creating recipe_label table")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_label (
                recipe_id INTEGER REFERENCES recipe(id) ON DELETE CASCADE,
                label VARCHAR(255) NOT NULL,
                PRIMARY KEY (recipe_id, label)
            )
        """)
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating recipe_label table: {e}")
        conn.rollback()
        return False

def create_admin_user(conn):
    """
    Create a default admin user if no users exist.
    
    Args:
        conn: Database connection
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Check if any users exist
        cursor.execute('SELECT COUNT(*) FROM "user"')
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            logger.info("Creating default admin user")
            cursor.execute("""
                INSERT INTO "user" (email, password, name, is_admin)
                VALUES ('admin@example.com', 'password', 'Admin', TRUE)
            """)
            conn.commit()
            logger.info("Default admin user created")
        
        return True
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        conn.rollback()
        return False

def setup_schema(conn, force_recreate=False):
    """
    Set up the database schema.
    
    Args:
        conn: Database connection
        force_recreate: If True, drop and recreate all tables regardless of current state
        
    Returns:
        True if successful, False otherwise
    """
    # Define expected columns for each table
    user_columns = [
        'id', 'email', 'password', 'name', 'is_admin', 'created_at', 'updated_at'
    ]
    
    recipe_columns = [
        'id', 'title', 'ingredients', 'instructions', 'image_name', 'cleaned_ingredients',
        'user_id', 'created_at', 'updated_at',
        'title_feature_vector', 'title_hash_buckets',
        'ingredients_feature_vector', 'ingredients_hash_buckets',
        'instructions_feature_vector', 'instructions_hash_buckets',
        'text_feature_vector', 'text_hash_buckets'
    ]
    
    recipe_label_columns = ['recipe_id', 'label']
    
    # Check user table
    if force_recreate or not check_table_exists(conn, 'user') or not check_table_schema(conn, 'user', user_columns):
        if check_table_exists(conn, 'user'):
            if not drop_table(conn, 'user'):
                return False
        if not create_user_table(conn):
            return False
    
    # Check recipe table
    if force_recreate or not check_table_exists(conn, 'recipe') or not check_table_schema(conn, 'recipe', recipe_columns):
        if check_table_exists(conn, 'recipe'):
            if not drop_table(conn, 'recipe'):
                return False
        if not create_recipe_table(conn):
            return False
    
    # Check recipe_label table
    if force_recreate or not check_table_exists(conn, 'recipe_label') or not check_table_schema(conn, 'recipe_label', recipe_label_columns):
        if check_table_exists(conn, 'recipe_label'):
            if not drop_table(conn, 'recipe_label'):
                return False
        if not create_recipe_label_table(conn):
            return False
    
    # Create admin user
    if not create_admin_user(conn):
        return False
    
    logger.info("Database schema setup completed successfully")
    return True

def main():
    """
    Main function.
    """
    load_dotenv()
    
    # Get database connection details from environment variables
    db_name = os.getenv('POSTGRES_DB', 'food_recipe')
    db_user = os.getenv('POSTGRES_USER', 'app_user')
    db_password = os.getenv('POSTGRES_PASSWORD', 'app_password')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    
    # Parse command line arguments
    force_recreate = False
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        force_recreate = True
        logger.info("Force recreate mode enabled")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        
        # Set up the schema
        if not setup_schema(conn, force_recreate):
            logger.error("Schema setup failed")
            conn.close()
            sys.exit(1)
        
        conn.close()
        logger.info("Schema setup completed successfully")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
