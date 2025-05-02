#!/usr/bin/env python3
"""
Database migrations management script.

This script provides two options:
1. For new installations: Recommends using the data/put_schemas_to_db.py script
2. For existing installations: Allows running individual migrations for backward compatibility
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root directory to the Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_schema_setup():
    """
    Run the comprehensive schema setup script.
    """
    logger.info("Running comprehensive schema setup script...")
    schema_script_path = os.path.join(root_dir, "data", "put_schemas_to_db.py")
    
    if not os.path.exists(schema_script_path):
        logger.error(f"Schema script not found at {schema_script_path}")
        return False
    
    try:
        # Change to project root directory
        os.chdir(root_dir)
        
        # Execute the schema script
        exit_code = os.system(f"python {schema_script_path} --force")
        
        if exit_code != 0:
            logger.error(f"Schema script failed with exit code {exit_code}")
            return False
            
        logger.info("Schema setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running schema setup: {e}")
        return False

def run_individual_migrations():
    """
    Run individual migrations for backward compatibility.
    """
    logger.info("Running individual migrations...")
    
    try:
        # Import and run migrations
        from database.migrations import migrate_recipes_for_multi_field_lsh, migrate_recipes_for_categories
        
        # Run the migrations
        logger.info("Running multi-field LSH migration...")
        migrate_recipes_for_multi_field_lsh()
        
        logger.info("Running categories migration...")
        migrate_recipes_for_categories()
        
        logger.info("Individual migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running individual migrations: {e}")
        return False

def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description="Database migration management")
    parser.add_argument(
        "--mode", 
        choices=["schema", "migrations", "all"], 
        default="schema",
        help="Migration mode: 'schema' for complete schema setup, 'migrations' for individual migrations, 'all' for both"
    )
    
    args = parser.parse_args()
    
    if args.mode in ["schema", "all"]:
        if not run_schema_setup():
            logger.error("Schema setup failed")
            sys.exit(1)
    
    if args.mode in ["migrations", "all"]:
        if not run_individual_migrations():
            logger.error("Individual migrations failed")
            sys.exit(1)
    
    logger.info(f"Database migration completed successfully (mode: {args.mode})")

if __name__ == "__main__":
    main() 