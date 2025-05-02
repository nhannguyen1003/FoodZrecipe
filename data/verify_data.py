#!/usr/bin/env python3
"""
Script to verify the data loaded in the database.
"""
import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Add project root to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the LSH constants
from backend.utils.lsh_utils import (
    EMBEDDING_DIM_TITLE,
    EMBEDDING_DIM_INGREDIENTS,
    EMBEDDING_DIM_INSTRUCTIONS,
    EMBEDDING_DIM_TEXT,
    EMBEDDING_DIM_IMAGE
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_data():
    """
    Verify the data loaded in the database.
    """
    load_dotenv()
    
    # Get database connection details from environment variables
    db_name = os.getenv('POSTGRES_DB', 'food_recipe')
    db_user = os.getenv('POSTGRES_USER', 'app_user')
    db_password = os.getenv('POSTGRES_PASSWORD', 'app_password')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        
        cursor = conn.cursor()
        
        # Check the number of recipes
        cursor.execute('SELECT COUNT(*) FROM recipe')
        recipe_count = cursor.fetchone()[0]
        logger.info(f"Total recipes in database: {recipe_count}")
        
        # Check the number of recipe labels
        cursor.execute('SELECT COUNT(*) FROM recipe_label')
        label_count = cursor.fetchone()[0]
        logger.info(f"Total recipe labels in database: {label_count}")
        
        # Check average number of labels per recipe
        if recipe_count > 0:
            avg_labels = label_count / recipe_count
            logger.info(f"Average labels per recipe: {avg_labels:.2f}")
        
        # Check sample recipes with their hash bucket counts, including image hash buckets
        cursor.execute("""
            SELECT 
                id, 
                title, 
                array_length(title_hash_buckets, 1) as title_hash_count,
                array_length(ingredients_hash_buckets, 1) as ingredients_hash_count,
                array_length(instructions_hash_buckets, 1) as instructions_hash_count,
                array_length(text_hash_buckets, 1) as text_hash_count,
                array_length(image_hash_buckets, 1) as image_hash_count,
                image_name
            FROM recipe 
            LIMIT 5
        """)
        
        logger.info("Sample recipes with hash bucket counts:")
        for row in cursor.fetchall():
            logger.info(f"ID: {row[0]}, Title: {row[1]}")
            logger.info(f"  - Title hash buckets: {row[2]}")
            logger.info(f"  - Ingredients hash buckets: {row[3]}")
            logger.info(f"  - Instructions hash buckets: {row[4]}")
            logger.info(f"  - Text hash buckets: {row[5]}")
            logger.info(f"  - Image hash buckets: {row[6]}")
            logger.info(f"  - Image name: {row[7]}")
        
        # Check for missing hash buckets, including image hash buckets
        cursor.execute("""
            SELECT COUNT(*) FROM recipe
            WHERE 
                array_length(title_hash_buckets, 1) IS NULL OR
                array_length(ingredients_hash_buckets, 1) IS NULL OR
                array_length(instructions_hash_buckets, 1) IS NULL OR
                array_length(text_hash_buckets, 1) IS NULL OR
                array_length(image_hash_buckets, 1) IS NULL
        """)
        
        missing_hash_count = cursor.fetchone()[0]
        logger.info(f"Recipes with missing hash buckets: {missing_hash_count}")
        
        # Check for recipes with non-empty image hash buckets
        cursor.execute("""
            SELECT COUNT(*) FROM recipe
            WHERE array_length(image_hash_buckets, 1) > 0
        """)
        
        with_image_hash_count = cursor.fetchone()[0]
        logger.info(f"Recipes with non-empty image hash buckets: {with_image_hash_count}")
        
        # Check for missing feature vectors, with correct dimensions based on constants
        cursor.execute(f"""
            SELECT COUNT(*) FROM recipe
            WHERE 
                array_length(title_feature_vector, 1) <> {EMBEDDING_DIM_TITLE} OR
                array_length(ingredients_feature_vector, 1) <> {EMBEDDING_DIM_INGREDIENTS} OR
                array_length(instructions_feature_vector, 1) <> {EMBEDDING_DIM_INSTRUCTIONS} OR
                array_length(text_feature_vector, 1) <> {EMBEDDING_DIM_TEXT} OR
                array_length(image_feature_vector, 1) <> {EMBEDDING_DIM_IMAGE}
        """)
        
        invalid_vector_count = cursor.fetchone()[0]
        logger.info(f"Recipes with invalid feature vector dimensions: {invalid_vector_count}")
        
        # Detailed breakdown of invalid vector dimensions
        dimension_checks = [
            ("title_feature_vector", EMBEDDING_DIM_TITLE),
            ("ingredients_feature_vector", EMBEDDING_DIM_INGREDIENTS),
            ("instructions_feature_vector", EMBEDDING_DIM_INSTRUCTIONS),
            ("text_feature_vector", EMBEDDING_DIM_TEXT),
            ("image_feature_vector", EMBEDDING_DIM_IMAGE)
        ]
        
        for field, expected_dim in dimension_checks:
            cursor.execute(f"""
                SELECT COUNT(*) FROM recipe
                WHERE array_length({field}, 1) <> {expected_dim}
            """)
            invalid_count = cursor.fetchone()[0]
            if invalid_count > 0:
                logger.warning(f"Found {invalid_count} recipes with invalid {field} dimension (expected {expected_dim})")
        
        # Check count of recipes with image names that have corresponding image hash buckets
        cursor.execute("""
            SELECT COUNT(*) FROM recipe
            WHERE image_name IS NOT NULL AND array_length(image_hash_buckets, 1) > 0
        """)
        
        with_image_and_hash_count = cursor.fetchone()[0]
        logger.info(f"Recipes with both image name and image hash buckets: {with_image_and_hash_count}")
        
        # Close the connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_data() 