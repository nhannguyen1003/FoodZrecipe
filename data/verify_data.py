#!/usr/bin/env python3
"""
Script to verify the data loaded in the database.
"""
import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

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
        
        # Check sample recipes with their hash bucket counts
        cursor.execute("""
            SELECT 
                id, 
                title, 
                array_length(title_hash_buckets, 1) as title_hash_count,
                array_length(ingredients_hash_buckets, 1) as ingredients_hash_count,
                array_length(instructions_hash_buckets, 1) as instructions_hash_count,
                array_length(text_hash_buckets, 1) as text_hash_count
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
        
        # Check for missing hash buckets
        cursor.execute("""
            SELECT COUNT(*) FROM recipe
            WHERE 
                array_length(title_hash_buckets, 1) IS NULL OR
                array_length(ingredients_hash_buckets, 1) IS NULL OR
                array_length(instructions_hash_buckets, 1) IS NULL OR
                array_length(text_hash_buckets, 1) IS NULL
        """)
        
        missing_hash_count = cursor.fetchone()[0]
        logger.info(f"Recipes with missing hash buckets: {missing_hash_count}")
        
        # Check for missing feature vectors
        cursor.execute("""
            SELECT COUNT(*) FROM recipe
            WHERE 
                array_length(title_feature_vector, 1) <> 64 OR
                array_length(ingredients_feature_vector, 1) <> 128 OR
                array_length(instructions_feature_vector, 1) <> 256 OR
                array_length(text_feature_vector, 1) <> 128
        """)
        
        invalid_vector_count = cursor.fetchone()[0]
        logger.info(f"Recipes with invalid feature vector dimensions: {invalid_vector_count}")
        
        # Close the connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_data() 